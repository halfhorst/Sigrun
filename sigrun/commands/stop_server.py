import time
from decimal import Decimal
from typing import List

from loguru import logger

from sigrun.cloud.util import CloudUtility
from sigrun.commands.base import BaseCommand
from sigrun.commands.discord import CHAT_INPUT_TYPE
from sigrun.model.game import VALHEIM
from sigrun.model.options import StopServerOptions


class StopServer(BaseCommand):

    def __init__(self, game: str, instance_name: str):
        self.game = Game(game)
        self.instance_name = instance_name

    @staticmethod
    def get_cli_description():
        return "Stop a game server."

    @staticmethod
    def get_discord_metadata():
        return {
            "type": CHAT_INPUT_TYPE,
            "name": "stop-server",
            "description": StopServer.get_cli_description(),
            "default_permission": True,
            "options": [
                {
                    "type": STRING_OPTION_TYPE,
                    "name": StopServerOptions.server_name.name,
                    "description": "The name of the world to stop. Check world-status to see what is currently up.",
                    "required": True,
                }
            ],
        }

    def handler(self) -> str:
        server_name = self.options.server_name.value
        cloud_utility = CloudUtility(self.game)
        table = cloud_utility.get_table_resource()

        existing_item = table.get_item(
            Key={"game": str(self.game), "serverName": server_name}
        )

        if "Item" not in existing_item:
            message = f"No running {self.game} server named {server_name} found."
            logger.info(message)
            return message

        task_arn = existing_item["Item"]["taskArn"]
        if task_arn == "":
            message = f"No running {self.game} server named {server_name} found."
            logger.info(message)
            return message

        stopped_task = cloud_utility.stop_task(task_arn)
        if stopped_task["ResponseMetadata"]["HTTPStatusCode"] != 200:
            message = "Failed to stop Fargate task!"
            logger.error(message)
            return message

        table = cloud_utility.get_table_resource()
        server_database_data = table.get_item(
            Key={"game": str(self.game), "serverName": server_name}
        )
        if server_database_data["ResponseMetadata"]["HTTPStatusCode"] != 200:
            message = "Fargate task stopped, but failed to update DynamoDB record."
            logger.error(message)
            return message

        if "Item" not in server_database_data:
            message = (
                "Failed to get DynamoDB record for an existing world. Most unexpected!"
            )
            logger.error(message)
            return message

        uptime = Decimal(time.time()) - server_database_data["Item"]["uptimeStart"]
        return self.update_item(table, server_name, uptime)

    def update_item(self, table, server_name: str, uptime: float) -> str:
        table.update_item(
            Key={"game": str(self.game), "serverName": server_name},
            AttributeUpdates={
                "totalUptime": {"Value": uptime, "Action": "ADD"},
                "uptimeStart": {"Value": None, "Action": "PUT"},
                "serverPassword": {"Value": None, "Action": "PUT"},
                "taskArn": {"Value": "", "Action": "PUT"},
                "status": {"Value": "STOPPED", "Action": "PUT"},
                "publicIp": {"Value": "", "Action": "PUT"},
            },
        )

        message = f"Stopped {self.game} server {server_name}."
        logger.info(message)
        return message

    def is_deferred(self) -> bool:
        return False

    def deferred_handler(self) -> str:
        pass
