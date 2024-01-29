import boto3
import json

client = boto3.client('iot')
data_client = boto3.client('iot-data')

def lambda_handler(event, context):
    global client
    global data_client

    message = json.loads(event["Records"][0]["Sns"]["Message"])

    # Filter for actionable check violations
    for audit in message["auditDetails"]:
        if audit["checkName"] == "DEVICE_CERTIFICATE_EXPIRING_CHECK":
            # Initialize the list with all impacted things
            auditResults = client.list_audit_findings(
                taskId=message["taskId"],
                checkName=audit["checkName"]
            )

            for finding in auditResults["findings"]:
                expiringCertId = finding["nonCompliantResource"]["resourceIdentifier"]["deviceCertificateId"]
                
                myExpiringCert = client.describe_certificate(
                    certificateId=expiringCertId
                )
                
                expiringCertArn = myExpiringCert["certificateDescription"]["certificateArn"]

                # Get things for this certificate
                thingsResp = client.list_principal_things(
                    maxResults=100,
                    principal=expiringCertArn
                )

                # Send a CSR request to all the elements attached to the certificate, which will expire
                for thing in thingsResp["things"]:
                    # Publish CSR request message to topic
                    data_client.publish(
                        topic="device/"+ thing +"/csr_req",
                        qos=1,
                        payload="{}"
                    )

    return 'Done'
