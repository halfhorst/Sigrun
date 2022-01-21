from aws_cdk import (
    core as cdk,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr_assets as ecr_assets,
    aws_logs as logs
)

from pathlib import Path

DATA_MOUNT_ROOT = "/server_data"
VALHEIM_GAME_PORT = 2456

class GameServerConstruct(cdk.Construct):

    def __init__(self, scope: cdk.Construct, construct_id: str, vpc, file_system, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cluster = ecs.Cluster(self, "GameServerCluster", vpc=vpc, cluster_name="GameServerCluster")

        server_volume = ecs.Volume(name="GameServerVolume",
                                   efs_volume_configuration=ecs.EfsVolumeConfiguration(file_system_id=file_system.file_system_id))
        mount_point = ecs.MountPoint(container_path="/server_data",
                                     source_volume=server_volume.name,
                                     read_only=False)

        valheim_task = self.get_valheim_task(server_volume, mount_point)

        service_security_group = ec2.SecurityGroup(self, "GameServerSecurityGroup", vpc=vpc, security_group_name="GameServerSecurityGroup")

        service = ecs.FargateService(self, 
                                     "GameServerFargateService",
                                     cluster=cluster,
                                     task_definition=valheim_task,
                                     desired_count=0,
                                     platform_version=ecs.FargatePlatformVersion.VERSION1_4,
                                     security_groups=[service_security_group],
                                     capacity_provider_strategies=[
                                        ecs.CapacityProviderStrategy(capacity_provider="FARGATE_SPOT", weight=2),
                                        ecs.CapacityProviderStrategy(capacity_provider="FARGATE", weight=1)
                                     ])

        file_system.connections.allow_default_port_from(service)
        self.allow_valheim_connections(service)

    def get_valheim_task(self, server_volume: ecs.Volume, mount_point: ecs.MountPoint) -> ecs.FargateTaskDefinition:
        valheim_image = ecr_assets.DockerImageAsset(self, 
                                                    "ValheimImage", 
                                                    directory=str(Path(__file__).resolve().parents[0]), 
                                                    file="ValheimDockerfile")

        valheim_task = ecs.FargateTaskDefinition(self, 
                                                 "ValheimTask", 
                                                 cpu=2048,
                                                 memory_limit_mib=4096,
                                                 volumes=[server_volume],
                                                 family="Valheim")

        valheim_container_definition = valheim_task.add_container(
            "ValheimContainer",
            container_name="ValheimContainer",
            image=ecs.ContainerImage.from_docker_image_asset(valheim_image),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="valheim_server_logs",
                                            log_retention=logs.RetentionDays.TWO_WEEKS),
            environment={"DATA_MOUNT_ROOT": DATA_MOUNT_ROOT,
                         "VALHEIM_GAME_PORT": str(VALHEIM_GAME_PORT)})

        valheim_container_definition.add_mount_points(mount_point)

        return valheim_task

    def allow_valheim_connections(self, service: ecs.FargateService) -> None: 
        service.connections.allow_from_any_ipv4(ec2.Port(protocol=ecs.Protocol.UDP, 
                                                         from_port=VALHEIM_GAME_PORT,
                                                         to_port=VALHEIM_GAME_PORT + 1,  # Steam query port
                                                         string_representation="valheimUdpPorts"))
