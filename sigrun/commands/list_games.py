from typing import List
from importlib import resources

from sigrun.commands.base import BaseCommand
from sigrun.commands.discord import CHAT_INPUT_TYPE

# from sigrun.model.game import GAMES


class ListGames(BaseCommand):
    name = "list-games"

    def __init__(self, options: List[dict]):
        pass

    @staticmethod
    def get_cli_description():
        return "List games that Sigrun supports."

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
            games.append(resources.op)
        # with resources.open_text("sigrun.games.valheim", "metadata.json") as f:
        #     return f.read()

    @staticmethod
    def is_defered() -> bool:
        return False
