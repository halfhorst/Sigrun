import os

import click
import httpx
import pprint
from loguru import logger

from sigrun.commands.factory import COMMANDS

APPLICATION_ID = os.getenv("APPLICATION_ID")
GUILD_ID = os.getenv("GUILD_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not (APPLICATION_ID and GUILD_ID and BOT_TOKEN):
    raise RuntimeError("Missing a required environment variable.")

BASE_URL = "https://discord.com/api/v10"
COMMANDS_URL = f"{BASE_URL}/applications/{APPLICATION_ID}/commands"
GUILD_COMMANDS_URL = f"{BASE_URL}/applications/{APPLICATION_ID}/guilds/{GUILD_ID}/commands"
AUTH_HEADERS = {"Authorization": f"{BOT_TOKEN}"}


@click.group()
def sigrun():
    """The Sigrun Discord bot command line interface. Used to list and register commands
    with your application."""
    pass


@sigrun.command()
def list():
    """List Sigrun's commands. Only global commands are supported."""
    r = httpx.get(COMMANDS_URL, headers=AUTH_HEADERS)
    if r.status_code != 200:
        logger.error(f"Failed to get registered commands: {pprint.pformat(r.json())}")
    else:
        logger.info(f"Registered commands: {pprint.pformat(r.json())}")


@sigrun.command()
def register():
    """Register Sigrun's commands with your application. This only needs to 
    be run once. It's idempotent, you can run it repeatedly."""
    for command in COMMANDS:
        logger.debug(f"Registering command {command.get_discord_metadata()}")
        r = httpx.post(COMMANDS_URL, json=command.get_discord_metadata(), headers=AUTH_HEADERS)
        if not (r.status_code == 201 or r.status_code == 200):
            logger.error(f"Failed to register {command.name}: {r.status_code} {pprint.pformat(r.json())}")
        else:
            logger.info(f"Registered {command.name}.")


@sigrun.command()
@click.argument('command_id')
def delete(command_id: str):
    """Delete the Sigrun command referenced by COMMAND_ID."""
    r = httpx.delete(COMMANDS_URL + f"/{command_id}", headers=AUTH_HEADERS)
    if r.status_code != 204:
        logger.error(f"Failed to delete {command_id}: {r.status_code} {pprint.pformat(r.json())}")
    else:
        logger.info(f"Deleted {command_id}.")


@sigrun.command()
def update_valheim_image():
    raise NotImplementedError("TODO..")

# ################################
# # Bot Command CLI Interface
# ################################
#
# @sigrun.command(help=COMMANDS.get("server-status").get_description())
# def server_status():
#     COMMANDS.get("server-status").handler([])
#
# @sigrun.command(help=COMMANDS.get("start-server").get_description())
# @click.argument('world_name')
# @click.argument('server_name')
# @click.argument('server_password')
# def start_server(world_name: str, server_name: str, server_password: str):
#     command = COMMANDS.get("start-server")
#     command.handler([
#         {
#             "name": command.world_name_option,
#             "value": world_name
#         },
#         {
#             "name": command.server_name_option,
#             "value": server_name
#         },
#         {
#             "name": command.server_pass_option,
#             "value": server_password
#         }
#     ])
#
# @sigrun.command(help=COMMANDS.get("stop-server").get_description())
# @click.argument('world_name')
# def stop_server(world_name: str):
#     command = COMMANDS.get("stop-server")
#     command.handler([
#         {
#             "name": command.world_name_option,
#             "value": world_name
#         }
#     ])
