from sigrun.commands.base import Command
from sigrun.commands.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE
from sigrun.model.context import get_messager
from sigrun.model.game import Game


class StopServer(Command):

    def __init__(self, game: str, server_name: str):
        self.game = Game(game)
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

    def handler(self) -> str:
        get_messager()(f"Stopping server {self.server_name}")

    def __str__(self):
        return "StopServer"
