"""Configuring infrastructure for fleet provisioning on AWS"""
import pulumi
import pulumi_aws as aws
import pulumi_aws_native as aws_native
import os
import json
import iam

THING_GROUP_NAME=os.getenv('THING_GROUP_NAME')
CERT_BUCKET_NAME=os.getenv('CERT_BUCKET_NAME')
IMAGE_BUCKET_NAME=os.getenv('IMAGE_BUCKET_NAME')
TES_ROLE_ALIAS_NAME=os.getenv('TES_ROLE_ALIAS_NAME')
THING_POLICY_NAME=os.getenv('THING_POLICY_NAME')
HOOK_FCT_NAME=os.getenv('HOOK_FCT_NAME')
FLEET_TEMPLATE_NAME=os.getenv('FLEET_TEMPLATE_NAME')
CLAIM_POLICY_NAME=os.getenv('CLAIM_POLICY_NAME')
CLAIM_CERTIFICATE_ARN=os.getenv('CLAIM_CERTIFICATE_ARN')
AUDIT_ACTION_FCT_NAME=os.getenv('AUDIT_ACTION_FCT_NAME')
ROTATE_CERT_FCT_NAME=os.getenv('ROTATE_CERT_FCT_NAME')
CSR_TRIGGER_RULE_NAME=os.getenv('CSR_TRIGGER_RULE_NAME')
REVOKE_CERT_FCT_NAME=os.getenv('REVOKE_CERT_FCT_NAME')
CRT_ACK_TRIGGER_RULE_NAME=os.getenv('CRT_ACK_TRIGGER_RULE_NAME')
SNS_TOPIC_NAME=os.getenv('SNS_TOPIC_NAME')

aws_config = pulumi.Config("iot-ref-arch")
aws_account_id = aws_config.require("aws-account-id")
aws_region = aws_config.require("aws-region")

###########################################################
# Create an AWS IoT thing group
###########################################################
thing_group = aws_native.iot.ThingGroup("ThingGroupID",
    thing_group_name=THING_GROUP_NAME
)

###########################################################
# Create a token exchange role
###########################################################
# Greengrass core devices use an IAM service role, called the token exchange role, to authorize calls to AWS services. The device uses the AWS IoT credentials provider to get temporary AWS credentials for this role, which allows the device to interact with AWS IoT, send logs to Amazon CloudWatch Logs, and download custom component artifacts from Amazon S3.

# Create an AWS IoT role alias that points to the token exchange role
tes_role_alias = aws_native.iot.RoleAlias("TesRoleAliasID",
    role_alias=TES_ROLE_ALIAS_NAME,
    role_arn=iam.tes_role.arn,
    credential_duration_seconds=3600,
    opts=pulumi.ResourceOptions(depends_on=iam.tes_role)
)

###########################################################
# Create an AWS IoT policy
###########################################################
# Create an AWS IoT policy that defines the AWS IoT permissions for the fleet of Greengrass core devices. The following policy allows access to all MQTT topics and Greengrass operations, so the device works with custom applications and future changes that require new Greengrass operations. This policy also allows the iot:AssumeRoleWithCertificate permission, which allows your devices to use the token exchange role.
thing_policy = aws_native.iot.Policy("ThingPolicyID",
    policy_name=THING_POLICY_NAME,
    policy_document={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iot:Publish",
                    "iot:Subscribe",
                    "iot:Receive",
                    "iot:Connect",
                    "greengrass:*"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": "iot:AssumeRoleWithCertificate",
                "Resource": tes_role_alias.role_alias_arn
            }
        ]
    }
)

###########################################################
# Create pre-provisioning
###########################################################
# Create the Lambda pre-provisioning function that checks the allowlist
with open('pre_provisioning_hook_fct.py', 'r') as f:
    strPreProvisioningHookFunction = f.read()

strPreProvisioningHookFunction = strPreProvisioningHookFunction.replace("S3_BUCKET_NAME", CERT_BUCKET_NAME)

