from loguru import logger

from sigrun.cloud import ec2
from sigrun.cloud.session import ec2_resource
from sigrun.commands.base import Command
from sigrun.exceptions import GameNotFoundError
from sigrun.model.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE
from sigrun.model.game import Game
from sigrun.model.messenger import get_messenger


class StopServer(Command):

    def __init__(self, game: str, server_name: str):
        try:
            self.game = Game(game)
        except ModuleNotFoundError:
            logger.error(f"Invalid game name {game}")
            raise GameNotFoundError
        self.server_name = server_name

    @staticmethod
    def get_discord_name():
        return "stop-server"

    @staticmethod
    def get_cli_description():
        return "Stop an instance of a game server."

    @staticmethod
    def get_discord_metadata():
        return {
            "type": CHAT_INPUT_TYPE,
            "name": StopServer.get_discord_name(),
            "description": StopServer.get_cli_description(),
            "default_permission": True,
            "options": [
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "game",
                    "description": "The kind of game of the instance you want to stop",
                    "required": True,
                },
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "server_name",
                    "description": "The name of the server to stop.",
                    "required": True,
                },
            ],
        }

    def handler(self):
        instance = ec2.get_non_terminated_instance(
            ec2.get_tag_name(str(self.game), self.server_name)
        )

        # TODO: More than one instance is a critical failure

        if not instance:
            get_messenger()("No instances found with that name!")
            return
        instance = instance.pop()

        if instance.state["Name"] == "running":
            get_messenger()(f"Stopping {self.game} server {self.server_name}")
            self.stop_instance(instance)
            response = ec2_client.stop_instances(InstanceIds=[instance_id])
            return

        if instance.state["Name"] == "stopped":
            get_messenger()(
                f"{self.game} server {self.server_name} is already stopped!"
            )
            pass

    def stop_instance(self, instance):
        pass

    def __str__(self):
        return "StopServer"
