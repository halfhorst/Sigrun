"""This is a global configuration module for dictating where
messages are sent by Sigrun's commands."""

from typing import Callable

from loguru import logger


messenger = logger.info


def set_messenger(callable: Callable[[str], None]):
    global messenger
    messenger = callable


def get_messenger() -> Callable[[str], None]:
    return messenger
