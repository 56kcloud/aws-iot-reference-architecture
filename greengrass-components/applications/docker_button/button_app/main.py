# Standard libraries
import sys
import traceback
# Libraries
import awsiot.greengrasscoreipc.clientv2 as clientV2
from button.button import Button

# Main
def main():
    args = sys.argv[1:]
    device_button_topic = args[0]
    device_button_topic = device_button_topic.replace('"', '')

    try:
        ipc_client = clientV2.GreengrassCoreIPCClientV2()

        # New instances
        buttonApp = Button(ipc_client, device_button_topic)

        # Start led application
        buttonApp.app()

    except Exception:
        print("Exception occurred", file=sys.stderr)
        traceback.print_exc()


if __name__ == "__main__":
    main()