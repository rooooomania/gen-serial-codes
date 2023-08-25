import unittest
from unittest.mock import patch, MagicMock
from handler import lambda_handler


class TestLambdaHandler(unittest.TestCase):
    @patch("handler.boto3.client")
    def test_lambda_handler(self, mock_client):
        mock_s3_client = MagicMock()
        mock_client.return_value = mock_s3_client

        mock_s3_client.generate_presigned_url.return_value = (
            "https://serial-key-generator.s3.amazonaws.com/output_1234567890.txt"
        )

        event = {
            "queryStringParameters": {
                "ac": "ABCDEFGHJKLMNPRTUVWXY123456789",
                "skl": "15",
                "ic": "100",
            }
        }
        response = lambda_handler(event, None)

        mock_s3_client.put_object.assert_called_once()
        mock_s3_client.generate_presigned_url.assert_called_once()
        self.assertEqual(response["statusCode"], 200)
        self.assertTrue(
            response["body"].startswith(
                "https://serial-key-generator.s3.amazonaws.com/output_"
            )
        )

    @patch("handler.boto3.client")
    def test_lambda_handler_missing_parameters(self, mock_client):
        event = {"queryStringParameters": {}}
        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            response["body"],
            "Please specify the allowed characters, serial key length and issue count.",
        )

    @patch("handler.boto3.client")
    def test_lambda_handler_issue_count_greater_than_1000000(self, mock_client):
        event = {
            "queryStringParameters": {
                "ac": "ABCDEFGHJKLMNPRTUVWXY123456789",
                "skl": "15",
                "ic": "1000001",
            }
        }
        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            response["body"], "The issue count cannot be greater than 1000000."
        )

    @patch("handler.boto3.client")
    def test_lambda_handler_non_repeating_serial_keys(self, mock_client):
        mock_s3_client = MagicMock()
        mock_client.return_value = mock_s3_client

        mock_s3_client.generate_presigned_url.return_value = (
            "https://serial-key-generator.s3.amazonaws.com/output_1234567890.txt"
        )

        event = {
            "queryStringParameters": {
                "ac": "ABC",
                "skl": "3",
                "ic": "10",
                "norepeat": "true",
            }
        }
        response = lambda_handler(event, None)

        mock_s3_client.put_object.assert_called_once()
        mock_s3_client.generate_presigned_url.assert_called_once()
        self.assertEqual(response["statusCode"], 200)
        self.assertTrue(
            response["body"].startswith(
                "https://serial-key-generator.s3.amazonaws.com/output_"
            )
        )


if __name__ == "__main__":
    unittest.main()
