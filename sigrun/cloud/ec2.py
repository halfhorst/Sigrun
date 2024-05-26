from typing import List

from sigrun.cloud.session import ec2_resource


def get_non_terminated_instances(
    game: str = "", server_name: str = "", password: str = ""
) -> List:

    filters = []
    if game:
        filters.append({"Name": "tag:game", "Values": [game]})
    if server_name:
        filters.append({"Name": "tag:server_name", "Values": [server_name]})
    if password:
        filters.append({"Name": "tag:Password", "Values": [password]})

    instances = ec2_resource.instances.filter(Filters=filters)
    return [i for i in instances if i.state["Name"] != "terminated"]


def get_instance_by_id(instance_id: str):
    instances = ec2_resource.instances.filter(InstanceIds=[instance_id])
    return [i for i in instances if i.state["Name"] != "terminated"]
