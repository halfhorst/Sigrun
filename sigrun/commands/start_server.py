from sigrun.cloud.session import ec2
from sigrun.commands.base import Command
from sigrun.commands.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE
from sigrun.model.context import get_messager
from sigrun.model.game import Game


class StartServer(Command):

    def __init__(self, game: str, server_name: str, password: str):
        try:
            self.game = Game(game)
        except ModuleNotFoundError:
            raise RuntimeError(f"Invalid game name {game}")
        self.server_name = server_name
        self.password = password

    @staticmethod
    def get_discord_name():
        return "start-server"

    @staticmethod
    def get_cli_description():
        return """Start an instance of a game server. Will create if one doesn't
        currently eixst."""

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": StartServer.get_discord_name(),
            "description": StartServer.get_cli_description(),
            "default_permission": True,
            "options": [
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "game",
                    "description": "The kind of game to start.",
                    "required": True,
                },
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "server_name",
                    "description": "The name of the server.",
                    "required": True,
                },
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "password",
                    "description": "The server password.",
                    "required": True,
                },
            ],
        }

    def handler(self) -> str:
        get_messager()(f"Starting {self.game} server {self.server_name}")
        # instance = ec2.create_instances(
        #     BlockDeviceMappings=[
        #         {
        #             "DeviceName": "/dev/sdf",
        #             "Ebs": {
        #                 "DeleteOnTermination": False,
        #                 "VolumeSize": self.game.storage,
        #                 "VolumeType": "gp3",
        #             },
        #         }
        #     ],
        #     # Amazon Linux ARM
        #     # ImageId="ami-0ecb0bb5d6b19457a",
        #     ImageId="ami-008fe2fc65df48dac",
        #     InstanceType=self.game.instance_type,
        #     MaxCount=1,
        #     MinCount=1,
        #     UserData=self.game.start_script,
        # ).pop()

        # instance.create_tags(
        #     Tags=[
        #         {
        #             "Key": "Name",
        #             "Value": f"{self.game}-{self.server_name}",
        #         }
        #     ]
        # )

        # get_messager()(f"Started {self.game} instance {self.server_name}")

    def get_instance(self, name: str):
        # Check if an instance with the given name already exists
        instances = ec2.instances.filter(
            Filters=[{"Name": "tag:Name", "Values": [name]}]
        )

        for instance in instances:
            if instance.state["Name"] != "terminated":
                get_messager()(
                    f"An instance with the name '{name}' already exists (ID: {instance.id})."
                )
                return instance.id

    def __str__(self):
        return "StartServer"
