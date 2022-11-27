import json

import httpx
from aws_lambda_typing import events

from sigrun.commands.deferred_command import DeferredCommandInput


# SQS event shape
# https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
def main(event: events.SQSEvent, context):
    """The handler for deferred commands placed on the SQS queue.
    This is for longer-running activities.
    """
    # de-duplicate?
    for command_input in [parse_record(record) for record in event.Records]:
        response = command_input.command.deferred_handler()
        send_followup(response, command_input.application_id, command_input.interaction_token)


def parse_record(record: events.sqs.SQSMessage) -> DeferredCommandInput:
    parsed_body = json.loads(record['body'])
    return DeferredCommandInput.from_dict(parsed_body)


def send_followup(content: str, application_id: str, interaction_token: str):
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
    httpx.post(url, data={'content': content})
