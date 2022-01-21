import time
from decimal import Decimal
from datetime import date
from typing import List, Dict

import boto3
from boto3.dynamodb.conditions import Key
from loguru import logger

CHAT_INPUT_TYPE = 1
STRING_OPTION_TYPE = 3

# Cryptic validation note:
# Lambda EFS mount requires path begin with /mnt.
SERVER_DATA_ROOT = "/mnt/server_data"
VALHEIM_TASK_FAMILY = "Valheim"
DYNAMO_DB_TABLE = "GameServerTable"

class SigrunCommand:
    """Base class for a Sigrun command. Supports querying for relevant AWS constructs."""

    ecs_client = boto3.client("ecs")
    ec2_client = boto3.client('ec2')
    ddb_resource = boto3.resource('dynamodb')

    @classmethod
    def get_metadata(cls):
        """Get command metadata for registering the command
        with Discord."""
        raise NotImplementedError
    
    @classmethod
    def handler(cls, options: list):
        """The handler for the command when it is invoked."""
        raise NotImplementedError

    @classmethod
    def get_option(cls, name: str, options: list):
        """Retrieve a named option from the options list."""
        return [o for o in options if o["name"] == name][0]["value"]

    @classmethod
    def get_vpc(cls) -> str:
        vpcs = cls.ec2_client.describe_vpcs(Filters=[{"Name": "tag:Name", "Values": ["SigrunAppStack/GameServerVpc"]}])
        if vpcs["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError(f"Failed to successfully query for vpc data.")
        elif len(vpcs["Vpcs"]) != 1:
            raise RuntimeError("Didn't find exactly one VPC. This is unexpected")

        return vpcs["Vpcs"][0]["VpcId"]

    @classmethod
    def get_subnet_id(cls, vpc_id: str) -> str:
        subnets = cls.ec2_client.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
        if subnets['ResponseMetadata']["HTTPStatusCode"] != 200:
            raise RuntimeError(f"Failed to successfully query for subnet data.")
        elif len(subnets["Subnets"]) != 1:
            raise RuntimeError(f"Didn't find exactly one subnet. This is unexpected.")

        return subnets["Subnets"][0]["SubnetId"]

    @classmethod
    def get_security_group_ids(cls, vpc_id: str) -> List[str]:
        security_groups = cls.ec2_client.describe_security_groups(Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {"Name": "group-name", "Values": ["FileSystemSecurityGroup", "GameServerSecurityGroup"]}])

        if security_groups["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Failed to successfully query for security group data.")
        elif len(security_groups["SecurityGroups"]) != 2:
            raise RuntimeError("Didn't find exactly two security groups. This is unexpected.")

        return [sg["GroupId"] for sg in security_groups["SecurityGroups"]]
    
    @classmethod
    def get_tasks(cls) -> List:
        tasks = cls.ecs_client.list_tasks(cluster="GameServerCluster")
        if tasks["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Failed to query for list of tasks.")
        
        if len(tasks["taskArns"]) == 0:
            return []

        task_descriptions = cls.ecs_client.describe_tasks(cluster="GameServerCluster", 
                                            tasks=tasks["taskArns"], include=["TAGS"] )
        if task_descriptions["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Failed to query for task descriptions.")

        return task_descriptions["tasks"]

    @classmethod
    def get_public_ip(cls, elastic_network_interface_id: str) -> str:
        eni = boto3.resource('ec2').NetworkInterface(elastic_network_interface_id)

        return eni.association_attribute['PublicIp']


