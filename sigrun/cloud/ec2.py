from sigrun.cloud.session import ec2_resource


def get_non_termianted_instance(game: str, server: str):
    tag = get_tag_name(game, server)
    instances = ec2_resource.instances.filter(
        Filters=[{"Name": "tag:Name", "Values": [tag]}]
    )
    for instance in instances:
        if instance.state["Name"] != "terminated":
            return instance
    return None


def get_tag_name(game: str, server: str):
    return f"{game}-{server}"
