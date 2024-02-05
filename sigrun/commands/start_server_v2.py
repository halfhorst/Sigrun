from typing import List

import boto3
from loguru import logger

from sigrun.commands.base import BaseCommand
from sigrun.commands.discord import CHAT_INPUT_TYPE
from sigrun.model.options import StartServerOptions
from sigrun.model.game import GAMES

session = boto3.Session(profile_name="sigrun")
ec2 = session.resource("ec2")


class StartServer(BaseCommand):
    # name = "start-server"
    options: StartServerOptions

    def __init__(self, game: str, name: str, password: str):
        self.game = GAMES.get(game, "")
        self.name = name
        self.password = password
        if self.game == "":
            raise RuntimeError(
                f"Invalid game {game}. Please select one of {', '.join(GAMES.keys())}."
            )

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
            "options": StartServerOptions.get_discord_metadata(),
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
            UserData="""
#!/bin/bash

sudo add-apt-repository multiverse -y
sudo dpkg --add-architecture i386
sudo apt -q -y update
# sudo apt upgrade -y
echo steam steam/question select "I AGREE" | debconf-set-selections && \
    echo steam steam/license note '' | debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends \
      libatomic1 libpulse-dev libpulse0 steamcmd net-tools ca-certificates gosu
""",
        ).pop()

        instance.create_tags(
            Tags=[
                {
                    "Key": "Name",
                    "Value": self.name,
                }
            ]
        )

        logger.info(f"Started instance {instance} with name {self.name}")

    @staticmethod
    def is_deferred() -> bool:
        False

    def get_instance(self, name: str):
        # Check if an instance with the given name already exists
        instances = ec2.instances.filter(
            Filters=[{"Name": "tag:Name", "Values": [name]}]
        )

        for instance in instances:
            if instance.state["Name"] != "terminated":
                logger.warn(
                    f"An instance with the name '{name}' already exists (ID: {instance.id})."
                )
                return instance.id
