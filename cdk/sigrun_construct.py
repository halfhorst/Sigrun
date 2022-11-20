from pathlib import Path

from constructs import Construct
from aws_cdk import Duration
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_efs as efs
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_apigatewayv2_alpha as apigateway
from aws_cdk import aws_apigatewayv2_integrations_alpha as apigateway_integrations
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_lambda_event_sources as LambdaEventSources


import sigrun

class SigrunConstruct(Construct):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, file_system: efs.FileSystem, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dynamodb.Table(
            self, 
            "GameServerTable",
            table_name="GameServerTable",
            partition_key=dynamodb.Attribute(name="game.py", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="worldName", type=dynamodb.AttributeType.STRING))

        handler = lambda_.Function(self, "DiscordLambdaHandler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset(str(Path(sigrun.__file__).resolve().parents[1] / "sigrun.zip")),
            handler="discord.main",
            timeout=Duration.seconds(15),
            log_retention=logs.RetentionDays.TWO_WEEKS)

        lambda_integration = apigateway_integrations.HttpLambdaIntegration("HttpLambdaIntegration", handler=handler)
        http_api = apigateway.HttpApi(self, "SigrunHttpApi")

        http_api.add_routes(
            path="/",
            methods=[apigateway.HttpMethod.ANY],
            integration=lambda_integration)

        queue = sqs.Queue(self, "StartServerQueue")
        queue_handler = lambda_.Function(self, "SqsLambdaHandler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset(str(Path(sigrun.__file__).resolve().parents[1] / "sigrun.zip")),
            handler="sqs.main",
            timeout=Duration.seconds(15),
            log_retention=logs.RetentionDays.TWO_WEEKS)

        event_source = LambdaEventSources.SqsEventSource(queue);
        queue_handler.add_event_source(event_source);