class ServerStatus(SigrunCommand):

    name = "server-status"

    @classmethod
    def get_description(cls):
        return "List server status and details for all existing Valheim worlds."

    @classmethod
    def get_metadata(cls):
        return {
            "name": cls.name,
            "description": cls.get_description(),
            "default_permission": True,
            "type": CHAT_INPUT_TYPE
        }

    @classmethod
    def handler(cls, options: list):
        table = cls.ddb_resource.Table(DYNAMO_DB_TABLE)

        world_records = table.query(
            KeyConditionExpression=Key("game").eq("Valheim")
        )
        if world_records["ResponseMetadata"]['HTTPStatusCode'] != 200:
            logger.error("Failed to query DynamoDb")

        if "Items" not in world_records:
            world_records = {}
        else:
            world_records = {record["worldName"]: record for record in world_records["Items"]}

        # TODO: Get more granular start time?
        tasks = cls.get_tasks()
        running_world_data = {}
        for task in tasks:
            tags = {tag["key"]: tag["value"] for tag in task["tags"]}
            world = tags["sigrun-world"]
            eni_id = None
            for attachment in task["attachments"]:
                if attachment["type"] == "ElasticNetworkInterface":
                    for detail in attachment["details"]:
                        if detail["name"] == "networkInterfaceId":
                            eni_id = detail["value"]
            running_world_data[world] = {"publicIp": cls.get_public_ip(eni_id), "status": task["lastStatus"]}

        for world, data in world_records.items():
            data.update(running_world_data.get(world, {"publicIp": None}))

        # TODO: Update the records so they are eventually consistent w.r.t state? do I care?

        message = cls.format_world_info(world_records.values()) if len(world_records) > 0 else "No worlds currently exist."
        logger.info(message)
        return {"content": message}

    @staticmethod
    def format_world_info(worlds: List):
        def _formatter(data: Dict):
            return (f"World: [{data['worldName']}] "
                    f"Server name: [{data['serverName']}] "
                    f"Password: [{data['serverPassword']}] "
                    f"Status: [{data['status']}] "
                    f"Public IP: [{data['publicIp']}] ")
        return "\n".join([_formatter(data) for data in worlds])


