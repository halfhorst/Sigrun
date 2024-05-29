import json
from dataclasses import dataclass
from importlib import resources

from sigrun.exceptions import GameNotFoundError, MissingStartupScriptError


@dataclass
class Game:
    start_script: str
    name: str
    pretty_name: str
    storage: int
    instance_type: str

    def __init__(self, name: str):
        # NOTE: The name that a user can use for a particular game in an argument
        #       corresponds to the dir name containing the game's metadata.
        try:
            with resources.open_text(f"sigrun.games.{name}", "metadata.json") as f:
                self.name = name
                metadata = json.loads(f.read())
                for key, value in metadata.items():
                    setattr(self, key, value)
        except ModuleNotFoundError:
            raise GameNotFoundError

        with resources.open_text(f"sigrun.games.{name}", "startup.sh") as f:
            self.start_script = f.read()

        if not hasattr(self, "start_script") or not hasattr(self, "name"):
            raise MissingStartupScriptError(
                f"Game {name} does not have valid metadata."
            )

    def __str__(self) -> str:
        return self.pretty_name

    def __repr__(self) -> str:
        return f"Game({self.name})"
