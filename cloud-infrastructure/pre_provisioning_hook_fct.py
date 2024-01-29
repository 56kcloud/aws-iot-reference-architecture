import json
import boto3
import re

s3_client = boto3.client("s3")

def isAllowlisted(serial_number, allowlist):
    serial_number_regex = r'\b' + re.escape(serial_number) + r'\b'

    # Check serial number in allowlist
    if re.search(serial_number_regex, allowlist):
        return True
        
    return False
    
def lambda_handler(event, context):
    global s3_client

    provisionResponse = {'allowProvisioning': False}

    # Display all attributes sent from device
    print("Received event: " + json.dumps(event, indent=2))

    # Assume device has sent a serial number
    device_serial = event["parameters"]["SerialNumber"]

    try:
        # Read allowlist file from S3
        allowlistContent = s3_client.get_object(
            Bucket="S3_BUCKET_NAME", Key="allowlist.txt")["Body"].read().decode('utf-8')

        # Allow provisioning if device is authorised
        if isAllowlisted(device_serial, allowlistContent):
            provisionResponse["allowProvisioning"] = True

    except Exception as e:
        print(f"Error reading from S3: {e}")
        
    return provisionResponse