from dataclasses import dataclass
from importlib import resources
import json


@dataclass
class Game:
    start_script: str
    name: str
    storage: int
    instance_type: str

    def __init__(self, name: str):
        with resources.open_text(f"sigrun.games.{name}", "metadata.json") as f:
            metadata = json.loads(f.read())
            self.name = metadata["name"]
            self.storage = metadata["storage"]
            self.instance_type = metadata["instance_type"]

        with resources.open_text(f"sigrun.games.{name}", "start.sh") as f:
            self.start_script = f.read()
