import os
from pathlib import Path

from aws_cdk import Duration, SecretValue
from aws_cdk import aws_apigatewayv2 as apigateway
from aws_cdk import aws_apigatewayv2_integrations as apigateway_integrations
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct

import sigrun


class SigrunConstruct(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        try:
            secret = secretsmanager.Secret(
                self,
                "ApplicationPublicKeySecret",
                secret_name="APPLICATION_PUBLIC_KEY",
                secret_object_value={
                    "APPLICATION_PUBLIC_KEY": SecretValue.unsafe_plain_text(
                        os.environ.get("APPLICATION_PUBLIC_KEY", None)
                    )
                },
            )
        except TypeError:
            raise RuntimeError(
                "You must expose your Discord application pub key as an environment variable named APPLICATION_PUBLIC_KEY"
            )

        deferred_handler = lambda_.Function(
            self,
            "DeferredLambdaHandler",
            runtime=lambda_.Runtime.PYTHON_3_10,
            code=lambda_.Code.from_asset(
                str(Path(sigrun.__file__).resolve().parents[1] / "sigrun.zip")
            ),
            handler="deferred.main",
            timeout=Duration.minutes(5),
            log_retention=logs.RetentionDays.TWO_WEEKS,
        )

        initial_handler = lambda_.Function(
            self,
            "DiscordLambdaHandler",
            runtime=lambda_.Runtime.PYTHON_3_10,
            code=lambda_.Code.from_asset(
                str(Path(sigrun.__file__).resolve().parents[1] / "sigrun.zip")
            ),
            handler="initial.main",
            timeout=Duration.seconds(10),
            log_retention=logs.RetentionDays.TWO_WEEKS,
            environment={"DEFERRED_LAMBDA_NAME": deferred_handler.function_name},
        )

        describe_instances_policy = iam.PolicyStatement(
            actions=[
                "ec2:DescribeInstances",
                "ec2:StartInstances",
                "ec2:StopInstances",
                "ec2:CreateTags",
                "ec2:DeleteTags",
            ],
            resources=["*"],
        )

        lambda_integration = apigateway_integrations.HttpLambdaIntegration(
            "HttpLambdaIntegration", handler=initial_handler
        )
        http_api = apigateway.HttpApi(self, "SigrunHttpApi")

        http_api.add_routes(
            path="/",
            methods=[apigateway.HttpMethod.ANY],
            integration=lambda_integration,
        )

        secret.grant_read(initial_handler.role)
        deferred_handler.grant_invoke(initial_handler)
        deferred_handler.add_to_role_policy(describe_instances_policy)
