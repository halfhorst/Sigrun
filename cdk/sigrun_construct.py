from pathlib import Path

from constructs import Construct
from aws_cdk import Duration
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_apigatewayv2_alpha as apigateway
from aws_cdk import aws_apigatewayv2_integrations_alpha as apigateway_integrations
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_lambda_event_sources as LambdaEventSources
from aws_cdk import aws_iam as iam

import sigrun


class SigrunConstruct(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        table = dynamodb.Table(
            self,
            "GameServerTable",
            table_name="GameServerTable",
            partition_key=dynamodb.Attribute(name="game", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="serverName", type=dynamodb.AttributeType.STRING))

        self.discord_handler = lambda_.Function(self, "DiscordLambdaHandler",
                                                runtime=lambda_.Runtime.PYTHON_3_8,
                                                code=lambda_.Code.from_asset(
                                                    str(Path(sigrun.__file__).resolve().parents[1] / "sigrun.zip")),
                                                handler="discord.main",
                                                timeout=Duration.seconds(15),
                                                log_retention=logs.RetentionDays.TWO_WEEKS)

        lambda_integration = apigateway_integrations.HttpLambdaIntegration("HttpLambdaIntegration",
                                                                           handler=self.discord_handler)
        http_api = apigateway.HttpApi(self, "SigrunHttpApi")

        http_api.add_routes(
            path="/",
            methods=[apigateway.HttpMethod.ANY],
            integration=lambda_integration)

        queue = sqs.Queue(self, "SigrunMessageQueue", queue_name="SigrunMessageQueue")
        queue.grant_send_messages(self.discord_handler.role)
        self.queue_handler = lambda_.Function(self, "SqsLambdaHandler",
                                              runtime=lambda_.Runtime.PYTHON_3_8,
                                              code=lambda_.Code.from_asset(
                                                  str(Path(sigrun.__file__).resolve().parents[1] / "sigrun.zip")),
                                              handler="sqs.main",
                                              timeout=Duration.minutes(5),
                                              log_retention=logs.RetentionDays.TWO_WEEKS)

        event_source = LambdaEventSources.SqsEventSource(queue)
        self.queue_handler.add_event_source(event_source)

        table.grant_read_write_data(self.discord_handler.role)
        table.grant_read_write_data(self.queue_handler.role)

        describe_vpc_policy_statement = iam.PolicyStatement(
            actions=["ec2:DescribeVpcs", "ec2:DescribeSubnets", "ec2:DescribeSecurityGroups"], resources=['*'])
        describe_vpc_policy = iam.Policy(self, "DescribeVpcsPolicy", statements=[describe_vpc_policy_statement])
        self.discord_handler.role.attach_inline_policy(describe_vpc_policy)
        self.queue_handler.role.attach_inline_policy(describe_vpc_policy)