class StartServer(SigrunCommand):

    name = "start-server"
    world_name_option = "world-name"
    server_name_option = "server-name"
    server_pass_option = "server-password"

    @classmethod
    def get_description(cls):
        return "Start Valheim server SERVER_NAME. The world will be created if it doesn't exist."

    @classmethod
    def get_metadata(cls):
        return {
            "name": cls.name,
            "description": cls.get_description(),
            "options": [
                {
                    "type": STRING_OPTION_TYPE,
                    "name": cls.world_name_option,
                    "description": "The name of the world to start.",
                    "required": True,
                },
                {
                    "type": STRING_OPTION_TYPE,
                    "name": cls.server_name_option,
                    "description": "The name of the server. This name will show up in Valheim's server list. ",
                    "required": True,
                },
                {
                    "type": STRING_OPTION_TYPE,
                    "name": cls.server_pass_option,
                    "description": "The server password.",
                    "required": True
                }
            ],
            "default_permission": True,
            "type": CHAT_INPUT_TYPE
        }

    @classmethod
    def handler(cls, options: list):
        world = cls.get_option(cls.world_name_option, options)
        server = cls.get_option(cls.server_name_option, options)
        password = cls.get_option(cls.server_pass_option, options)

        if len(password) <= 3:
            message = "Password must be longer than 3 characters to appease Odin."
            logger.error(message) 
            return {"content": message}

        vpc_id = cls.get_vpc()
        subnet_id = cls.get_subnet_id(vpc_id)
        security_group_ids = cls.get_security_group_ids(vpc_id)

        tasks = cls.get_tasks()
        for task in tasks:
            tags = {tag["key"]: tag["value"] for tag in task["tags"]}
            if tags["sigrun-world"] == world:
                message = f"The world {world} is already up and running! be patient."
                logger.warning(message)
                return {"content": message}

        task = cls.ecs_client.run_task(
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
                            {
                                "name": "VALHEIM_WORLD_NAME",
                                "value": world
                            }
                        ]
                    }
                ]
            },
            tags=[
                {
                    "key": "sigrun-game",
                    "value": "valheim"
                },
                {
                    "key": "sigrun-world",
                    "value": world
                },
                {
                    "key": "sigrun-server-name",
                    "value": server
                },
                {
                    "key": "sigrun-server-password",
                    "value": password
                }
            ],
            taskDefinition="Valheim")
        if task["ResponseMetadata"]["HTTPStatusCode"] != 200:
            message = "Failed to initiate Fargate task."
            logger.error(message)
            return {"content": message}

        table = cls.ddb_resource.Table(DYNAMO_DB_TABLE)

        world_record = table.get_item(
            Key={
                "game": "Valheim",
                "worldName": world
            }
        )
        if world_record["ResponseMetadata"]['HTTPStatusCode'] != 200:
            message = "Fargate task initiated, but failed to record in DynamoDb"
            logger.error(message)
            return {"content": message}

        if "Item" in world_record:
            table.update_item(
                Key={
                    "game": "Valheim",
                    "worldName": world
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

            message = f"Starting up existing world {world}. Server name: {server}. Password: {password}."
        else:
            table.put_item(
                Item={
                    "game": "Valheim",
                    "worldName": world,
                    "serverName": server,
                    "serverPassword": password,
                    "status": "INITIATED",
                    "creationTime": str(date.today()),
                    "totalUptime": 0,
                    "totalSessions": 0,
                    "uptimeStart": Decimal(time.time()),
                    "lastStarted": str(date.today())
                })
            message = f"Creating a new world named {world}. Server name: {server}. Password: {password}."

        logger.info(message)
        return {"content": message}


class StopServer(SigrunCommand):

    name = "stop-server"
    world_name_option = "world-name"

    @classmethod
    def get_description(cls):
        return "Stop the server running the Valheim world WORLD_NAME."

    @classmethod
    def get_metadata(cls):
        return {
            "name": cls.name,
            "description": cls.get_description(),
            "options": [{
                "type": STRING_OPTION_TYPE,
                "name": cls.world_name_option,
                "description": "The name of the world to stop. Check world-status to see what is currently up.",
                "required": True,
            }],
            "default_permission": True,
            "type": CHAT_INPUT_TYPE
        }

    @classmethod
    def handler(cls, options: list):
        world = cls.get_option(cls.world_name_option, options)

        ecs_client = boto3.client("ecs")

        task_descriptions = cls.get_tasks()

        task_to_stop = None
        for task in task_descriptions:
            for tag in task["tags"]:
                if tag["key"] == "sigrun-world" and tag["value"] == world:
                    task_to_stop = task

        if task_to_stop is None:
            message = f"No running world named {world} found."
            logger.info(message)
            return {"content": message}

        stopped_task = ecs_client.stop_task(cluster="GameServerCluster", task=task_to_stop["taskArn"], reason="Sigrun request.")
        if stopped_task["ResponseMetadata"]["HTTPStatusCode"] != 200:
            message = "Failed to stop Fargate task."
            logger.error(message)
            return {"content": message}

        table = cls.ddb_resource.Table(DYNAMO_DB_TABLE)

        world_record = table.get_item(
            Key={
                "game": "Valheim",
                "worldName": world
            }
        )
        if world_record["ResponseMetadata"]['HTTPStatusCode'] != 200:
            message = "Fargate task stopped, but failed to update DynamoDB record."
            logger.error(message)
            return {"content": message}

        if "Item" not in world_record:
            message = "Failed to get DynamoDB record for an existing world. Most unexpected!"
            logger.error(message)
            return {"content": message}

        table.update_item(
            Key={
                "game": "Valheim",
                "worldName": world
            },
            AttributeUpdates={
                "totalUptime": {
                    "Value": Decimal(time.time()) - world_record['Item']["uptimeStart"],
                    "Action": "ADD"
                },
                "serverName": {
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

        message = f"Stopped world {world}."
        logger.info(message)
        return {"content": message}


class RiseAndGrind(SigrunCommand):

    name = "rise-and-grind"
    world_name_option = "world-name"
    server_name_option = "server-name"
    server_pass_option = "server-password"

    @classmethod
    def get_description(cls):
        return "A synonym of start-server..."

    @classmethod
    def get_metadata(cls):
        return {
            "name": cls.name,
            "description": cls.get_description(),
            "options": [
                {
                    "type": STRING_OPTION_TYPE,
                    "name": cls.world_name_option,
                    "description": "The name of the world to start.",
                    "required": True,
                },
                {
                    "type": STRING_OPTION_TYPE,
                    "name": cls.server_name_option,
                    "description": "The name of the server. This name will show up in Valheim's server list. ",
                    "required": True,
                },
                {
                    "type": STRING_OPTION_TYPE,
                    "name": cls.server_pass_option,
                    "description": "The server password.",
                    "required": True
                }
            ],
            "default_permission": True,
            "type": CHAT_INPUT_TYPE
        }

    @classmethod
    def handler(cls, options: List):
        return StartServer.handler(options)
