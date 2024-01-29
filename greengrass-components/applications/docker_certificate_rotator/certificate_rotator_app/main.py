# Standard libraries
import sys
import traceback
# Libraries
import awsiot.greengrasscoreipc.clientv2 as clientV2
from pubsub.sub import Subscribe
from certificate_rotator.certificate_rotator import CertificateRotator

# Main
def main():
    args = sys.argv[1:]
    lambda_csr_res_topic = args[0]
    lambda_csr_res_topic = lambda_csr_res_topic.replace('"', '')
    lambda_crt_ack_topic = args[1]
    lambda_crt_ack_topic = lambda_crt_ack_topic.replace('"', '')
    device_csr_req_topic = args[2]
    device_csr_req_topic = device_csr_req_topic.replace('"', '')
    device_crt_topic = args[3]
    device_crt_topic = device_crt_topic.replace('"', '')
    serial_number = args[4]
    serial_number = serial_number.replace('"', '')

    try:
        ipc_client = clientV2.GreengrassCoreIPCClientV2()

        # New instances
        certRotatorApp = CertificateRotator(ipc_client, serial_number, lambda_csr_res_topic, lambda_crt_ack_topic, device_csr_req_topic, device_crt_topic)
        subFreq = Subscribe(ipc_client, certRotatorApp)

        # Subscribe to the topics
        subFreq.subscribe_to_topic(device_csr_req_topic)
        subFreq.subscribe_to_topic(device_crt_topic)

        # Start certificate rotator application
        certRotatorApp.app()

    except Exception:
        print("Exception occurred", file=sys.stderr)
        traceback.print_exc()


if __name__ == "__main__":
    main()