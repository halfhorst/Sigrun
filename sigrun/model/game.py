from dataclasses import dataclass


@dataclass
class Game:
    name: str
    storage: int
    instance_type: str
    # boot: str
    # start: str


GAMES = {
    "Valheim": Game("Valheim", 10, "m7g.xlarge"),
    "Seven Days to Die": Game("Seven Days to Die", 10, "m7i.xlarge"),
    "Palworld": Game("Palworld", 10, "m7g.xlarge"),
}

# Below for backwards compatibility


# class Game:
#     """A Sigrun-supported game"""

#     def __init__(self, name: str, task_definition: str):
#         self.name = name
#         self.task_definition = name

#     def __str__(self):
#         return self.name


# VALHEIM = Game("Valheim", "Valheim")
