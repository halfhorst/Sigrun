import pprint
from loguru import logger
import httpx

from sigrun.model.messenger import set_messenger
from sigrun.commands import COMMANDS


def main(event, context):
    """The handler for deferred commands placed on the SQS queue.
    This is for longer-running activities.
    """
    logger.info(f"Event is {event}")
    command_name = event["command"]
    application_id = event["application_id"]
    interaction_token = event["interaction_token"]
    options = event["options"]

    set_messenger(
        lambda content: send_followup(content, application_id, interaction_token)
    )

    command = COMMANDS.get(command_name)

    logger.info("Command: " + command_name)
    logger.info("Options: " + pprint.pformat(options))
    command(**options).handler()


def send_followup(content: str, application_id: str, interaction_token: str):
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
    r = httpx.post(url, data={"content": content})
    logger.info(f"Https response: {r}")
