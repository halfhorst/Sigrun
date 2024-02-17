from typing import List

import boto3
from loguru import logger

from sigrun.cloud.session import ec2
from sigrun.commands.base import Command
from sigrun.commands.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE


class StartServer(Command):

    def __init__(self, game: str, instance_name: str, password: str):
        self.game = Game(game)
        self.instance_name = instance_name
        self.password = password

    @staticmethod
    def get_cli_description():
        return "Start a game server instance. A new instance will be created if one does not already exist."

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": "start-server",
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
                    "name": "instance_name",
                    "description": "The name of the server instance.",
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
        instance = ec2.create_instances(
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/sdf",
                    "Ebs": {
                        "DeleteOnTermination": False,
                        "VolumeSize": self.game.storage,
                        "VolumeType": "gp3",
                    },
                }
            ],
            # Amazon Linux ARM
            # ImageId="ami-0ecb0bb5d6b19457a",
            ImageId="ami-008fe2fc65df48dac",
            InstanceType=self.game.instance_type,
            MaxCount=1,
            MinCount=1,
            UserData=self.game.start_script,
        ).pop()

        instance.create_tags(
            Tags=[
                {
                    "Key": "Name",
                    "Value": f"{self.game}-{self.instance_name}",
                }
            ]
        )

        self.send_message(f"Started {self.game} instance {self.instance_name}")

    def get_instance(self, name: str):
        # Check if an instance with the given name already exists
        instances = ec2.instances.filter(
            Filters=[{"Name": "tag:Name", "Values": [name]}]
        )

        for instance in instances:
            if instance.state["Name"] != "terminated":
                self.send_message(
                    f"An instance with the name '{name}' already exists (ID: {instance.id})."
                )
                return instance.id
