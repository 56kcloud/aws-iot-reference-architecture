import unittest
from unittest.mock import MagicMock, patch
import sys
import fake_rpi
sys.modules['RPi'] = fake_rpi.RPi           # Fake RPi
sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO
from button.button import Button            # noqa: E402

BUTTON_GPIO = 36

#*************************** Button tests ***************************#
class TestButton(unittest.TestCase):
    # Initialisation of test class
    @classmethod
    def setUpClass(cls):
        # Mock IPC client for testing
        cls.mock_ipc_client = MagicMock()

        # Instantiate the Button class with mocked parameters
        cls.button = Button(
            ipc_client=cls.mock_ipc_client,
            device_button_topic="device_button"
        )

        # Mock the Publish class
        cls.button.publish.publish_to_topic = MagicMock()


    # Test switch from ON to OFF
    @patch('RPi.GPIO.input')
    def test_button_off(self, mock_gpio_input):
        # Simulate button press
        mock_gpio_input.return_value = 0
        self.button.interrupt_service_routine(BUTTON_GPIO)
        # Assert that button.on variable has changed
        self.assertFalse(self.button.on)


    # Test switch from OFF to ON
    @patch('RPi.GPIO.input')
    def test_button_on(self, mock_gpio_input):
        # Simulate button press
        mock_gpio_input.return_value = 0
        self.button.interrupt_service_routine(BUTTON_GPIO)
        # Assert that button.on variable has changed
        self.assertTrue(self.button.on)


    # Test of publish when button pressed
    @patch('RPi.GPIO.input')
    def test_button_publish(self, mock_gpio_input):
        # Simulate button press
        mock_gpio_input.return_value = 0
        self.button.interrupt_service_routine(BUTTON_GPIO)
        # Check if publish was called with the correct arguments
        expected_message = '{"state": false}'
        # Assert that the publish.publish_to_topic method is called with the correct arguments
        self.button.publish.publish_to_topic.assert_called_with(
            self.button.device_button_topic,
            expected_message
        )


if __name__ == '__main__':
    unittest.main()