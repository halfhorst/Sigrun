from typing import List

from sigrun.commands.base import BaseCommand
from sigrun.commands.discord import CHAT_INPUT_TYPE
from sigrun.model.game import GAMES


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
        return ", ".join(GAMES.keys())

    @staticmethod
    def is_defered() -> bool:
        return False
