# import time
# from decimal import Decimal
# from typing import List

# from loguru import logger

# from sigrun.cloud.util import CloudUtility
# from sigrun.commands.base import BaseCommand
# from sigrun.commands.discord import CHAT_INPUT_TYPE
# from sigrun.model.game import VALHEIM
# from sigrun.model.options import StopServerOptions


# class StopServer(BaseCommand):
#     name = "stop-server"
#     options: StopServerOptions

#     def __init__(self, options: List[dict]):
#         self.options = StopServerOptions.from_dict(options)
#         self.game = VALHEIM

#     @staticmethod
#     def get_cli_description():
#         return "Stop a game server."

#     @staticmethod
#     def get_discord_metadata():
#         return {
#             "type": CHAT_INPUT_TYPE,
#             "name": "stop-server",
#             "description": StopServer.get_cli_description(),
#             "default_permission": True,
#             "options": StopServerOptions.get_discord_metadata(),
#         }

#     def handler(self) -> str:
#         server_name = self.options.server_name.value
#         cloud_utility = CloudUtility(self.game)
#         table = cloud_utility.get_table_resource()

#         existing_item = table.get_item(
#             Key={"game": str(self.game), "serverName": server_name}
#         )

#         if "Item" not in existing_item:
#             message = f"No running {self.game} server named {server_name} found."
#             logger.info(message)
#             return message

#         task_arn = existing_item["Item"]["taskArn"]
#         if task_arn == "":
#             message = f"No running {self.game} server named {server_name} found."
#             logger.info(message)
#             return message

#         stopped_task = cloud_utility.stop_task(task_arn)
#         if stopped_task["ResponseMetadata"]["HTTPStatusCode"] != 200:
#             message = "Failed to stop Fargate task!"
#             logger.error(message)
#             return message

#         table = cloud_utility.get_table_resource()
#         server_database_data = table.get_item(
#             Key={"game": str(self.game), "serverName": server_name}
#         )
#         if server_database_data["ResponseMetadata"]["HTTPStatusCode"] != 200:
#             message = "Fargate task stopped, but failed to update DynamoDB record."
#             logger.error(message)
#             return message

#         if "Item" not in server_database_data:
#             message = (
#                 "Failed to get DynamoDB record for an existing world. Most unexpected!"
#             )
#             logger.error(message)
#             return message

#         uptime = Decimal(time.time()) - server_database_data["Item"]["uptimeStart"]
#         return self.update_item(table, server_name, uptime)

#     def update_item(self, table, server_name: str, uptime: float) -> str:
#         table.update_item(
#             Key={"game": str(self.game), "serverName": server_name},
#             AttributeUpdates={
#                 "totalUptime": {"Value": uptime, "Action": "ADD"},
#                 "uptimeStart": {"Value": None, "Action": "PUT"},
#                 "serverPassword": {"Value": None, "Action": "PUT"},
#                 "taskArn": {"Value": "", "Action": "PUT"},
#                 "status": {"Value": "STOPPED", "Action": "PUT"},
#                 "publicIp": {"Value": "", "Action": "PUT"},
#             },
#         )

#         message = f"Stopped {self.game} server {server_name}."
#         logger.info(message)
#         return message

#     def is_deferred(self) -> bool:
#         return False

#     def deferred_handler(self) -> str:
#         pass
