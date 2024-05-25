from sigrun.cloud import ec2
from sigrun.cloud.session import ec2_resource
from sigrun.commands.base import Command
from sigrun.model.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE
from sigrun.model.messenger import get_messenger


class ListServers(Command):

    def __init__(self, game: str = ""):
        self.game = game

    @staticmethod
    def get_discord_name():
        return "list-servers"

    @staticmethod
    def get_cli_description():
        return "List existing servers for a game."

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": ListServers.get_discord_name(),
            "description": ListServers.get_cli_description(),
            "default_permission": True,
            "options": [
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "game",
                    "required": "false",
                    "description": "Only list servers of this game.",
                    "required": False,
                },
            ],
        }

    def handler(self):
        message = "Listing game servers"
        if self.game:
            message += f" for {self.game}"
        get_messenger()(message)

        instances = ec2.get_non_terminated_instance()
        # instance_id
        # launch_time
        # calculate uptime
        # from tags: game server name password
        # monitoring: cpu, mem, connections

        import pdb

        pdb.set_trace()

    def __str__(self):
        return "ListServers"
