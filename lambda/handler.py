import json

from loguru import logger
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from sigrun import COMMANDS

# TODO: Move this into a secret
APPLICATION_PUBLIC_KEY = "13ec6cb5326e5b5fb0394d8744540a3a108daba4bd454b193f3950a0bd8e9a72"

PING_TYPE = 1
APPLICATION_COMMAND_TYPE = 4


def main(event: dict, context):
    """The Lambda's entrypoint, its handler. This is invoked for any
    `ANY \`. In other words, any request to the API flows through
    this method."""
    logger.info(f"Received an event!: {event}")

    headers = event["headers"]
    try:
        raw_body = event["body"]
    except KeyError:
        return build_response(200, {}, {})

    logger.info(f"Headers: {headers}")
    logger.info(f"Raw body: {raw_body}")

    if not validate_signature(headers["x-signature-ed25519"],
                              headers["x-signature-timestamp"],
                              raw_body):
        logger.warning("Signature not valid. returning 401")
        return build_response(401, {}, {})

    logger.info("Signature valid.")

    body = json.loads(raw_body)

    if body["type"] == PING_TYPE:
        return build_response(200, {}, {"type": PING_TYPE})
    else:
        command = body["data"]["name"]
        options = body["data"]["options"] if "options" in body["data"] else []
        return build_response(200, {}, {"type": APPLICATION_COMMAND_TYPE , "data": COMMANDS.get(command).handler(options)})


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
