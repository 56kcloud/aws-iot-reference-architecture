import pulumi
from pulumi_aws_native import iam
import os

TES_ROLE_NAME=os.getenv('TES_ROLE_NAME')
TES_POLICY_NAME=os.getenv('TES_POLICY_NAME')
HOOK_ROLE_NAME=os.getenv('HOOK_ROLE_NAME')
HOOK_POLICY_NAME=os.getenv('HOOK_POLICY_NAME')
CERT_BUCKET_NAME=os.getenv('CERT_BUCKET_NAME')
FLEET_ROLE_NAME=os.getenv('FLEET_ROLE_NAME')
AUDIT_ACTION_ROLE_NAME=os.getenv('AUDIT_ACTION_ROLE_NAME')
AUDIT_ACTION_POLICY_NAME=os.getenv('AUDIT_ACTION_POLICY_NAME')
AUDIT_ROLE_NAME=os.getenv('AUDIT_ROLE_NAME')
AUDIT_POLICY_NAME=os.getenv('AUDIT_POLICY_NAME')
ROTATE_CERT_ROLE_NAME=os.getenv('ROTATE_CERT_ROLE_NAME')
ROTATE_CERT_POLICY_NAME=os.getenv('ROTATE_CERT_POLICY_NAME')
REVOKE_CERT_ROLE_NAME=os.getenv('REVOKE_CERT_ROLE_NAME')
REVOKE_CERT_POLICY_NAME=os.getenv('REVOKE_CERT_POLICY_NAME')
SNS_TOPIC_NAME=os.getenv('SNS_TOPIC_NAME')

aws_config = pulumi.Config("iot-ref-arch")
aws_account_id = aws_config.require("aws-account-id")
aws_region = aws_config.require("aws-region")

# Create an IAM role that the device can use as a token exchange role
tes_role = iam.Role("TesRoleID",
    role_name=TES_ROLE_NAME,
    description="Greengrass core devices use an IAM service role, called the token exchange role, to authorize calls to AWS services.",
    assume_role_policy_document="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "credentials.iot.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }"""
)

# Create the IAM policy and attach to token exchange role
tes_policy = iam.RolePolicy("TesPolicyID",
    policy_name=TES_POLICY_NAME,
    role_name=TES_ROLE_NAME,
    policy_document={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams",
                    "s3:GetBucketLocation",
                    "s3:GetObject",
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "cloudwatch:PutMetricData"
                ],
                "Resource": "*"
            }
        ]
    },
    opts=pulumi.ResourceOptions(depends_on=tes_role)
)

# Create an IAM role that allow the Lambda pre-provisioning function to read from the S3 bucket to check the allowlist
pre_provisioning_hook_role = iam.Role("PreProvisioningHookRoleID",
    role_name=HOOK_ROLE_NAME,
    description="Allow the Lambda pre-provisioning function to read from the S3 bucket to check the allowlist",
    assume_role_policy_document="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }"""
)

# Create the IAM policy and attach to pre-provisioning hook role
pre_provisioning_hook_policy = iam.RolePolicy("PreProvisioningHookPolicyID",
    policy_name=HOOK_POLICY_NAME,
    role_name=pre_provisioning_hook_role.role_name,
    policy_document={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject"
                ],
                "Resource": "arn:aws:s3:::" + CERT_BUCKET_NAME + "/*"
            }
        ]
    },
    opts=pulumi.ResourceOptions(depends_on=pre_provisioning_hook_role)
)

# Create an IAM role that AWS IoT can assume to provision resources in the AWS account and attach the AWSIoTThingsRegistration IAM policy
fleet_role = iam.Role("FleetRoleID",
    role_name=FLEET_ROLE_NAME,
    description="Allows access to all permissions that AWS IoT might use when provisioning devices",
    managed_policy_arns=["arn:aws:iam::aws:policy/service-role/AWSIoTThingsRegistration"],
    assume_role_policy_document="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "iot.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }"""
)

# Create an IAM role that allows to get description of expiring certificates, get things attached to these certificates and send a CSR request to these things via MQTT
audit_actions_role = iam.Role("IoTDeviceDefenderAuditActionsRoleID",
    role_name=AUDIT_ACTION_ROLE_NAME,
    description="Allow to get description of expiring certificates, get things attached to these certificates and send a CSR request to these things via MQTT",
    assume_role_policy_document="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }"""
)

