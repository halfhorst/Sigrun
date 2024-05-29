from datetime import datetime, timezone

from loguru import logger

from sigrun.cloud import ec2
from sigrun.commands.base import Command
from sigrun.exceptions import GameNotFoundError
from sigrun.model.discord import CHAT_INPUT_TYPE, STRING_OPTION_TYPE
from sigrun.model.game import Game
from sigrun.model.messenger import get_messenger


class ListServers(Command):

    def __init__(self, game: str = ""):
        self.game_name = game

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
        game = None
        if self.game_name:
            try:
                game = Game(self.game_name)
            except GameNotFoundError:
                logger.error(f"Invalid game name {self.game_name}")
                get_messenger()(f"I'm sorry, I don't support {self.game_name}.")
                return

        instances = []
        if game:
            get_messenger()(f"Fetching your {game} servers now!")
            instances = ec2.get_non_terminated_instances(game.name)
        else:
            get_messenger()("Fetching your game servers now!")
            instances = ec2.get_non_terminated_instances()

        if not instances:
            get_messenger()("I don't see any instances... Why don't you create one?")
            return

        get_messenger()("\n" + "\n".join([self.format_instance(i) for i in instances]))

    def format_instance(self, instance) -> str:
        # TODO: monitoring: cpu, mem, connections
        # TODO: monthly cost to date
        # TODO: instance type, storage size
        launch_time = instance.launch_time.strftime("%m/%d/%y %H:%M:%S %Z")
        instance_id = instance.id
        public_ip = instance.public_ip_address
        state = instance.state["Name"].upper()
        tags = {tag["Key"]: tag["Value"] for tag in instance.tags}
        game = tags["pretty_game"]
        server_name = tags["server_name"]
        password = tags["password"]

        descriptors = []
        descriptors.append(f"Server: {server_name}")
        descriptors.append(f"Password: {password}")
        descriptors.append(f"Created: {launch_time}")
        descriptors.append(f"Instance ID: {instance_id}")
        descriptors.append(f"State: {state}")
        if public_ip:
            descriptors.append(f"Public IP: {public_ip}")
        if "start_time" in tags:
            uptime = self.calculate_uptime(datetime.fromisoformat(tags["start_time"]))
            descriptors.append(f"Uptime: {uptime}")

        prefix = "\n... "
        return f"[{game}]" + "".join([prefix + d for d in descriptors])

    @staticmethod
    def calculate_uptime(start_time: datetime) -> str:
        delta = datetime.now(timezone.utc) - start_time
        total_seconds = int(delta.total_seconds())
        days = delta.days
        hours, remainder = divmod(total_seconds - days * 86400, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{days} days, {hours} hours and {minutes} minutes"

    def __str__(self):
        return "ListServers"
