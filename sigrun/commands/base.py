from enum import Enum
from typing import Callable, List

from loguru import logger


"""/**
https://github.com/discord/discord-api-docs/issues/2389
https://github.com/discord/discord-api-docs/pull/2362/files
https://discord.com/developers/docs/interactions/receiving-and-responding#followup-messages
**/"""


class Context(Enum):
    DISCORD = 1
    CLI = 2


def get_message_sender(context: Context) -> Callable[[str], None]:
    if context == Context.DISCORD:
        # TODO:
        logger.info
    else:
        return logger.info


class Command:
    """The Sigrun command interface. It supports self-registration with Diregistering commands with Discord and two-phase
    execution."""

    # Context-specific messaging
    send_message: Callable

    def __init__(self, context: Context):
        self.send_message = get_message_sender(context)

    @staticmethod
    def get_cli_description():
        """A description for the command line interface. You should probably use the same as
        the one in the discord metadata."""
        raise NotImplementedError

    @staticmethod
    def get_discord_metadata():
        """Get command metadata for registering the command with Discord."""
        raise NotImplementedError

    @classmethod
    def handler(cls) -> str:
        """The handler for the command when it is invoked by the Lambda. This
        needs to return in 3 seconds."""
        raise NotImplementedError

    # @staticmethod
    # def is_deferred() -> bool:
    #     """The method that indicates if a command should be deferred. If `True`, after
    #     `handler` is run, the command will be placed in an SQS queue for further
    #     execution, where a second Lambda will run `follow_up`."""
    #     raise NotImplementedError

    # @classmethod
    # def deferred_handler(cls) -> str:
    #     """A followup method to run if the command is deferred"""
    #     raise NotImplementedError

    @classmethod
    def get_option(cls, name: str, options: list):
        """Retrieve a named option from the options list."""
        return [o for o in options if o["name"] == name][0]["value"]