# Create the IAM policy and attach to IoT device defender audit actions role
audit_actions_policy = iam.RolePolicy("IoTDeviceDefenderAuditActionsPolicyID",
    policy_name=AUDIT_ACTION_POLICY_NAME,
    role_name=audit_actions_role.role_name,
    policy_document={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "iot:Publish",
                "Resource": "arn:aws:iot:" + aws_region + ":" + aws_account_id + ":topic/device/*/csr_req"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iot:ListAuditFindings",
                    "iot:ListPrincipalThings"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": "iot:DescribeCertificate",
                "Resource": "arn:aws:iot:" + aws_region + ":" + aws_account_id + ":cert/*"
            }
        ]
    },
    opts=pulumi.ResourceOptions(depends_on=audit_actions_role)
)

# Create an IAM role that allows access to iot certificates and the publication of notifications on Amazon SNS
audit_role = iam.Role("IoTDeviceDefenderAuditRoleID",
    role_name=AUDIT_ROLE_NAME,
    description="Allow access to iot certificates and the publication of notifications on Amazon SNS",
    assume_role_policy_document="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "iot.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }"""
)

# Create the IAM policy and attach to IoT device defender audit role
audit_policy = iam.RolePolicy("IoTDeviceDefenderAuditPolicyID",
    policy_name=AUDIT_POLICY_NAME,
    role_name=audit_role.role_name,
    policy_document={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "iot:ListCertificates",
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": "iot:DescribeCertificate",
                "Resource": "arn:aws:iot:" + aws_region + ":" + aws_account_id + ":cert/*"
            },
            {
                "Effect": "Allow",
                "Action": "sns:Publish",
                "Resource": "arn:aws:sns:" + aws_region + ":" + aws_account_id + ":" + SNS_TOPIC_NAME
            }
        ]
    },
    opts=pulumi.ResourceOptions(depends_on=audit_role)
)

# Create an IAM role that allows access to the creation of a new certificate with IoT Core and publish it in a topic via MQTT
rotate_cert_role = iam.Role("IoTDeviceDefenderRotateCertRoleID",
    role_name=ROTATE_CERT_ROLE_NAME,
    description="Allow access to the creation of a new certificate with IoT Core and publish it in a topic via MQTT",
    assume_role_policy_document="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }"""
)

# Create the IAM policy and attach to IoT device defender rotate cert role
rotate_cert_policy = iam.RolePolicy("IoTDeviceDefenderRotateCertPolicyID",
    policy_name=ROTATE_CERT_POLICY_NAME,
    role_name=rotate_cert_role.role_name,
    policy_document={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "iot:Publish",
                "Resource": "arn:aws:iot:" + aws_region + ":" + aws_account_id + ":topic/device/*/crt"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iot:CreateCertificateFromCsr",
                    "iot:AttachThingPrincipal"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": "iot:AttachPolicy",
                "Resource": "arn:aws:iot:" + aws_region + ":" + aws_account_id + ":cert/*"
            }
        ]
    },
    opts=pulumi.ResourceOptions(depends_on=rotate_cert_role)
)

# Create an IAM role that allows access to certificates for revocation and deletion
revoke_cert_role = iam.Role("IoTDeviceDefenderRevokeCertRoleID",
    role_name=REVOKE_CERT_ROLE_NAME,
    description="Allow access to certificates for revocation and deletion",
    assume_role_policy_document="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }"""
)

# Create the IAM policy and attach to IoT device defender revoke cert role
revoke_cert_policy = iam.RolePolicy("IoTDeviceDefenderRevokeCertPolicyID",
    policy_name=REVOKE_CERT_POLICY_NAME,
    role_name=revoke_cert_role.role_name,
    policy_document={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iot:ListThingPrincipals",
                    "iot:ListAttachedPolicies",
                    "iot:DetachThingPrincipal"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iot:DescribeCertificate",
                    "iot:UpdateCertificate",
                    "iot:DetachPrincipalPolicy",
                    "iot:DeleteCertificate"
                ],
                "Resource": "arn:aws:iot:" + aws_region + ":" + aws_account_id + ":cert/*"
            }
        ]
    },
    opts=pulumi.ResourceOptions(depends_on=revoke_cert_role)
)