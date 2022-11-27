import time
from decimal import Decimal
from datetime import date
from typing import List, Tuple, Dict

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

    def __init__(self, options: List[dict]):
        self.options = StartServerOptions.from_dict(options)
        self.game = VALHEIM

    @staticmethod
    def get_cli_description():
        return "Start a game server with server name as seed. Will create if one doesn't currently exist."

    @staticmethod
    def get_discord_metadata() -> dict:
        return {
            "type": CHAT_INPUT_TYPE,
            "name": "start-server",
            "description": StartServer.get_cli_description(),
            "default_permission": True,
            "options": StartServerOptions.get_discord_metadata()
        }

    def handler(self) -> str:
        server_name = self.options.server_name.value
        password = self.options.server_password.value

        is_failed, response = self.validate_input(server_name, password)
        if is_failed:
            return response

        cloud_utility = CloudUtility(self.game)
        if self.is_running(cloud_utility, self.game, server_name):
            message = f"The {self.game} server {server_name} has already been initiated!"
            logger.warning(message)
            return message

        return (f"Initiating {self.game} server [{server_name}] with password [{password}]. "
                f"I'll tell you when it is ready.")

    def is_deferred(self) -> bool:
        return True

    def deferred_handler(self) -> str:
        server_name = self.options.server_name.value
        password = self.options.server_password.value
        game = VALHEIM

        cloud_utility = CloudUtility(game)
        table = cloud_utility.get_table_resource()

        if self.is_running(cloud_utility, self.game, server_name):
            return f"Unable to start {self.game} server {server_name}."

        task_metadata = self.launch_task(game, server_name, password, cloud_utility)
        http_status = task_metadata["ResponseMetadata"]["HTTPStatusCode"]
        if http_status != 200:
            message = f"Failed to initiate Fargate task: {http_status}"
            logger.error(message)
            return message

        task_arn = task_metadata["tasks"][0]["taskArn"]
        task_status = task_metadata["tasks"][0]["lastStatus"]
        self.record_initialization(table, game, server_name, password, task_status, task_arn)
        while task_status != "RUNNING" and task_status != "STOPPED":
            new_status = self.get_task_status(task_arn, cloud_utility)
            if new_status != task_status:
                logger.info(f"{str(game)} server {server_name} status changed: {task_status} to {new_status}.")
                task_status = new_status
                self.put_item_attribute(table, game, server_name, {"attribute": "status", "value": task_status})
            time.sleep(5)

        if task_status == "RUNNING":
            ip_address = self.get_task_ip(task_arn, cloud_utility)
            self.put_item_attribute(table, game, server_name, {"attribute": "PublicIp", "value": ip_address})
            return (f"Your {game} server {server_name} is now up and running! "
                    f"The password is {password} and the IP address is {ip_address}.")
        return f"Your {game} server {server_name} could not be started, sorry :(."

    @staticmethod
    def validate_input(server_name: str, password: str) -> Tuple[bool, str]:
        if len(password) <= 5:
            message = "Passwords must be longer than 3 characters."
            logger.error(message)
            return True, message

        if len(server_name) < 2:
            message = "Server names must be longer than 2 characters."
            logger.error(message)
            return True, message
        return False, ""

    @staticmethod
    def is_running(cloud_utility: CloudUtility, game: Game, server: str) -> bool:
        # TODO: Query for ARN and get status
        table = cloud_utility.get_table_resource()
        existing_item = table.get_item(Key={
                "game": str(game),
                "serverName": server
        })

        if 'Item' not in existing_item:
            return False

        task_arn = existing_item['Item']['taskArn']
        if task_arn == "":
            return False

        return StartServer.get_task_status(task_arn, cloud_utility) != "STOPPED"

    @staticmethod
    def get_task_status(task_arn: str, cloud_utility: CloudUtility) -> str:
        task = cloud_utility.describe_task(task_arn)

        if len(task['tasks']) == 0:
            raise RuntimeError(f"Unable to find Fargate task {task_arn} that is expected to be available.")

        return task['tasks'][0]['lastStatus']

    @staticmethod
    def get_task_ip(task_arn: str, cloud_utility: CloudUtility) -> str:
        task = cloud_utility.describe_task(task_arn)
        public_ip = ""
        for attachment in task['tasks'][0]["attachments"]:
            if attachment["type"] == "ElasticNetworkInterface":
                for detail in attachment["details"]:
                    if detail["name"] == "networkInterfaceId":
                        eni_id = detail["value"]
                        public_ip = cloud_utility.get_public_ip(eni_id)
        return public_ip

    @staticmethod
    def launch_task(game: Game, server: str, password: str, cloud_utility: CloudUtility):
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

        return task

    def record_initialization(self, table, game: Game, server: str, password: str, task_status: str, task_arn: str):
        server_data = table.get_item(Key={"game": str(game), "serverName": server})
        if server_data["ResponseMetadata"]['HTTPStatusCode'] != 200:
            message = "Fargate task initiated but failed to record metadata in the database"
            logger.error(message)
            return message

        if "Item" in server_data:
            message = f"Starting up existing {game} server [{server}] with password [{password}]."
            self.update_server_initiated(table, game, server, password, task_status, task_arn)
        else:
            message = f"Creating a new {game} server {server} with password [{password}]."
            self.create_server(table, game, server, password, task_status, task_arn)

        # TODO: check put/update response as well
        logger.info(message)

    @staticmethod
    def update_server_initiated(table, game: Game, server: str, password: str, task_status: str, task_arn: str):
        key = {
                "game": str(game),
                "serverName": server
            }
        attributes = {
                "lastStarted": {
                    "Value": str(date.today()),
                    "Action": "PUT"
                },
                "serverPassword": {
                    "Value": password,
                    "Action": "PUT"
                },
                "taskArn": {
                    "Value": task_arn,
                    "Action": "PUT",
                },
                "status": {
                    "Value": task_status,
                    "Action": "PUT"
                },
                "publicIp": {
                    "Value": "",
                    "Action": "PUT"
                },
                "uptimeStart": {
                    "Value": Decimal(time.time()),
                    "Action": "PUT"
                },
                "totalSessions": {
                    "Value": 1,
                    "Action": "ADD"
                },
            }
        table.update_item(
            Key=key,
            AttributeUpdates=attributes)
        logger.info(f"Updating existing database key {key} with {attributes}.")

    @staticmethod
    def put_item_attribute(table, game: str, server: str, attribute: Dict[str, str]):
        key = {
            "game": str(game),
            "serverName": server
        }
        attributes = {
            attribute["attribute"]: {
                "Value": attribute["value"],
                "Action": "PUT"
            }
        }

        table.update_item(
            Key=key,
            AttributeUpdates=attributes)
        logger.info(f"Updating existing database key {key} with {attributes}.")

    @staticmethod
    def create_server(table, game: Game, server: str, password: str, task_status: str, task_arn: str):
        item = {
                "game": str(game),
                "serverName": server,
                "serverPassword": password,
                "status": task_status,
                "publicIp": "",
                "taskArn": task_arn,
                "creationTime": str(date.today()),
                "totalUptime": 0,
                "totalSessions": 0,
                "uptimeStart": Decimal(time.time()),
                "lastStarted": str(date.today())
        }
        table.put_item(Item=item)
        logger.info(f"Putting new item in database {item}.")
