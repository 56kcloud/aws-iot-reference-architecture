# Standard libraries
import traceback

#*************************** Subscribe ***************************#
class Subscribe:
    # Initialisation
    def __init__(self, ipc_client, certRotatorApp):
        self.ipc_client = ipc_client
        self.certRotatorApp = certRotatorApp


    # Subscribe function
    def subscribe_to_topic(self, topic):
        _topic = topic
        _qos = '1'
        return self.ipc_client.subscribe_to_iot_core(
            topic_name = _topic,
            qos = _qos,
            on_stream_event = self._on_stream_event,
            on_stream_error = self._on_stream_error,
            on_stream_closed = self._on_stream_closed
        )
  

    # Callback function for incoming messages
    def _on_stream_event(self, event) -> None:
        message = str(event.message.payload, 'utf-8')
        topic = event.message.topic_name
        print("Received new message on topic %s: %s" % (topic, message))
        self.certRotatorApp.callback_message(topic, message)


    # Callback function for incoming error
    def _on_stream_error(self, error: Exception) -> bool:
        print("Received a stream error.")
        traceback.print_exc()
        return False    # Return True to close stream, False to keep stream open.
    

    # Callback function for closing topic stream
    def _on_stream_closed(self) -> None:
        print("Subscribe to topic stream closed.")