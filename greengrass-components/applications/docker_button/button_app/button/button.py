# Standard libraries
import json
from time import sleep  # Sleep function from the time module
# Libraries
import RPi.GPIO as GPIO # Raspberry Pi GPIO
from pub.pub import Publish

BUTTON_GPIO = 36

#*************************** Button ***************************#
class Button:
    # Initialisation
    def __init__(self, ipc_client, device_button_topic):
        self.device_button_topic = device_button_topic
        self.on = True

        # New instance
        self.publish = Publish(ipc_client)

        # Set GPIO
        GPIO.setwarnings(False)     # Ignore warning for now
        GPIO.setmode(GPIO.BOARD)    # Use physical pin numbering
        GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)   # Set pin 36 to be an output pin and set initial value to low (off)


    # Callback function for interruption
    def interrupt_service_routine(self, BUTTON_GPIO):
        sleep(0.05) # Edge debounce of 50ms
        # Only deal with valid edges
        if GPIO.input(BUTTON_GPIO) == 0:
            self.on = not self.on
            # Publish to change the state of the led
            message = {
                "state": self.on
            }
            self.publish.publish_to_topic(self.device_button_topic, json.dumps(message))


    # Button application
    def app(self):
        # Define the event; bountime of 200ms means that subsequent edges will be ignored for 200ms
        GPIO.add_event_detect(BUTTON_GPIO, GPIO.FALLING, callback=self.interrupt_service_routine, bouncetime=200)

        # Keep the main thread alive, or the process will exit.
        while True:
            pass