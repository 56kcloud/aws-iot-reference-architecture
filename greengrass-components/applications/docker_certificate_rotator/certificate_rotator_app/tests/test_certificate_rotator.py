import unittest
from unittest.mock import MagicMock, patch
import json
from certificate_rotator.certificate_rotator import CertificateRotator  # noqa: E402

#*************************** Certificate Rotator tests ***************************#
class TestCertificateRotator(unittest.TestCase):
    # Initialisation of test class
    @classmethod
    def setUpClass(cls):
        # Mock IPC client for testing
        cls.mock_ipc_client = MagicMock()

        # Instantiate the Button class with mocked parameters
        cls.certificateRotator = CertificateRotator(
            ipc_client=cls.mock_ipc_client,
            serial_number="0123456789",
            lambda_csr_res_topic="lambda_csr_res",
            lambda_crt_ack_topic="lambda_crt_ack",
            device_csr_req_topic="device_csr_req",
            device_crt_topic="device_crt"
        )

        # Mock the Publish class to check if publish_to_topic is called
        cls.certificateRotator.publish.publish_to_topic = MagicMock()
        
        # Mock Certificate Signing Request (CSR)
        cls.mock_csr = MagicMock()
        # Mock private key
        cls.mock_private_key = MagicMock()


    # Test to publish a new Certificate Signing Request (CSR)
    @patch('cryptography.x509.CertificateSigningRequestBuilder')
    def test_publish_csr(self, mock_csr_builder):
        # Set up mock values
        mock_csr_builder.return_value.subject_name.return_value.sign.return_value = self.mock_csr
        self.mock_csr.public_bytes.return_value.decode.return_value.strip.return_value = 'MockResult'

        # Simulate a CSR request
        self.certificateRotator.callback_message(self.certificateRotator.device_csr_req_topic, None)

        # Check if publish was called with the correct arguments
        expected_csr_message = {
                "ThingName": self.certificateRotator.thing_name,
                "csr": "MockResult"
            }
        # Assert that the publish.publish_to_topic method is called with the correct arguments
        self.certificateRotator.publish.publish_to_topic.assert_called_with(self.certificateRotator.lambda_csr_res_topic, json.dumps(expected_csr_message))


    # Test to publish acknowledgement of the newly created certificate
    @patch('os.popen')
    @patch('builtins.open')
    def test_publish_ack(self, mock_open, mock_os_popen):
        # Set up mock values
        self.certificateRotator.private_key = self.mock_private_key
        self.mock_private_key.private_bytes.return_value = "MockPrivateKey"

        # Simulate the delivery of a new certificate
        new_certificate_message = {
                "certificatePem": "MockCertificatePem",
                "certificateArn": "MockCertificateArn"
            }
        self.certificateRotator.callback_message(self.certificateRotator.device_crt_topic, json.dumps(new_certificate_message))

        # Check if publish was called with the correct arguments
        expected_ack_message = {
                "ThingName": self.certificateRotator.thing_name,
                "certificateArn": new_certificate_message["certificateArn"]
            }
        # Assert that the publish.publish_to_topic method is called with the correct arguments
        self.certificateRotator.publish.publish_to_topic.assert_called_with(self.certificateRotator.lambda_crt_ack_topic, json.dumps(expected_ack_message))


    # Test that the new private key is written in the correct path
    @patch('os.popen')
    @patch('builtins.open')
    def test_path_key(self, mock_open, mock_os_popen):
        # Set up mock values
        self.certificateRotator.private_key = self.mock_private_key
        self.mock_private_key.private_bytes.return_value = "MockPrivateKey"

        # Simulate the delivery of a new certificate
        new_certificate_message = {
                "certificatePem": "MockCertificatePem",
                "certificateArn": "MockCertificateArn"
            }
        self.certificateRotator.callback_message(self.certificateRotator.device_crt_topic, json.dumps(new_certificate_message))

        # Assert that open is called with the correct arguments to write the private key
        mock_open.assert_any_call("/greengrass/v2/privKey.key", "wb")
        

    # Test that the new certificate is written in the correct path
    @patch('os.popen')
    @patch('builtins.open')
    def test_path_crt(self, mock_open, mock_os_popen):
        # Set up mock values
        self.certificateRotator.private_key = self.mock_private_key
        self.mock_private_key.private_bytes.return_value = "MockPrivateKey"

        # Simulate the delivery of a new certificate
        new_certificate_message = {
                "certificatePem": "MockCertificatePem",
                "certificateArn": "MockCertificateArn"
            }
        self.certificateRotator.callback_message(self.certificateRotator.device_crt_topic, json.dumps(new_certificate_message))

        # Assert that open is called with the correct arguments to write the private key
        mock_open.assert_any_call("/greengrass/v2/thingCert.crt", "w")


if __name__ == '__main__':
    unittest.main()