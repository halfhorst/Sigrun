import json

from loguru import logger

from sigrun.commands.base import BaseCommand
from sigrun.commands import factory


class DeferredCommandInput:
    command: BaseCommand
    options: dict
    application_id: str
    interaction_token: str

    def __init__(self, command, application_id: str, interaction_token: str):
        self.command = command
        self.application_id = application_id
        self.interaction_token = interaction_token

    @staticmethod
    def from_dict(body: dict):
        try:
            command_name = body.get("command")
            options = body.get("options")
            application_id = body.get("application_id")
            interaction_token = body.get("interaction_token")
        except KeyError:
            raise RuntimeError(f"Received an improperly formatted event body: {input}.")

        command = factory.get_command(command_name, options)
        return DeferredCommandInput(command, application_id, interaction_token)

    def to_json(self) -> str:
        return json.dumps(self.__dict__)
