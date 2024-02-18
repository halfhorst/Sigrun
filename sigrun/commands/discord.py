import json

import httpx
from loguru import logger

CHAT_INPUT_TYPE = 1
STRING_OPTION_TYPE = 3
APPLICATION_COMMAND_TYPE = 4

INITIAL_RESPONSE_URL = "https://discord.com/api/v10/interactions/{interaction_id}/{interaction_token}/callback"
FOLLOW_UP_URL = (
    "https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
)


def respond(
    body: str,
    application_id: str,
    interaction_token: str,
    headers: dict,
    status_code: int,
):
    headers["Content-Type"] = "application/json"
    response = {
        "statusCode": status_code,
        "isBase64Encoded": "false",
        "headers": headers,
        "multiValueHeaders": {},
        "body": body,
    }
    url = FOLLOW_UP_URL.format(
        application_id=application_id, interaction_token=interaction_token
    )
    logger.info(f"POSTING to discord: {url}, {response}, {headers}")
    httpx.post(
        url,
        json=json.reads(response),
        headers=headers,
    )
