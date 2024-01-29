# Standard libraries
import json
import os
# Libraries
from pubsub.pub import Publish
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.x509.oid import NameOID

#*************************** Certificate Rotator ***************************#
class CertificateRotator:
    # Initialisation
    def __init__(self, ipc_client, serial_number, lambda_csr_res_topic, lambda_crt_ack_topic, device_csr_req_topic, device_crt_topic):
        self.thing_name = serial_number
        self.lambda_csr_res_topic = lambda_csr_res_topic
        self.lambda_crt_ack_topic = lambda_crt_ack_topic
        self.device_csr_req_topic = device_csr_req_topic
        self.device_crt_topic = device_crt_topic
        self.private_key = None

        # New instance
        self.publish = Publish(ipc_client)

    # Callback message function
    def callback_message(self, topic, message):
        if topic == self.device_csr_req_topic:
            self.create_csr()
        if topic == self.device_crt_topic:
            self.rotate_certificate(message)


    # Create Certificate Signing Request (CSR)
    def create_csr(self):
        common_name = 'AWS IoT Certificate'

        # Generate a new private key
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # Create a Certificate Signing Request (CSR)
        csr = x509.CertificateSigningRequestBuilder().subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
        ).sign(self.private_key, hashes.SHA256())

        message = {
                "ThingName": self.thing_name,
                "csr": csr.public_bytes(serialization.Encoding.PEM).decode('utf-8').strip()
            }

        # Publish CSR
        self.publish.publish_to_topic(self.lambda_csr_res_topic, json.dumps(message))


    # Rotate the old certificate with the new one
    def rotate_certificate(self, newCertificate):
        private_key_path = '/greengrass/v2/privKey.key'
        certificate_path = '/greengrass/v2/thingCert.crt'

        # Load the json to a string
        resp = json.loads(newCertificate)

        # Overwrite old private key by new private key
        with open(private_key_path, 'wb') as file:
            file.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # Overwrite old certificate by new certificate
        with open(certificate_path, 'w') as file:
            file.write(resp["certificatePem"])

        message = {
                "ThingName": self.thing_name,
                "certificateArn": resp["certificateArn"]
            }

        # Publish acknowledgement of the newly created certificate
        self.publish.publish_to_topic(self.lambda_crt_ack_topic, json.dumps(message))

        os.popen("systemctl restart greengrass") # nosec


    # Certificate rotator application
    def app(self):
        # Keep the main thread alive, or the process will exit.
        while True:
            pass