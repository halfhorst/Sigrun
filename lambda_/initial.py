import json
import os
import pprint

import boto3
from aws_lambda_typing import events
from loguru import logger
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from sigrun.commands import COMMANDS

secrets_manager = boto3.client("secretsmanager")
lambda_client = boto3.client("lambda")

CHANNEL_MESSAGE_WITH_SOURCE = 4
PING_TYPE = 1


# Context object
# https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
def main(event: events.APIGatewayProxyEventV2, context):
    """The handler for API calls assumed to originate from Discord.
    This is invoked for any `ANY \`. In other words, any request to
    the API flows through this method, but we assume the shape Discord
    emits."""
    logger.info(f"Received an event!: {event}")

    headers = event["headers"]
    raw_body = event["body"]
    body = json.loads(raw_body)
    logger.info(f"Headers: {headers}")
    logger.info(f"Message body: {body}")

    if not validate_signature(
        headers["x-signature-ed25519"], headers["x-signature-timestamp"], raw_body
    ):
        logger.warning("Signature not valid.")
        return {"statusCode": 401}
    logger.info("Signature valid.")

    if body["type"] == PING_TYPE:
        logger.info("Acking a ping.")
        return build_response(200, {"type": PING_TYPE})

    command_name = body["data"]["name"]
    command = COMMANDS.get(command_name)
    if command is None:
        logger.error(f"Command {command_name} is not supported.")
        return {"statusCode": 400}

    options = (
        {opt["name"]: opt["value"] for opt in body["data"]["options"]}
        if "options" in body["data"]
        else {}
    )

    logger.info("Command: " + command_name)
    logger.info("Options: " + pprint.pformat(options))
    # TODO: The EC2 implementation is much faster, try
    #       calling directly again insted of deferring
    invoke_deferred(
        {
            "command": command_name,
            "application_id": body["application_id"],
            "interaction_id": body["id"],
            "interaction_token": body["token"],
            "options": options,
        }
    )

    return build_response(200, {"type": 5})


def invoke_deferred(payload: dict):
    logger.info(f"Invoking deferred handler with {payload}")
    deferred_function_name = os.environ.get("DEFERRED_LAMBDA_NAME")
    lambda_client.invoke(
        FunctionName=deferred_function_name,
        InvocationType="Event",
        Payload=json.dumps(payload).encode("utf-8"),
    )


def validate_signature(signature: str, timestamp: str, body: str):
    verify_key = VerifyKey(bytes.fromhex(get_application_public_key()))
    try:
        verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
        return True
    except BadSignatureError:
        return False


def get_application_public_key():
    secret_string = json.loads(
        secrets_manager.get_secret_value(SecretId="APPLICATION_PUBLIC_KEY")[
            "SecretString"
        ]
    )
    return secret_string["APPLICATION_PUBLIC_KEY"]


def build_response(status_code: int, body: dict):
    headers = {"Content-Type": "application/json"}
    response = {
        "statusCode": status_code,
        "isBase64Encoded": "false",
        "headers": headers,
        "multiValueHeaders": {},
        "body": json.dumps(body),
    }

    logger.info(f"Response object: {response}")
    return response
