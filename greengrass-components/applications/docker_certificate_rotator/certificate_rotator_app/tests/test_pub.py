import unittest
from unittest.mock import MagicMock
from pubsub.pub import Publish

#*************************** Publish tests ***************************#
class TestPublish(unittest.TestCase):
    # Initialisation of test class
    @classmethod
    def setUpClass(cls):
        # Mock IPC client for testing
        cls.mock_ipc_client = MagicMock()

        # Instantiate the Publish class with mocked parameters
        cls.publish = Publish(
            ipc_client=cls.mock_ipc_client
        )


    # Test publish function
    def test_publish_to_topic(self):
        # Simulate publication
        self.publish.publish_to_topic("topic", "world")

        # Assert that the ipc_client.publish_to_iot_core method is called with the correct arguments
        self.publish.ipc_client.publish_to_iot_core.assert_called_once_with(
            topic_name="topic",
            qos="1",
            payload="world"
        )


if __name__ == '__main__':
    unittest.main()