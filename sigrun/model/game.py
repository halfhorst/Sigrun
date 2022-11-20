class Game:
    """A Sigrun-supported game"""

    def __init__(self, name: str, task_definition: str):
        self.name = name
        self.task_definition = name

    def __str__(self):
        return self.name


VALHEIM = Game("Valheim", "Valheim")
