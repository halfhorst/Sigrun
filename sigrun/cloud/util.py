from typing import List

import boto3


class CloudUtility:
    ecs_client = boto3.client("ecs")
    ec2_client = boto3.client("ec2")
    ec2_resource = boto3.resource("ec2")
    ddb_resource = boto3.resource("dynamodb")

    DYNAMO_DB_TABLE = "GameServerTable"

    def __init__(self, game):
        self.game = game

    def get_vpc_id(self) -> str:
        vpcs = self.ec2_client.describe_vpcs(
            Filters=[{"Name": "tag:Name", "Values": ["SigrunAppStack/GameServerVpc"]}]
        )
        if vpcs["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Failed to successfully query for vpc data.")
        elif len(vpcs["Vpcs"]) != 1:
            raise RuntimeError("Didn't find exactly one VPC. This is unexpected")

        return vpcs["Vpcs"][0]["VpcId"]

    def get_subnet_id(self, vpc_id: str) -> str:
        subnets = self.ec2_client.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        if subnets["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Failed to successfully query for subnet data.")
        elif len(subnets["Subnets"]) != 1:
            raise RuntimeError("Didn't find exactly one subnet. This is unexpected.")

        return subnets["Subnets"][0]["SubnetId"]

    def get_security_group_ids(self, vpc_id: str) -> List[str]:
        security_groups = self.ec2_client.describe_security_groups(
            Filters=[
                {"Name": "vpc-id", "Values": [vpc_id]},
                {
                    "Name": "group-name",
                    "Values": ["FileSystemSecurityGroup", "GameServerSecurityGroup"],
                },
            ]
        )

        if security_groups["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Failed to successfully query for security group data.")
        elif len(security_groups["SecurityGroups"]) != 2:
            raise RuntimeError(
                "Didn't find exactly two security groups. This is unexpected."
            )

        return [sg["GroupId"] for sg in security_groups["SecurityGroups"]]

    def get_tasks(self) -> List:
        tasks = self.ecs_client.list_tasks(cluster="GameServerCluster")
        if tasks["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Failed to query for list of tasks.")

        if len(tasks["taskArns"]) == 0:
            return []

        task_descriptions = self.ecs_client.describe_tasks(
            cluster="GameServerCluster", tasks=tasks["taskArns"], include=["TAGS"]
        )
        if task_descriptions["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Failed to query for task descriptions.")

        return task_descriptions["tasks"]

    def describe_task(self, task_arn: str) -> dict:
        return self.ecs_client.describe_tasks(
            cluster="GameServerCluster", tasks=[task_arn]
        )

    def get_public_ip(self, elastic_network_interface_id: str) -> str:
        eni = self.ec2_resource.NetworkInterface(elastic_network_interface_id)

        return eni.association_attribute["PublicIp"]

    def get_table_resource(self):
        return self.ddb_resource.Table(self.DYNAMO_DB_TABLE)

    def stop_task(self, task_arn: str):
        return self.ecs_client.stop_task(
            cluster="GameServerCluster", task=task_arn, reason="Sigrun request."
        )
