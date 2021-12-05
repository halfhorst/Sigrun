from pathlib import Path

from aws_cdk import (
    core as cdk,
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    aws_efs as efs,
    aws_apigatewayv2 as apigateway,
    aws_apigatewayv2_integrations as apigateway_integrations,
    aws_logs as logs,
    aws_dynamodb as dynamodb)

import sigrun


class SigrunConstruct(cdk.Construct):

    def __init__(self, scope: cdk.Construct, construct_id: str, vpc: ec2.Vpc, file_system: efs.FileSystem, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dynamodb.Table(
            self, 
            "GameServerTable",
            table_name="GameServerTable",
            partition_key=dynamodb.Attribute(name="game", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="worldName", type=dynamodb.AttributeType.STRING))

        handler = lambda_.Function(self, "SigrunLambdaFunction",
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset(str(Path(sigrun.__file__).resolve().parents[1] / "sigrun.zip")),
            handler="handler.main",
            timeout=cdk.Duration.seconds(15),
            log_retention=logs.RetentionDays.TWO_WEEKS)

        lambda_integration = apigateway_integrations.HttpLambdaIntegration("HttpLambdaIntegration", handler=handler)
        http_api = apigateway.HttpApi(self, "SigrunHttpApi")

        http_api.add_routes(
            path="/",
            methods=[apigateway.HttpMethod.ANY],
            integration=lambda_integration)
