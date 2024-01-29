import unittest
from unittest.mock import MagicMock
import sys
import fake_rpi
sys.modules['RPi'] = fake_rpi.RPi           # Fake RPi
sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO
from led.led import Led                     # noqa: E402

#*************************** Led tests ***************************#
class TestLed(unittest.TestCase):
    # Initialisation of test class
    @classmethod
    def setUpClass(cls):
        # Mock IPC client for testing
        cls.mock_ipc_client = MagicMock()

        # Instantiate the Led class with mocked parameters
        cls.led = Led(
            frequency=100,  # Provide initial values as needed
            ipc_client=cls.mock_ipc_client,
            lambda_frequency_topic="lambda_frequency",
            lambda_button_topic="lambda_button",
            device_frequency_topic="device_frequency",
            device_button_topic="device_button",
        )

        # Mock the Publish class
        cls.led.publish.publish_to_topic = MagicMock()
        # Mock the GPIO.PWM class
        cls.led.pwm.ChangeDutyCycle = MagicMock()


    # Frequency change test
    def test_frequency_change(self):
        # Simulate a frequency change message
        frequency_message = '{"frequency": 200}'
        self.led.callback_message(self.led.device_frequency_topic, frequency_message)

        # Assert that led.frequency variable has changed
        self.assertEqual(self.led.frequency, 200,'wrong frequency after change')


    # Frequency publish test
    def test_frequency_publish(self):
        # Simulate a frequency change message
        frequency_message = '{"frequency": 300}'
        self.led.callback_message(self.led.device_frequency_topic, frequency_message)

        # Assert that the publish.publish_to_topic method is called with the correct arguments
        self.led.publish.publish_to_topic.assert_called_with(self.led.lambda_frequency_topic, frequency_message)


    # Button status on test
    def test_on(self):
        # Simulate an on state message
        on_state_message = '{"state": true}'
        self.led.callback_message(self.led.device_button_topic, on_state_message)

        # Assert that led.state variable has changed to True
        self.assertTrue(self.led.state)


    # Button status off test
    def test_off(self):
        # Simulate an off state message
        off_state_message = '{"state": false}'
        self.led.callback_message(self.led.device_button_topic, off_state_message)

        # Assert that led.state variable has changed to False
        self.assertFalse(self.led.state)


    # State publish test
    def test_state_publish(self):
        # Simulate a state change message
        state_message = '{"state": true}'
        self.led.callback_message(self.led.device_button_topic, state_message)

        # Assert that the publish.publish_to_topic method is called with the correct arguments
        self.led.publish.publish_to_topic.assert_called_with(self.led.lambda_button_topic, state_message)

    
    # Duty cycle change test
    def test_duty_cycle_change(self):
        # Simulate a state change message
        state_message = '{"state": true}'
        self.led.callback_message(self.led.device_button_topic, state_message)

        # Assert that the pwm.ChangeDutyCycle method is called with the correct duty cycle
        self.led.pwm.ChangeDutyCycle.assert_called_once_with(50)


if __name__ == '__main__':
    unittest.main()