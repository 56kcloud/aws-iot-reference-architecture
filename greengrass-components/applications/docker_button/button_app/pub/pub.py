from awsiot.greengrasscoreipc.model import PublishMessage, BinaryMessage

#*************************** Publish ***************************#
class Publish:
    # Initialisation
    def __init__(self, ipc_client):
        self.ipc_client = ipc_client
    
    # Publishing messages in the topic at local level
    def publish_to_topic(self, topic, message):
        _topic = topic
        binary_message = BinaryMessage(message=bytes(message, 'utf-8'))
        publish_message = PublishMessage(binary_message=binary_message)
        return self.ipc_client.publish_to_topic(
            topic=_topic,
            publish_message=publish_message
        )