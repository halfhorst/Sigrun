import json
from typing import List
from importlib import resources

from sigrun.commands.base import Command, Context
from sigrun.commands.discord import CHAT_INPUT_TYPE


class ListGames(Command):

    def __init__(self, context: Context):
        super().__init__(context)

    @staticmethod
    def get_cli_description():
        return "List supported games."

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": "list-games",
            "description": ListGames.get_cli_description(),
            "default_permission": True,
        }

    def handler(self) -> str:
        games = []
        for game in resources.contents("sigrun.games"):
            with resources.open_text(f"sigrun.games.{game}", "metadata.json") as f:
                metadata = json.loads(f.read())
                games.append(metadata["name"])
        self.send_message(games)
