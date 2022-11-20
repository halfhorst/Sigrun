from enum import Enum


class ContainerTag(Enum):
    GAME = 'sigrun-game.py'
    SERVER = 'sigrun-server-name'
    PASSWORD = 'sigrun-server-password'

    def __init__(self, string: str):
        self.tag = string
