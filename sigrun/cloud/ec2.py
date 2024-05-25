from typing import List

from sigrun.cloud.session import ec2_resource


def get_non_terminated_instance(tag: str = None) -> List:  # game: str, server: str):
    # tag = get_tag_name(game, server)
    if tag:
        filters = [{"Name": "tag:Name", "Values": [tag]}]
    else:
        filters = []

    instances = ec2_resource.instances.filter(Filters=filters)
    # for instance in instances:
    #     if instance.state["Name"] != "terminated":
    #         return instance
    return [i for i in instances if i.state["Name"] != "terminated"]


def get_tag_name(game: str, server: str):
    return f"{game}-{server}"
