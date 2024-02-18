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
        for short_name in resources.contents("sigrun.games"):
            with resources.open_text(
                f"sigrun.games.{short_name}", "metadata.json"
            ) as f:
                metadata = json.loads(f.read())
                games.append({metadata["name"]: short_name})
        get_messenger()(
            f"I support the following games and corresponding arguments:\n{pprint.pformat(games)}"
        )

    def __str__(self):
        return "ListGames"
