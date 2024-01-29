# Standard libraries
import sys
import traceback
# Libraries
import awsiot.greengrasscoreipc.clientv2 as clientV2
from pubsub.sub import Subscribe
from led.led import Led

# Main
def main():
    args = sys.argv[1:]
    lambda_frequency_topic = args[0]
    lambda_frequency_topic = lambda_frequency_topic.replace('"', '')
    lambda_button_topic = args[1]
    lambda_button_topic = lambda_button_topic.replace('"', '')
    device_frequency_topic = args[2]
    device_frequency_topic = device_frequency_topic.replace('"', '')
    device_button_topic = args[3]
    device_button_topic = device_button_topic.replace('"', '')
    frequency = " ".join(args[4:])
    f = int(frequency.replace('"', ''))

    try:
        ipc_client = clientV2.GreengrassCoreIPCClientV2()

        # New instances
        ledApp = Led(f, ipc_client, lambda_frequency_topic, lambda_button_topic, device_frequency_topic, device_button_topic)
        subFreq = Subscribe(ipc_client, ledApp)

        # Subscribe to the topics
        subFreq.subscribe_to_topic(device_frequency_topic)
        subFreq.subscribe_to_topic_local(device_button_topic)

        # Start led application
        ledApp.app()

    except Exception:
        print("Exception occurred", file=sys.stderr)
        traceback.print_exc()


if __name__ == "__main__":
    main()