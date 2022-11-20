import pprint

from boto3.dynamodb.conditions import Key
from loguru import logger

from sigrun.cloud.util import CloudUtility
from sigrun.commands.base import BaseCommand
from sigrun.model.container import ContainerTag
from sigrun.model.game import VALHEIM

CHAT_INPUT_TYPE = 1


class ServerStatus(BaseCommand):
    name = "server-status"

    def __init__(self):
        self.game = VALHEIM

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": "server-status",
            "description": "List server status and details for all existing Valheim worlds.",
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

        tasks = cloud_utility.get_tasks()
        for task in tasks:
            tags = {tag["key"]: tag["value"] for tag in task["tags"]}
            public_ip = ""
            for attachment in task["attachments"]:
                if attachment["type"] == "ElasticNetworkInterface":
                    for detail in attachment["details"]:
                        if detail["name"] == "networkInterfaceId":
                            eni_id = detail["value"]
                            public_ip = cloud_utility.get_public_ip(eni_id)
            database_server_data[tags[ContainerTag.SERVER]].update({
                'publicIp': public_ip,
                'status': task['lastStatus']
            })

        return self.format_server_data(database_server_data)

    @staticmethod
    def format_server_data(data: dict) -> str:
        return pprint.pformat(data)

    def is_deferred(self) -> bool:
        return False

    def deferred_handler(self, discord_token: str) -> str:
        pass
