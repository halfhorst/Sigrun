import json

import boto3
from aws_lambda_typing import events
from loguru import logger
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from sigrun.commands import factory
from sigrun.commands.deferred_command import DeferredCommandInput

# TODO: Move this into a secret
APPLICATION_PUBLIC_KEY = "13ec6cb5326e5b5fb0394d8744540a3a108daba4bd454b193f3950a0bd8e9a72"
QUEUE_NAME = "SigrunMessageQueue"
PING_TYPE = 1
APPLICATION_COMMAND_TYPE = 4

sqs_client = boto3.client('sqs')


# Context object
# https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
def main(event: events.APIGatewayProxyEventV2, context):
    """The handler for API calls assumed to originate from Discord.
    This is invoked for any `ANY \`. In other words, any request to 
    the API flows through this method, but we assume the shape Discord
    emits."""
    logger.info(f"Received an event!: {event}")

    headers = event["headers"]
    try:
        raw_body = event["body"]
    except KeyError:
        return build_response(200, {}, {})
    body = json.loads(raw_body)
    logger.info(f"Headers: {headers}")
    logger.info(f"Message body: {body}")

    if not validate_signature(headers["x-signature-ed25519"],
                              headers["x-signature-timestamp"],
                              raw_body):
        logger.warning("Signature not valid. returning 401")
        return build_response(401, {}, {})
    logger.info("Signature valid.")

    if body["type"] == PING_TYPE:
        return build_response(200, {}, {"type": PING_TYPE})

    command_name = body["data"]["name"]
    options = body["data"]["options"] if "options" in body["data"] else []

    command = factory.get_command(command_name, options)
    response = command.handler()

    if command.is_deferred():
        enqueue(command, options, body['application_id'], body['token'])

    return build_response(200, {}, {"type": APPLICATION_COMMAND_TYPE, "data": {"content": response}})


def enqueue(command, options, application_id, interaction_token):
    queue_url = sqs_client.get_queue_url(QueueName=QUEUE_NAME)[QUEUE_NAME]
    if queue_url is None:
        logger.error("Failed to fine SQS queue to enqueue to.")
        return

    deferred_command_input = DeferredCommandInput(command, options, application_id, interaction_token)
    sqs_client.send_message(QueueUrl=queue_url, MessageBody=deferred_command_input.to_json(), )


def validate_signature(signature: str, timestamp: str, body: str):
    verify_key = VerifyKey(bytes.fromhex(APPLICATION_PUBLIC_KEY))
    try:
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
        return True
    except BadSignatureError:
        return False


def build_response(status_code: int, headers: dict, body: dict):
    headers["Content-Type"] = "application/json"
    response = {
        "statusCode": status_code,
        "isBase64Encoded": "false",
        "headers": headers,
        "multiValueHeaders": {},
        "body": json.dumps(body)
    }

    logger.info(f"Response object: {response}")
    return response
