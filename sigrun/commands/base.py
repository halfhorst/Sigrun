# Lambda EFS mount requires path begin with /mnt.
SERVER_DATA_ROOT = "/mnt/server_data"

"""/**
https://github.com/discord/discord-api-docs/issues/2389
https://github.com/discord/discord-api-docs/pull/2362/files
https://discord.com/developers/docs/interactions/receiving-and-responding#followup-messages
**/"""


class BaseCommand:
    """The Sigrun command interface. It supports registerin commands with Discord and two-phase
       execution."""
    name: str

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

    @classmethod
    def is_deferred(cls) -> bool:
        """The method that indicates if a command should be deferred. If `True`, after
           `handler` is run, the command will be placed in an SQS queue for further
           execution, where a second Lambda will run `follow_up`."""
        raise NotImplementedError

    @classmethod
    def deferred_handler(cls) -> str:
        """A followup method to run if the command is deferred"""
        raise NotImplementedError

    @classmethod
    def get_option(cls, name: str, options: list):
        """Retrieve a named option from the options list."""
        return [o for o in options if o["name"] == name][0]["value"]
