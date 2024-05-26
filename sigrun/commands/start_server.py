from loguru import logger

from sigrun.cloud import ec2
from sigrun.cloud.session import ec2_resource
from sigrun.commands.base import Command
from sigrun.exceptions import GameNotFoundError
from sigrun.model.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE
from sigrun.model.game import Game
from sigrun.model.messenger import get_messenger


class StartServer(Command):

    def __init__(self, game: str, server_name: str, password: str):
        try:
            self.game = Game(game)
        except ModuleNotFoundError:
            logger.error(f"Invalid game name {game}")
            raise GameNotFoundError
        self.server_name = server_name
        self.password = password

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
                    "name": "game",
                    "description": "The kind of game to start.",
                    "required": True,
                },
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "server_name",
                    "description": "The name of the server.",
                    "required": True,
                },
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "password",
                    "description": "The server password.",
                    "required": True,
                },
            ],
        }

    def handler(self):
        instance = ec2.get_non_terminated_instances(self.game.name, self.server_name)

        if not instance:
            get_messenger()(f"Creating {self.game} server {self.server_name}")
            self.create_instance()
            return
        instance = instance.pop()

        if instance.state["Name"] == "running":
            get_messenger()(
                f"{self.game} server {self.server_name} is already running!"
            )
            return

        if instance.state["Name"] == "stopped":
            get_messenger()(
                f"Restarting {self.game} server {self.server_name}"
            )  # TODO: Add instance id
            self.restart_instance(instance)
            return

        get_messenger()(
            f"I found an existing instance, but it's in an unrecognized state: {instance.state['Name']}. Please try again"
        )

    def create_instance(self):
        instance = ec2_resource.create_instances(
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/sdf",
                    "Ebs": {
                        "DeleteOnTermination": False,
                        "VolumeSize": self.game.storage,
                        "VolumeType": "gp3",
                    },
                }
            ],
            ImageId="ami-008fe2fc65df48dac",
            InstanceType=self.game.instance_type,
            MaxCount=1,
            MinCount=1,
            UserData=self.game.start_script,
        ).pop()

        instance.create_tags(
            Tags=[
                {"Key": "Game", "Value": self.game.name},
                {
                    "Key": "Name",
                    "Value": self.server_name,
                },
                {"Key": "Password", "Value": self.password},
            ]
        )

        get_messenger()(f"Started {self.game} instance {self.server_name}: {instance}")

    def restart_instance(self, instance):
        pass

    def __str__(self):
        return "StartServer"
