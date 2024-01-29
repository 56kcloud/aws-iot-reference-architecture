import unittest
from unittest.mock import MagicMock
from awsiot.greengrasscoreipc.model import BinaryMessage, PublishMessage
from pub.pub import Publish

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

        # Assert that the ipc_client.publish_to_topic method is called with the correct arguments
        self.publish.ipc_client.publish_to_topic.assert_called_once_with(
            topic="topic",
            publish_message=PublishMessage(binary_message=BinaryMessage(message=b"world"))
        )


if __name__ == '__main__':
    unittest.main()