pre_provisioning_hook_function = aws_native.lambda_.Function("PreProvisioningHookFunctionID",
    function_name=HOOK_FCT_NAME,
    description="Lambda pre-provisioning function that checks the allowlist",
    role=iam.pre_provisioning_hook_role.arn,
    code=aws_native.lambda_.FunctionCodeArgs(zip_file=strPreProvisioningHookFunction),
    runtime="python3.12",
    handler="index.lambda_handler",
    architectures=["arm64"],
    opts=pulumi.ResourceOptions(depends_on=iam.pre_provisioning_hook_role)
)

# Allow a trigger from AWS IoT Core when a new device needs to be provisioned
pre_provisioning_hook_function_permission = aws_native.lambda_.Permission("PreProvisioningHookFunctionPermissionID",
    action="lambda:InvokeFunction",
    function_name=pre_provisioning_hook_function.function_name,
    principal="iot.amazonaws.com",
    source_account=aws_account_id,
    source_arn=f"arn:aws:iot:{aws_region}:{aws_account_id}:*",
    opts=pulumi.ResourceOptions(depends_on=pre_provisioning_hook_function)
)

###########################################################
# Create a fleet provisioning template
###########################################################
# AWS IoT fleet provisioning templates define how to provision AWS IoT things, policies, and certificates.

# Create the fleet provisioning template from the provisioning template document
dictFleetTemplate = {
    "Parameters": {
        "SerialNumber": {
            "Type": "String"
        },
        "AWS::IoT::Certificate::Id": {
            "Type": "String"
        }
    },
    "Resources": {
        "Thing": {
            "OverrideSettings": {
                "AttributePayload": "REPLACE",
                "ThingGroups": "REPLACE",
                "ThingTypeName": "REPLACE"
            },
            "Properties": {
                "AttributePayload": {},
                "ThingGroups": [
                    THING_GROUP_NAME
                ],
                "ThingName": {
                    "Ref": "SerialNumber"
                }
            },
            "Type": "AWS::IoT::Thing"
        },
        "Policy": {
            "Properties": {
                "PolicyName": THING_POLICY_NAME
            },
            "Type": "AWS::IoT::Policy"
        },
        "Certificate": {
            "Properties": {
                "CertificateId": {
                    "Ref": "AWS::IoT::Certificate::Id"
                },
                "Status": "Active"
            },
            "Type": "AWS::IoT::Certificate"
        }
    }
}

strFleetTemplate = json.dumps(dictFleetTemplate)

fleet_template = aws_native.iot.ProvisioningTemplate("FleetTemplateID",
    template_name=FLEET_TEMPLATE_NAME,
    description="A provisioning template for Greengrass core devices.",
    provisioning_role_arn=iam.fleet_role.arn,
    template_type="FLEET_PROVISIONING",
    template_body=f"""{strFleetTemplate}""",
    pre_provisioning_hook=aws_native.iot.ProvisioningTemplateProvisioningHookArgs(
        payload_version="2020-04-01",
        target_arn=pre_provisioning_hook_function.arn),
    enabled=True,
    opts=pulumi.ResourceOptions(depends_on=[iam.fleet_role, pre_provisioning_hook_function])
)

###########################################################
# Attach the claim certificate to AWS IoT policy
###########################################################
# Claim certificates are X.509 certificates that allow devices to register as AWS IoT things and retrieve a unique X.509 device certificate to use for regular operations.

# Create and attach an AWS IoT policy that allows devices to use the certificate to create unique device certificates and provision with the fleet provisioning template
claim_policy = aws_native.iot.Policy("ClaimPolicyID",
    policy_name=CLAIM_POLICY_NAME,
    policy_document={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "iot:Connect",
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iot:Publish",
                    "iot:Receive"
                ],
                "Resource": [
                    "arn:aws:iot:" + aws_region + ":" + aws_account_id + ":topic/$aws/certificates/create/*",
                    "arn:aws:iot:" + aws_region + ":" + aws_account_id + ":topic/$aws/provisioning-templates/" + FLEET_TEMPLATE_NAME + "/provision/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": "iot:Subscribe",
                "Resource": [
                    "arn:aws:iot:" + aws_region + ":" + aws_account_id + ":topicfilter/$aws/certificates/create/*",
                    "arn:aws:iot:" + aws_region + ":" + aws_account_id + ":topicfilter/$aws/provisioning-templates/" + FLEET_TEMPLATE_NAME + "/provision/*"
                ]
            }
        ]
    }
)

