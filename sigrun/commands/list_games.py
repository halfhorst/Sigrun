import json
from importlib import resources

from sigrun.commands.base import Command
from sigrun.commands.discord import CHAT_INPUT_TYPE
from sigrun.model.context import get_messager


class ListGames(Command):

    @staticmethod
    def get_discord_name():
        return "list_games"

    @staticmethod
    def get_cli_description():
        return "List supported games."

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": ListGames.get_discord_name(),
            "description": ListGames.get_cli_description(),
            "default_permission": True,
        }

    def handler(self) -> str:
        games = []
        for game in resources.contents("sigrun.games"):
            with resources.open_text(f"sigrun.games.{game}", "metadata.json") as f:
                metadata = json.loads(f.read())
                games.append(metadata["name"])
        get_messager()(games)

    def __str__(self):
        return "ListGames"
