import json
from importlib import resources
import pprint

from sigrun.commands.base import Command
from sigrun.model.discord import CHAT_INPUT_TYPE
from sigrun.model.messenger import get_messenger


class ListGames(Command):

    @staticmethod
    def get_discord_name():
        return "list-games"

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

    def handler(self):
        games = []
        for game in resources.contents("sigrun.games"):
            with resources.open_text(f"sigrun.games.{game}", "metadata.json") as f:
                metadata = json.loads(f.read())
                games.append(metadata["name"])
        get_messenger()(pprint.pformat(games))

    def __str__(self):
        return "ListGames"
