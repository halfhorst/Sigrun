import json
from typing import Dict

import httpx
from aws_lambda_typing import events
from loguru import logger

from sigrun.commands import factory
from sigrun.commands.base import BaseCommand


# SQS event shape
# https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
def main(event: events.SQSEvent, context):
    """The handler for deferred commands placed on the SQS queue.
    This is for longer-running activities.
    """
    # de-duplicate?
    for command_input in [parse_record(record) for record in event.Records]:
        response = command_input.command.deferred_handler(command_input.options,
                                                          command_input.interaction_token)
        send_followup(response, command_input.application_id, command_input.interaction_token)


class DeferredCommandInput:
    command: BaseCommand
    options: Dict
    application_id: str
    interaction_token: str

    def __init__(self, command, options: Dict, application_id: str, interaction_token: str):
        self.command = command
        self.options = options
        self.application_id = application_id
        self.interaction_token = interaction_token

    @staticmethod
    def from_dict(body: Dict):
        try:
            command_name = body.get("command")
            options = body.get("options")
            application_id = body.get("application_id")
            interaction_token = body.get("interaction_token")
        except KeyError:
            logger.error(f"Received an improperly formatted event body: {input}.")
        command = factory.get_command(command_name)
        return DeferredCommandInput(command, options, application_id, interaction_token)

    def to_json(self) -> dict:
        return json.dumps(self.__dict__)


def parse_record(record: events.sqs.SQSMessage) -> DeferredCommandInput:
    parsed_boyd = json.loads(record['body'])
    return DeferredCommandInput.from_dict(parsed_boyd)


def send_followup(content: dict, application_id: str, interaction_token: str):
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
    httpx.post(url, data={'content': content})
