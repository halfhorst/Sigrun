from typing import List

from sigrun.cloud.session import ec2_resource


def get_non_terminated_instances(
    game: str = "", server_name: str = "", password: str = ""
) -> List:

    filters = []
    if game:
        filters.append({"Name": "tag:Game", "Values": [game]})
    if server_name:
        filters.append({"Name": "tag:Name", "Values": [server_name]})
    if password:
        filters.append({"Name": "tag:Password", "Values": [password]})

    instances = ec2_resource.instances.filter(Filters=filters)
    return [i for i in instances if i.state["Name"] != "terminated"]


# def get_tag_name(game: str, server: str):
#     return f"{game}-{server}"
