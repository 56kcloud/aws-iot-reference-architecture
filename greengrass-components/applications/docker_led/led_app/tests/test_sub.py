import unittest
from unittest.mock import MagicMock
from pubsub.sub import Subscribe

#*************************** Subscribe tests ***************************#
class TestSubscribe(unittest.TestCase):
    # Initialisation of test class
    @classmethod
    def setUpClass(cls):
        # Mock IPC client for testing
        cls.mock_ipc_client = MagicMock()
        # Mock the Led class for testing
        cls.mock_ledApp = MagicMock()
        # Mock event object
        cls.mock_event = MagicMock()
        # Mock error object
        cls.mock_error = MagicMock()

        # Instantiate the Subscribe class with mocked parameters
        cls.subscribe = Subscribe(
            ipc_client=cls.mock_ipc_client,
            ledApp=cls.mock_ledApp
        )


    # Initialisation of test methods
    def setUp(self):
        # Reset mocks
        self.subscribe.ledApp.callback_message.reset_mock()


    # Test subscribe function
    def test_subscribe_to_topic(self):
        # Simulate publication
        self.subscribe.subscribe_to_topic("topic")

        # Assert that the ipc_client.subscribe_to_iot_core method is called with the correct arguments
        self.subscribe.ipc_client.subscribe_to_iot_core.assert_called_once_with(
            topic_name="topic",
            qos="1",
            on_stream_event=self.subscribe._on_stream_event,
            on_stream_error=self.subscribe._on_stream_error,
            on_stream_closed=self.subscribe._on_stream_closed
        )


    # Test local subscribe function
    def test_subscribe_to_topic_local(self):
        # Simulate publication
        self.subscribe.subscribe_to_topic_local("topic")

        # Assert that the ipc_client.subscribe_to_iot_core method is called with the correct arguments
        self.subscribe.ipc_client.subscribe_to_topic.assert_called_once_with(
            topic="topic",
            on_stream_event=self.subscribe._on_stream_event_local,
            on_stream_error=self.subscribe._on_stream_error_local,
            on_stream_closed=self.subscribe._on_stream_closed_local
        )


    # Test message received function
    def test_on_stream_event(self):
        # Simulate event
        self.mock_event.message.topic_name = 'topic'
        self.mock_event.message.payload = b'world'
        self.subscribe._on_stream_event(self.mock_event)

        # Assert that the ledApp.callback_message method is called with the correct arguments
        self.subscribe.ledApp.callback_message.assert_called_once_with(
            "topic",
            "world"
        )


    # Test local message received function
    def test_on_stream_event_local(self):
        # Simulate event
        self.mock_event.binary_message.context.topic = 'topic'
        self.mock_event.binary_message.message = b'world'
        self.subscribe._on_stream_event_local(self.mock_event)

        # Assert that the ledApp.callback_message method is called with the correct arguments
        self.subscribe.ledApp.callback_message.assert_called_once_with(
            "topic",
            "world"
        )


     # Test error event function
    def test_on_stream_error(self):
        # Assert that the _on_stream_error method return False
        self.assertFalse(self.subscribe._on_stream_error(self.mock_error))


    # Test local error event function
    def test_on_stream_error_local(self):
        # Assert that the _on_stream_error_local method return False
        self.assertFalse(self.subscribe._on_stream_error_local(self.mock_error))

        
if __name__ == '__main__':
    unittest.main()