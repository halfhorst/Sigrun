import time
from decimal import Decimal
from datetime import date
from typing import Tuple

from loguru import logger

from sigrun.commands.base import BaseCommand
from sigrun.cloud.util import CloudUtility
from sigrun.model.container import ContainerTag
from sigrun.model.game import Game, VALHEIM
from sigrun.model.options import StartServerOptions

CHAT_INPUT_TYPE = 1


class StartServer(BaseCommand):
    name = "start-server"
    options: StartServerOptions

    def __init__(self, options: dict):
        self.options = StartServerOptions.from_dict(options)
        self.game = VALHEIM

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": "start-server",
            "description": "Start a game server with server name as seed. "
                           "Will create if one doesn't currently exist.",
            "default_permission": True,
            "options": StartServerOptions.get_discord_metadata()
        }

    def handler(self) -> str:
        server_name = self.options.server_name.get()
        password = self.options.server_password.get()

        is_failed, response = self.validate_input(server_name, password)
        if is_failed:
            return response

        cloud_data = CloudUtility(self.game)
        if self.is_running(cloud_data, self.game, server_name):
            message = f"The {self.game} server {server_name} has already been initiated!"
            logger.warning(message)
            return message

        return (f"Initiating server [{server_name}] for {self.game}. The password will be [{password}]."
                f"I\"ll tell you when it is ready.")

    def is_deferred(self) -> bool:
        return True

    def deferred_handler(self, discord_token: str) -> str:
        server_name = self.options.server_name.get()
        password = self.options.server_password.get()
        game = VALHEIM

        response_code = self.launch_task(game, server_name, password)
        if response_code != 200:
            message = f"Failed to initiate Fargate task: {response_code}"
            logger.error(message)
            return message

        return self.record_result(game, server_name, password)

    @staticmethod
    def validate_input(server_name: str, password: str) -> Tuple[bool, str]:
        if len(password) <= 5:
            message = "Passwords must be longer than 3 characters."
            logger.error(message)
            return True, message

        if len(server_name) < 2:
            message = "Server names should be longer than 2 characters."
            logger.error(message)
            return True, message
        return False, ""

    @staticmethod
    def is_running(cloud_utility: CloudUtility, game: Game, server: str):
        tasks = cloud_utility.get_tasks()
        for task in tasks:
            tags = {tag["key"]: tag["value"] for tag in task["tags"]}
            if (tags[ContainerTag.GAME.tag] == str(game)
                    and tags[ContainerTag.SERVER.tag] == server):
                return True
        return False

    @staticmethod
    def launch_task(game: Game, server: str, password: str) -> int:
        cloud_utility = CloudUtility(game)
        vpc_id = cloud_utility.get_vpc_id()
        subnet_id = cloud_utility.get_subnet_id(vpc_id)
        security_group_ids = cloud_utility.get_security_group_ids(vpc_id)

        task = CloudUtility.ecs_client.run_task(
            cluster="GameServerCluster",
            launchType="FARGATE",
            count=1,
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": [subnet_id],
                    "securityGroups": security_group_ids,
                    "assignPublicIp": "ENABLED"
                }
            },
            overrides={
                "containerOverrides": [
                    {
                        "name": "ValheimContainer",
                        "environment": [
                            {
                                "name": "VALHEIM_SERVER_NAME",
                                "value": server
                            },
                            {
                                "name": "VALHEIM_SERVER_PASSWORD",
                                "value": password
                            },
                        ]
                    }
                ]
            },
            tags=[
                {
                    "key": ContainerTag.GAME.tag,
                    "value": str(game)
                },
                {
                    "key": ContainerTag.SERVER.tag,
                    "value": server
                },
                {
                    "key": ContainerTag.PASSWORD.tag,
                    "value": password
                }
            ],
            taskDefinition=game.task_definition)

        return task["ResponseMetadata"]["HTTPStatusCode"]

    def record_result(self, game: Game, server: str, password: str) -> str:
        cloud_utility = CloudUtility(game)
        table = cloud_utility.get_table_resource()

        world_record = table.get_item(Key={"game": str(game), "serverName": server})
        if world_record["ResponseMetadata"]['HTTPStatusCode'] != 200:
            message = "Fargate task initiated but failed to record metadata in the database"
            logger.error(message)
            return message

        if "Item" in world_record:
            return self.update_item(table, game, server, password)
        else:
            return self.create_item(table, game, server, password)

    @staticmethod
    def update_item(table, game: Game, server: str, password: str) -> str:
        table.update_item(
            Key={
                "game": str(game),
                "serverName": server
            },
            AttributeUpdates={
                "lastStarted": {
                    "Value": str(date.today()),
                    "Action": "PUT"
                },
                "serverName": {
                    "Value": server,
                    "Action": "PUT"
                },
                "serverPassword": {
                    "Value": password,
                    "Action": "PUT"
                },
                "status": {
                    "Value": "INITIATED",
                    "Action": "PUT"
                },
                "uptimeStart": {
                    "Value": Decimal(time.time()),
                    "Action": "PUT"
                },
                "totalSessions": {
                    "Value": 1,
                    "Action": "ADD"
                }
            })

        message = f"Starting up existing {game} server [{server}] with password [{password}]."
        logger.info(message)
        return message

    @staticmethod
    def create_item(table, game: Game, server: str, password: str) -> str:
        table.put_item(
            Item={
                "game": str(game),
                "serverName": server,
                "serverPassword": password,
                "status": "INITIATED",
                "creationTime": str(date.today()),
                "totalUptime": 0,
                "totalSessions": 0,
                "uptimeStart": Decimal(time.time()),
                "lastStarted": str(date.today())
            })
        message = f"Creating a new {game} server {server} with password [{password}]."
        logger.info(message)
        return message
