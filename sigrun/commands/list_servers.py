from sigrun.commands.base import Command
from sigrun.commands.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE
from sigrun.model.context import get_messager


class ListServers(Command):

    def __init__(self, game: str = ""):
        self.game = game

    @staticmethod
    def get_discord_name():
        return "list-servers"

    @staticmethod
    def get_cli_description():
        return "List existing servers for a game."

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": ListServers.get_discord_name(),
            "description": ListServers.get_cli_description(),
            "default_permission": True,
            "options": [
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "game",
                    "required": "false",
                    "description": "Only list servers of this game.",
                    "required": True,
                },
            ],
        }

    def handler(self) -> str:
        message = "Listing game servers"
        if self.game:
            message += f" for {self.game}"
        get_messager()(message)

    def __str__(self):
        return "ListServers"
