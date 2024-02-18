import json
from typing import Callable

from loguru import logger

from sigrun.commands.discord import APPLICATION_COMMAND_TYPE, respond

messager = logger.info


def set_context_cli():
    messager = logger.info


def set_context_discord(application_id: str, interaction_token: str, headers: dict):
    def partial(message):
        body = json.dumps(
            {"type": APPLICATION_COMMAND_TYPE, "data": {"content": message}}
        )
        return respond(body, application_id, interaction_token, headers, 200)

    messager = partial


def get_messager() -> Callable[[str], None]:
    return messager