# Attach the AWS IoT policy to the provisioning claim certificate
iot_policy_attachment = aws.iot.PolicyAttachment('IotPolicyAttachmentID',
    policy=CLAIM_POLICY_NAME,
    target=CLAIM_CERTIFICATE_ARN,
    opts=pulumi.ResourceOptions(depends_on=claim_policy)
)

###########################################################
# Secure IoT fleet with Device Defender Audit
###########################################################
# Create Lambda function that is triggered from Device Defender Audit when a device certificate is expiring. This function get description of certificates expiring and get things attached to this. It sends a CSR request to these things via MQTT.
with open('iot_device_defender_audit_actions_fct.py', 'r') as f:
    strAuditActionsFunction = f.read()

audit_actions_function = aws_native.lambda_.Function("IoTDeviceDefenderAuditActionsFunctionID",
    function_name=AUDIT_ACTION_FCT_NAME,
    description="Get description of expiring certificates, get things attached to these certificates and send a CSR request to these things via MQTT",
    role=iam.audit_actions_role.arn,
    code=aws_native.lambda_.FunctionCodeArgs(zip_file=strAuditActionsFunction),
    runtime="python3.12",
    handler="index.lambda_handler",
    architectures=["arm64"],
    opts=pulumi.ResourceOptions(depends_on=iam.audit_actions_role)
)

# Allow triggering of the Lambda audit actions function from Amazon SNS when an expiring certificate is detected in the audit
audit_actions_function_permission = aws_native.lambda_.Permission("IoTDeviceDefenderAuditActionsFunctionPermissionID",
    action="lambda:InvokeFunction",
    function_name=audit_actions_function.function_name,
    principal="sns.amazonaws.com",
    source_arn=f"arn:aws:sns:{aws_region}:{aws_account_id}:{SNS_TOPIC_NAME}",
    opts=pulumi.ResourceOptions(depends_on=audit_actions_function)
)

# Create SNS topic attached to IoT security audit to trigger Lambda audit actions function
device_certificate_expiring_topic = aws_native.sns.Topic("DeviceCertificateExpiringTopicID",
    topic_name=SNS_TOPIC_NAME,
    subscription=[aws_native.sns.TopicSubscriptionArgs(
        endpoint=audit_actions_function.arn,
        protocol="lambda"
    )],
    opts=pulumi.ResourceOptions(depends_on=audit_actions_function)
)

# Create an IoT security audit that checks the expiration of the device certificate and sends notifications to Amazon SNS
device_defender_audit = aws_native.iot.AccountAuditConfiguration("IoTDeviceDefenderAuditID",
    account_id=aws_account_id,
    role_arn=iam.audit_role.arn,
    audit_check_configurations={
        "deviceCertificateExpiringCheck": aws_native.iot.AccountAuditConfigurationAuditCheckConfigurationArgs(
            enabled=True,
        )
    },
    audit_notification_target_configurations={
        "sns": aws_native.iot.AccountAuditConfigurationAuditNotificationTargetArgs(
            target_arn=device_certificate_expiring_topic.topic_arn,
            role_arn=iam.audit_role.arn,
            enabled=True,
        )
    },
    opts=pulumi.ResourceOptions(depends_on=iam.audit_role)
)

# Create a scheduled audit with a daily control audit frequency
scheduled_audit = aws_native.iot.ScheduledAudit("ScheduledAuditID",
    scheduled_audit_name="IoTDeviceDefenderDailyAudit",
    frequency="DAILY",
    target_check_names=["DEVICE_CERTIFICATE_EXPIRING_CHECK"],
    opts=pulumi.ResourceOptions(depends_on=device_defender_audit)
)

# Create Lambda function that creates a new certificate from CSR and sends it to the device
with open('iot_device_defender_rotate_cert_fct.py', 'r') as f:
    strRotateCertFunction = f.read()

strRotateCertFunction = strRotateCertFunction.replace("THING_POLICY_NAME", THING_POLICY_NAME)

