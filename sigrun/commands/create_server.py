from datetime import datetime, timezone

from loguru import logger

from sigrun.cloud import ec2
from sigrun.cloud.session import ec2_resource
from sigrun.commands.base import Command
from sigrun.exceptions import GameNotFoundError, PasswordTooShortError
from sigrun.model.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE
from sigrun.model.game import Game
from sigrun.model.messenger import get_messenger


class CreateServer(Command):

    def __init__(self, game: str, server_name: str, password: str):
        self.game_name = game
        self.server_name = server_name
        self.password = password

    @staticmethod
    def get_discord_name():
        return "create-server"

    @staticmethod
    def get_cli_description():
        return """Create an instance of a game server. Use it's unique id to start and stop the instance."""

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": CreateServer.get_discord_name(),
            "description": CreateServer.get_cli_description(),
            "default_permission": True,
            "options": [
                {
                    "type": STRING_OPTION_TYPE,
                    "name": "game",
                    "description": "A supported game.",
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

    def handler(self):
        try:
            game = Game(self.game_name)
        except GameNotFoundError:
            logger.error(f"Invalid game name {self.game_name}")
            get_messenger()(f"I'm sorry, I don't support {self.game_name}.")
            return

        instance = ec2.get_non_terminated_instances(game.name, self.server_name)

        if not instance:
            get_messenger()(
                f"Ok, I'll create a {game} server named {self.server_name}."
            )
            self.create_instance(
                game,
                self.server_name,
                self.password,
            )
            return
        instance = instance.pop()

        if instance.state["Name"] == "running":
            get_messenger()(f"The {game} server {self.server_name} is already running!")
            return

        if instance.state["Name"] == "stopped":
            get_messenger()(
                f"I'm restarting {game} server {self.server_name}: {instance}."
            )
            response = instance.start()
            response = instance.create_tags(
                Tags=[
                    {
                        "Key": "start_time",
                        "Value": datetime.now(timezone.utc).isoformat(),
                    },
                ]
            )
            return

        get_messenger()(
            f"I found an existing instance, but it's in an unsupported state: {instance.state['Name'].upper()}. Please try again"
        )

    @staticmethod
    def create_instance(game: Game, server_name: str, password: str):
        if game.name == "valheim" and len(password) < 5:
            get_messenger()(
                f"A Valheim server requires a password at least 5 characters long!"
            )
            raise PasswordTooShortError

        instance = ec2_resource.create_instances(
            BlockDeviceMappings=[
                {
                    # DeviceName needs to match device name in AMI
                    # or will create a second unmounted device
                    "DeviceName": "/dev/sda1",
                    "Ebs": {
                        "DeleteOnTermination": False,
                        "VolumeSize": game.storage,
                        "VolumeType": "gp3",
                    },
                }
            ],
            ImageId="ami-008fe2fc65df48dac",
            InstanceType=game.instance_type,
            MaxCount=1,
            MinCount=1,
            UserData=game.start_script.replace(
                "PYTHON_SERVER_NAME", server_name
            ).replace("PYTHON_PASSWORD", password),
        ).pop()

        response = instance.create_tags(
            Tags=[
                {"Key": "game", "Value": game.name},
                {"Key": "pretty_game", "Value": game.pretty_name},
                {
                    "Key": "server_name",
                    "Value": server_name,
                },
                {"Key": "password", "Value": password},
                {"Key": "start_time", "Value": datetime.now(timezone.utc).isoformat()},
                {"Key": "sigrun", "Value": ""},
                # This will be the instance's visible name in the console
                {"Key": "Name", "Value": f"{game.pretty_name}-{server_name}"},
            ]
        )

        get_messenger()(
            f"{server_name} has been initialized. It's ID is {instance.id}."
        )

    @staticmethod
    def create_security_group(game, server-name, port):
        response = ec2_client.create_security_group(
            GroupName="my-security-group",
            Description="Security group for allowing traffic on port 80",
        )
        security_group_id = response["GroupId"]
        print(f"Security Group Created {security_group_id}")

        # Add an inbound rule to allow traffic on port 80
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 80,
                    "ToPort": 80,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                }
            ],
        )

    def __str__(self):
        return "StartServer"
