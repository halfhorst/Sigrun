import time
from decimal import Decimal

from loguru import logger

from sigrun.cloud.util import CloudUtility
from sigrun.commands.base import BaseCommand
from sigrun.model.container import ContainerTag
from sigrun.model.game import VALHEIM
from sigrun.model.options import StopServerOptions

CHAT_INPUT_TYPE = 1


class StopServer(BaseCommand):
    name = "stop-server"
    world_name_option = "world-name"

    def __init__(self, options: dict):
        self.options = StopServerOptions.from_dict(options)
        self.game = VALHEIM

    @staticmethod
    def get_discord_metadata():
        return {
            "type": CHAT_INPUT_TYPE,
            "name": "stop-server",
            "description": "Stop a game server.",
            "default_permission": True,
            "options": StopServerOptions.get_discord_metadata(),
        }

    def handler(self) -> str:
        server_name = self.options.server_name.get()

        cloud_utility = CloudUtility(self.game)
        tasks = cloud_utility.get_tasks()

        task_to_stop = None
        for task in tasks:
            tags = {tag["key"]: tag["value"] for tag in task["tags"]}
            task_server = tags.get(ContainerTag.SERVER.tag, "")
            if task_server == server_name:
                task_to_stop = task

        if task_to_stop is None:
            message = f"No running {self.game} server named {server_name} found."
            logger.info(message)
            return message

        stopped_task = cloud_utility.stop_task(task_to_stop['taskArn'])
        if stopped_task["ResponseMetadata"]["HTTPStatusCode"] != 200:
            message = "Failed to stop Fargate task!"
            logger.error(message)
            return message

        table = cloud_utility.get_table_resource()
        server_database_data = table.get_item(Key={"game": str(self.game), "serverName": server_name})
        if server_database_data["ResponseMetadata"]['HTTPStatusCode'] != 200:
            message = "Fargate task stopped, but failed to update DynamoDB record."
            logger.error(message)
            return message

        if "Item" not in server_database_data:
            message = "Failed to get DynamoDB record for an existing world. Most unexpected!"
            logger.error(message)
            return message

        uptime = Decimal(time.time()) - server_database_data['Item']['uptimeStart']
        return self.update_item(table, server_name, uptime)

    def update_item(self, table, server_name: str, uptime: float) -> str:
        table.update_item(
            Key={
                "game": str(self.game),
                "serverName": server_name
            },
            AttributeUpdates={
                "totalUptime": {
                    "Value": uptime,
                    "Action": "ADD"
                },
                "uptimeStart": {
                    "Value": None,
                    "Action": "PUT"
                },
                "serverPassword": {
                    "Value": None,
                    "Action": "PUT"
                },
                "status": {
                    "Value": "STOPPED",
                    "Action": "PUT"
                }
            }
        )

        message = f"Stopped {self.game} server {server_name}."
        logger.info(message)
        return message

    def is_deferred(self) -> bool:
        return False

    def deferred_handler(self, discord_token: str) -> str:
        pass
