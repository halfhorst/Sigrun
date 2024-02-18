import json
import pprint

import boto3
from aws_lambda_typing import events
from loguru import logger
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from sigrun.commands import COMMANDS, discord
from sigrun.model.context import set_context_discord

client = boto3.client(service_name="secretsmanager")
sqs_client = boto3.client("sqs")

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

    application_id = body["application_id"]
    interaction_id = body["id"]
    interaction_token = body["token"]

    set_context_discord(application_id, interaction_token, headers)

    if body["type"] == PING_TYPE:
        logger.warn("Acking a ping.")
        # return discord.respond(
        #     json.dumps({"type": PING_TYPE}),
        #     application_id,
        #     interaction_token,
        #     headers,
        #     status_code=200,
        # )

    command_name = body["data"]["name"]
    options = body["data"]["options"] if "options" in body["data"] else []

    command = COMMANDS.get(command_name)
    if command is None:
        logger.error(f"Command {command_name} is not supported.")
        # return discord.respond("foo")

    logger.info("Command " + command_name)
    logger.info("Options " + ",".join(pprint.pformat(options)))
    # command.handler(**options)


def validate_signature(signature: str, timestamp: str, body: str):
    verify_key = VerifyKey(bytes.fromhex(get_application_public_key))
    try:
        verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
        return True
    except BadSignatureError:
        return False


def get_application_public_key():
    secret_string = json.loads(
        client.get_secret_value(SecretId="APPLICATION_PUBLIC_KEY")["SecretString"]
    )
    return secret_string["APPLICATION_PUBLIC_KEY"]
