import json
from dataclasses import dataclass
from importlib import resources

from sigrun.exceptions import MissingStartupScriptError


@dataclass
class Game:
    start_script: str
    name: str
    storage: int
    instance_type: str

    def __init__(self, name: str):
        name = name.lower()
        # NOTE: The name that a user can use for a particular game in an argument
        #       corresponds to the dir name containing the game's metadata.
        with resources.open_text(f"sigrun.games.{name}", "metadata.json") as f:
            metadata = json.loads(f.read())
            for key, value in metadata.items():
                setattr(self, key, value)

        with resources.open_text(f"sigrun.games.{name}", "start.sh") as f:
            self.start_script = f.read()

        if not hasattr(self, "start_script") or not hasattr(self, "name"):
            raise MissingStartupScriptError(
                f"Game {name} does not have valid metadata."
            )

    def __str__(self) -> str:
        return self.name
