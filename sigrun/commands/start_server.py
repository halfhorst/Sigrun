from datetime import datetime, timezone

from botocore.exceptions import ClientError

from sigrun.cloud import ec2
from sigrun.commands.base import Command
from sigrun.model.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE
from sigrun.model.messenger import get_messenger


class StartServer(Command):

    def __init__(self, instance_id: str):
        self.instance_id = instance_id

    @staticmethod
    def get_discord_name():
        return "start-server"

    @staticmethod
    def get_cli_description():
        return """Start an instance of a game server. Will create if one doesn't
        currently eixst."""

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": StartServer.get_discord_name(),
            "description": StartServer.get_cli_description(),
            "default_permission": True,
            "options": [
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "instance_id",
                    "description": "The instance id of the server you want to start. You can get this by using `list-servers`.",
                    "required": True,
                }
            ],
        }

    def handler(self):
        instance = []
        try:
            instance = ec2.get_instance_by_id(self.instance_id)
        except ClientError as e:
            if e.response["Error"]["Code"] != "InvalidInstanceID.Malformed":
                raise e

        if not instance:
            get_messenger()("I couldn't find an instance with that ID!")
            return

        instance = instance.pop()
        state = instance.state["Name"]
        tags = {tag["Key"]: tag["Value"] for tag in instance.tags}
        game = tags["pretty_game"]
        server_name = tags["server_name"]
        password = tags["password"]

        if state == "running":
            get_messenger()(f"The {game} server {server_name} is already running!")
            return

        if state == "stopped":
            get_messenger()(
                f"Booting up {game} server {server_name} now! The password is {password}. Use `list-servers` to monitor its status."
            )
            response = instance.start()
            response = instance.create_tags(
                Tags=[
                    {
                        "Key": "start_time",
                        "Value": datetime.now(timezone.utc).isoformat(),
                    },
                ]
            )
            return

        get_messenger()(
            f"I found an existing instance, but it's in an unsupported state: {instance.state['Name'].upper()}. Please try again"
        )

    def __str__(self):
        return "StartServer"
