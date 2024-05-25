import json
import pprint
from importlib import resources

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
        games = {}
        for short_name in resources.contents("sigrun.games"):
            with resources.open_text(
                f"sigrun.games.{short_name}", "metadata.json"
            ) as f:
                metadata = json.loads(f.read())
                games.update({metadata["name"]: short_name})

        format_name = lambda name, short: f"- '{short}': {name}"
        game_list = "\n".join(
            [format_name(name, short) for name, short in games.items()]
        )
        get_messenger()(f"I support the following game arguments:\n{game_list}")

    def __str__(self):
        return "ListGames"
