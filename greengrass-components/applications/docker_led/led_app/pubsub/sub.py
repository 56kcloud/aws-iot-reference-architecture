# Standard libraries
import traceback

#*************************** Subscribe ***************************#
class Subscribe:
    # Initialisation
    def __init__(self, ipc_client, ledApp):
        self.ipc_client = ipc_client
        self.ledApp = ledApp


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
        self.ledApp.callback_message(topic, message)


    # Callback function for incoming error
    def _on_stream_error(self, error: Exception) -> bool:
        print("Received a stream error.")
        traceback.print_exc()
        return False    # Return True to close stream, False to keep stream open.
    

    # Callback function for closing topic stream
    def _on_stream_closed(self) -> None:
        print("Subscribe to topic stream closed.")

    
    # Subscribe function at local level
    def subscribe_to_topic_local(self, topic):
        _topic = topic
        return self.ipc_client.subscribe_to_topic(
            topic = _topic,
            on_stream_event = self._on_stream_event_local,
            on_stream_error = self._on_stream_error_local,
            on_stream_closed = self._on_stream_closed_local
        )


    # Callback function for incoming messages at local level
    def _on_stream_event_local(self, event) -> None:
        message = str(event.binary_message.message, 'utf-8')
        topic = event.binary_message.context.topic
        print("Received new message on topic %s: %s" % (topic, message))
        self.ledApp.callback_message(topic, message)


    # Callback function for incoming error at local level
    def _on_stream_error_local(self, error: Exception) -> bool:
        print("Received a stream error.")
        traceback.print_exc()
        return False    # Return True to close stream, False to keep stream open.
    
    
    # Callback function for closing topic stream at local level
    def _on_stream_closed_local(self) -> None:
        print("Subscribe to topic stream closed.")