rotate_cert_function = aws_native.lambda_.Function("IoTDeviceDefenderRotateCertFunctionID",
    function_name=ROTATE_CERT_FCT_NAME,
    description="Get the CSR from the device whose certificate expires, create a new certificate from the CSR, publish the new certificate on the device",
    role=iam.rotate_cert_role.arn,
    code=aws_native.lambda_.FunctionCodeArgs(zip_file=strRotateCertFunction),
    runtime="python3.12",
    handler="index.lambda_handler",
    architectures=["arm64"],
    opts=pulumi.ResourceOptions(depends_on=iam.rotate_cert_role)
)

# Allow triggering of the Lambda rotation certificate function when a CSR is sent by the device
rotate_cert_function_permission = aws_native.lambda_.Permission("IoTDeviceDefenderRotateCertFunctionPermissionID",
    action="lambda:InvokeFunction",
    function_name=rotate_cert_function.function_name,
    principal="iot.amazonaws.com",
    source_arn=f"arn:aws:iot:{aws_region}:{aws_account_id}:rule/{CSR_TRIGGER_RULE_NAME}",
    opts=pulumi.ResourceOptions(depends_on=rotate_cert_function)
)

# Create an IoT topic rule in message routing for CSR requests from the IoT device
csr_trigger_iot_topic_rule = aws_native.iot.TopicRule("CsrTriggerIoTTopicRuleID",
    rule_name=CSR_TRIGGER_RULE_NAME,
    topic_rule_payload=aws_native.iot.TopicRulePayloadArgs(
        sql="SELECT * FROM 'lambda/+/csr_res'",
        actions=[
            aws_native.iot.TopicRuleActionArgs(
                lambda_=aws_native.iot.TopicRuleLambdaActionArgs(
                    function_arn=rotate_cert_function.arn
                )
            )
        ],
        description="Triggered when the CSR is sent by iot device",
        aws_iot_sql_version="2016-03-23"
    ),
    opts=pulumi.ResourceOptions(depends_on=rotate_cert_function)
)

# Create a Lambda function that revokes and deletes the device's expiring certificate
with open('iot_device_defender_revoke_cert_fct.py', 'r') as f:
    strRevokeCertFunction = f.read()

revoke_cert_function = aws_native.lambda_.Function("IoTDeviceDefenderRevokeCertFunctionID",
    function_name=REVOKE_CERT_FCT_NAME,
    description="Revoke and delete certificate associated with the thing except for the new one",
    role=iam.revoke_cert_role.arn,
    code=aws_native.lambda_.FunctionCodeArgs(zip_file=strRevokeCertFunction),
    runtime="python3.12",
    handler="index.lambda_handler",
    architectures=["arm64"],
    opts=pulumi.ResourceOptions(depends_on=iam.revoke_cert_role)
)

# Allow triggering of the Lambda revoke certificate function when a certificate acknowledgement is sent by the device
revoke_cert_function_permission = aws_native.lambda_.Permission("IoTDeviceDefenderRevokeCertFunctionPermissionID",
    action="lambda:InvokeFunction",
    function_name=revoke_cert_function.function_name,
    principal="iot.amazonaws.com",
    source_arn=f"arn:aws:iot:{aws_region}:{aws_account_id}:rule/{CRT_ACK_TRIGGER_RULE_NAME}",
    opts=pulumi.ResourceOptions(depends_on=revoke_cert_function)
)

# Create an IoT topic rule in message routing for certificate acknowledgement from the IoT device
csr_trigger_iot_topic_rule = aws_native.iot.TopicRule("CrtAckTriggerIoTTopicRuleID",
    rule_name=CRT_ACK_TRIGGER_RULE_NAME,
    topic_rule_payload=aws_native.iot.TopicRulePayloadArgs(
        sql="SELECT * FROM 'lambda/+/crt_ack'",
        actions=[
            aws_native.iot.TopicRuleActionArgs(
                lambda_=aws_native.iot.TopicRuleLambdaActionArgs(
                    function_arn=revoke_cert_function.arn
                )
            )
        ],
        description="Triggered when the certificate acknowledgement is sent by iot device",
        aws_iot_sql_version="2016-03-23"
    ),
    opts=pulumi.ResourceOptions(depends_on=revoke_cert_function)
)

###########################################################
# Create storage for custom OS image
###########################################################
# Create S3 bucket to store the custom OS image
os_bucket = aws_native.s3.Bucket("OSBucketID",
    bucket_name=IMAGE_BUCKET_NAME,
    access_control="Private"
)