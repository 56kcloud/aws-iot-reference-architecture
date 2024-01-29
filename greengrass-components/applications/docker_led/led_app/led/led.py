# Standard libraries
import json
from time import sleep  # Sleep function from the time module
# Libraries
import RPi.GPIO as GPIO # Raspberry Pi GPIO
from pubsub.pub import Publish

LED_GPIO = 12

#*************************** Led ***************************#
class Led:
    # Initialisation
    def __init__(self, frequency, ipc_client, lambda_frequency_topic, lambda_button_topic, device_frequency_topic, device_button_topic):
        self.frequency = frequency
        self.lambda_frequency_topic = lambda_frequency_topic
        self.lambda_button_topic = lambda_button_topic
        self.device_frequency_topic = device_frequency_topic
        self.device_button_topic = device_button_topic
        self.state = None

        # New instance
        self.publish = Publish(ipc_client)

        # Set GPIO
        GPIO.setwarnings(False)     # Ignore warning for now
        GPIO.setmode(GPIO.BOARD)    # Use physical pin numbering
        GPIO.setup(LED_GPIO, GPIO.OUT, initial=GPIO.LOW)   # Set pin 8 to be an output pin and set initial value to low (off)
        self.pwm = GPIO.PWM(LED_GPIO, self.frequency)


    # Callback message function
    def callback_message(self, topic, message):
        if topic == self.device_frequency_topic:
            self.frequency_change(message)
        if topic == self.device_button_topic:
            self.on_off(message)


    # Change of frequency
    def frequency_change(self, frequency):
        # Load the json to a string
        resp = json.loads(frequency)
        # Extract the frequency element in the response
        self.frequency = resp['frequency']
        
        # Change frequency
        self.pwm.ChangeFrequency(self.frequency)
        sleep(0.1)

        # Publish new frequency to dashboard
        self.publish.publish_to_topic(self.lambda_frequency_topic, frequency)


    # Enable or disable the blinking
    def on_off(self, state):
        # Load the json to a string
        resp = json.loads(state)
        # Extract the state element in the response
        self.state = resp['state']
        # Extract the state element in the response
        if self.state is True:
            self.pwm.ChangeDutyCycle(50)    # Enable blinking
        else:
            self.pwm.ChangeDutyCycle(0)     # Disable blinking

        # Publish button state to dashboard
        self.publish.publish_to_topic(self.lambda_button_topic, state)


    # LED application
    def app(self):
        self.pwm.start(50)

        # Keep the main thread alive, or the process will exit.
        while True:
            pass