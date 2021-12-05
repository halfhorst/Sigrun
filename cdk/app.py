from aws_cdk import (
    core as cdk,
    aws_ec2 as ec2,
    aws_efs as efs
)
from game_server_construct import GameServerConstruct
from sigrun_construct import SigrunConstruct


class SigrunAppStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, 
                      "GameServerVpc",
                      cidr="10.0.0.0/16", 
                      max_azs=1,
                      subnet_configuration=[ec2.SubnetConfiguration(cidr_mask=24,
                                                                    name="GameServerPublicSubnet",
                                                                    subnet_type=ec2.SubnetType.PUBLIC)])

        file_system_security_group = ec2.SecurityGroup(self, "FileSystemSecurityGroup", vpc=vpc,
                                                       security_group_name="FileSystemSecurityGroup",
                                                       allow_all_outbound=False)
        file_system = efs.FileSystem(self, "GameServerFileSystem", vpc=vpc, 
                                     enable_automatic_backups=True, security_group=file_system_security_group)
        
        GameServerConstruct(self, "GameServerConstruct", vpc, file_system)
        SigrunConstruct(self, "SigrunConstruct", vpc, file_system)

app = cdk.App()
SigrunAppStack(app, "SigrunAppStack")
app.synth()
