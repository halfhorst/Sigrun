from typing import Optional

"""/**
https://github.com/discord/discord-api-docs/issues/2389
https://github.com/discord/discord-api-docs/pull/2362/files
https://discord.com/developers/docs/interactions/receiving-and-responding#followup-messages
**/"""


class Command:
    """The Sigrun command interface. It supports self-registration with Diregistering commands with Discord and two-phase execution."""

    @staticmethod
    def get_discord_name() -> str:
        """The name of this comand."""
        raise NotImplementedError

    # @staticmethod
    # def is_deferred() -> bool:
    #     """Discord interactions must be responded to within 3 seconds. If your command takes longer than this, indicate it is
    #     deferred by overriding this method. A deferred command will be acknlowedged by `get_ack_message` and then executed
    #     asynchronously by a second Lambda function."""
    #     return False

    @staticmethod
    def get_ack_message() -> str:
        """The message an interaction is responded to with immediately."""
        return "I got your request. This is going to take a second."

    @staticmethod
    def get_cli_description() -> str:
        """A description for the command line interface. You should probably use the same as
        the one in the discord metadata."""
        raise NotImplementedError

    @staticmethod
    def get_discord_metadata():
        """Get command metadata for registering the command with Discord."""
        raise NotImplementedError

    @classmethod
    def handler(cls) -> Optional[str]:
        """The handler for the command when it is invoked by the Lambda. This
        needs to return in 3 seconds."""
        raise NotImplementedError
