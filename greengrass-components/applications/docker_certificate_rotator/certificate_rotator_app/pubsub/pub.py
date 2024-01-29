#*************************** Publish ***************************#
class Publish:
    # Initialisation
    def __init__(self, ipc_client):
        self.ipc_client = ipc_client
    
    
    # Publishing messages in the topic
    def publish_to_topic(self, topic, message):
        _topic = topic
        _qos = '1'
        payload = message
        return self.ipc_client.publish_to_iot_core(
            topic_name=_topic,
            qos=_qos,
            payload=payload
        )