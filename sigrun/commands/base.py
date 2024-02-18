"""/**
https://github.com/discord/discord-api-docs/issues/2389
https://github.com/discord/discord-api-docs/pull/2362/files
https://discord.com/developers/docs/interactions/receiving-and-responding#followup-messages
**/"""


class Command:
    """The Sigrun command interface. It supports self-registration with Diregistering commands with Discord and two-phase execution."""

    @staticmethod
    def get_discord_name():
        """The name of this comand."""

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
