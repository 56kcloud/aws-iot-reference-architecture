import boto3

client = boto3.client('iot')

def lambda_handler(event, context):
    global client
    
    # Get list of certificates for this thing
    certsResponse = client.list_thing_principals(
        thingName = event["ThingName"]
    )

    # Revoke and delete all certificates associated with this thing except for the new one
    for certARN in certsResponse["principals"]:
        if certARN != event["certificateArn"]:
            # Get certificate id from ARN
            base,certificateId = certARN.split("/")

            # Check its status
            statusResponse = client.describe_certificate(
                certificateId = certificateId
            )

            if statusResponse["certificateDescription"]["status"] != "REVOKED":
                # Revoke the certificate
                updateCertResponse = client.update_certificate(
                    certificateId = certificateId,
                    newStatus = 'REVOKED'
                )

                # List the policies for the certificate so they can be detached
                policiesResponse = client.list_attached_policies(
                    target=certARN,
                    recursive=False
                )

                # Remove the attachement
                for policy in policiesResponse["policies"]:
                    detachPrincipalPolicyResponse = client.detach_principal_policy(
                        policyName=policy["policyName"],
                        principal=certARN
                    )

                # Detach the certificate from the thing
                detachThingPrincipalResponse = client.detach_thing_principal(
                    thingName=event["ThingName"],
                    principal=certARN
                )

                # Delete the certificate
                deleteCertResponse = client.delete_certificate(
                    certificateId=certificateId,
                    forceDelete=False
                )

    return 'Done'
