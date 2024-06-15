from aws_cdk import App, Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct
from sigrun_construct import SigrunConstruct


class SigrunAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self,
            "GameServerVpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name="GameServerPublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                )
            ],
        )

        SigrunConstruct(self, "SigrunConstruct")


app = App()
SigrunAppStack(app, "SigrunAppStack")
app.synth()
