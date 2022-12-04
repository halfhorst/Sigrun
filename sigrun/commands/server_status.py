import pprint
from typing import List

from boto3.dynamodb.conditions import Key
from loguru import logger

from sigrun.cloud.util import CloudUtility
from sigrun.commands.base import BaseCommand
from sigrun.model.game import VALHEIM

CHAT_INPUT_TYPE = 1


class ServerStatus(BaseCommand):
    name = "server-status"

    def __init__(self, options: List[dict]):
        self.game = VALHEIM

    @staticmethod
    def get_cli_description():
        return "List server status and details for all existing Valheim worlds."

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": "server-status",
            "description": ServerStatus.get_cli_description(),
            "default_permission": True,
        }

    def handler(self) -> str:
        cloud_utility = CloudUtility(self.game)
        table = cloud_utility.get_table_resource()

        database_server_data = table.query(KeyConditionExpression=Key("game").eq(str(self.game)))
        if database_server_data["ResponseMetadata"]['HTTPStatusCode'] != 200:
            logger.error(f"Failed to query DynamoDb for {self.game} servers.")

        if "Items" not in database_server_data:
            database_server_data = {}
        else:
            database_server_data = {record["serverName"]: record for record in database_server_data["Items"]}

        for _, data in database_server_data.items():
            data.pop("taskArn")
        return self.format_server_data(database_server_data)

    @staticmethod
    def format_server_data(data: dict) -> str:
        for k, v in data.items():
            v['totalSessions'] = str(v['totalSessions'])
            v['totalUptime'] = str(round(v['totalUptime'] / 3600, 2)) + " hours"
            del v['uptimeStart']
        return pprint.pformat(data)

    def is_deferred(self) -> bool:
        return False

    def deferred_handler(self) -> str:
        pass
