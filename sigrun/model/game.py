from dataclasses import dataclass
from importlib import resources
import json


@dataclass
class Game:
    # metadata: dict
    start_script: str
    name: str
    # storage: int
    # instance_type: str
    # boot: str
    # start: str

    def __init__(self, name: str):
        with resources.open_text(f"sigrun.games.{name}", "metadata.json") as f:
            metadata = json.loads(f.read())
            self.name = metadata["name"]

        with resources.open_text(f"sigrun.games.{name}", "start.sh") as f:
            self.start_script = f.read()


# GAMES = {
#     "Valheim": Game("Valheim", 10, "m7g.xlarge"),
#     "Seven Days to Die": Game("Seven Days to Die", 10, "m7i.xlarge"),
#     "Palworld": Game("Palworld", 10, "m7g.xlarge"),
# }

# Below for backwards compatibility


# class Game:
#     """A Sigrun-supported game"""

#     def __init__(self, name: str, task_definition: str):
#         self.name = name
#         self.task_definition = name

#     def __str__(self):
#         return self.name


# VALHEIM = Game("Valheim", "Valheim")
