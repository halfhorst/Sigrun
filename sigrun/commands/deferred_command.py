# import json
# from typing import List

# from sigrun.commands.base import BaseCommand
# from sigrun.commands import factory


# class DeferredCommandInput:
#     command_name: str
#     options: List[dict]
#     application_id: str
#     interaction_token: str

#     def __init__(
#         self,
#         command_name: str,
#         options: List[dict],
#         application_id: str,
#         interaction_token: str,
#     ):
#         self.command_name = command_name
#         self.options = options
#         self.application_id = application_id
#         self.interaction_token = interaction_token

#     @staticmethod
#     def from_dict(body: dict):
#         try:
#             command_name = body.get("command_name")
#             options = body.get("options")
#             application_id = body.get("application_id")
#             interaction_token = body.get("interaction_token")
#         except KeyError:
#             raise RuntimeError(f"Received an improperly formatted event body: {input}.")

#         return DeferredCommandInput(
#             command_name, options, application_id, interaction_token
#         )

#     def to_json(self) -> str:
#         return json.dumps(
#             {
#                 "command_name": self.command_name,
#                 "options": self.options,
#                 "application_id": self.application_id,
#                 "interaction_token": self.interaction_token,
#             }
#         )
