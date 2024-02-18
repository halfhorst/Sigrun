from sigrun.commands.base import Command
from sigrun.model.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE
from sigrun.model.messenger import get_messenger
from sigrun.model.game import Game


class ServerStatus(Command):

    def __init__(self, game: str, server_name: str):
        self.game = Game(game)
        self.server_name = server_name

    @staticmethod
    def get_discord_name():
        return "server-status"

    @staticmethod
    def get_cli_description():
        return "List information about a game server."

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": ServerStatus.get_discord_name(),
            "description": ServerStatus.get_cli_description(),
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
            ],
        }

    def handler(self):
        get_messenger()(f"Getting server status for {self.game} {self.server_name}")

    def __str__(self):
        return "ServerStatus"
