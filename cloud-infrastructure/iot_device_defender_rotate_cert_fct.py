import boto3
import json

client = boto3.client('iot')
data_client = boto3.client('iot-data')

def lambda_handler(event, context):
    global client
    global data_client

    thingName = event["ThingName"]

    # Create new certificate from CSR, signed by the Amazon Root certificate authority
    cert_response = client.create_certificate_from_csr(
        certificateSigningRequest = event["csr"],
        setAsActive=True
    )

    certResponse = {}
    certResponse["certificateArn"] = cert_response["certificateArn"]
    certResponse["certificateId"] = cert_response["certificateId"]
    certResponse["certificatePem"] = cert_response["certificatePem"]

    # Attach policy to certificate
    attachPolicyResponse = client.attach_policy(
        policyName='THING_POLICY_NAME',
        target=cert_response["certificateArn"]
    )

    # Attach thing/device to this certificate
    attachThingPolicyResponse = client.attach_thing_principal(
        thingName=thingName,
        principal=cert_response["certificateArn"]
    )

    # Send the new certificate back to the device
    data_client.publish(
        topic="device/"+ thingName +"/crt",
        qos=0,
        payload=json.dumps(certResponse)
    )

    return 'Done'
