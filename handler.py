"""
Generates unique serial keys and writes them to a CSV file.
How to specify the allowed characters, serial key length and issue count:
https://{{endpoint}}/serial-key-generator?ac=ABCDEFGHJKLMNPRTUVWXY123456789&skl=15&ic=1000000
"""
from datetime import datetime
import random
import csv
import io
import boto3
from botocore.exceptions import NoCredentialsError


def lambda_handler(event, context):
    """
    Generates unique serial keys and writes them to a CSV file.

    Args:
        event (dict): A dictionary containing the query string parameters.
            - allowed_characters (str): A string containing the characters allowed in the serial keys.
            - serial_key_length (int): The length of each serial key.
            - issue_count (int): The number of unique serial keys to generate.
        context (object): An object containing information about the current execution environment.

    Returns:
        dict: A dictionary containing the generated serial keys.
            - serial_keys (list): A list of unique serial keys.
    """

    # Set Constants from event['queryStringParameters']
    # Throw an error if any of the required parameters are missing
    if (
        "queryStringParameters" not in event
        or "ac" not in event["queryStringParameters"]
        or "skl" not in event["queryStringParameters"]
        or "ic" not in event["queryStringParameters"]
    ):
        return {
            "statusCode": 400,
            "body": "Please specify the allowed characters, serial key length and issue count.",
        }

    # If the ic parameter is greater than 1000000, return an error
    if int(event["queryStringParameters"]["ic"]) > 1000000:
        return {
            "statusCode": 400,
            "body": "The issue count cannot be greater than 1000000.",
        }

    allowed_characters = event["queryStringParameters"]["ac"]
    serial_key_length = int(event["queryStringParameters"]["skl"])
    issue_count = int(event["queryStringParameters"]["ic"])

    def generate_serial_key():
        return "".join(
            random.choice(allowed_characters) for _ in range(serial_key_length)
        )

    def generate_non_repeating_string(allowed_characters, length):
        if length > 0 and len(allowed_characters) < 2:
            raise ValueError(
                "At least two different characters are required to avoid repetition."
            )

        result = []
        last_char = None

        for _ in range(length):
            # Choose a character that is not equal to the last one
            char = random.choice([c for c in allowed_characters if c != last_char])
            result.append(char)
            last_char = char

        return "".join(result)

    # Function to generate unique serial keys
    def generate_unique_serial_keys():
        unique_serial_keys = set()
        while len(unique_serial_keys) < issue_count:
            # If `norepeat` is specified in event['queryStringParameters'], call generate_non_repeating_string()
            if "norepeat" in event["queryStringParameters"]:
                serial_key = generate_non_repeating_string(
                    allowed_characters, serial_key_length
                )
            else:
                serial_key = generate_serial_key()
            unique_serial_keys.add(serial_key)
        return list(unique_serial_keys)

    # Generate the required unique serial keys
    unique_serial_keys = generate_unique_serial_keys()

    output = io.StringIO()
    writer = csv.writer(output)
    for serial_key in unique_serial_keys:
        writer.writerow([serial_key])

    # Reset the cursor to the beginning of the file
    output.seek(0)

    # Return the CSV as a response

    print("CSV file created.")

    # Bucket name: serial-key-generator
    # Object name: output_yyyymmddhhmmss.csv
    bucket_name = "serial-key-generator"
    file_name = f"output_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    s3_client = boto3.client("s3")

    # Generate a presigned URL for the S3 object
    try:
        s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=output.getvalue())
    except NoCredentialsError:
        print("Credentials not available")
    pre_signed_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": file_name},
        # Expires in 300 seconds (5 min)
        ExpiresIn=300,
    )

    return {"statusCode": 200, "body": pre_signed_url}
