import os

import click
import httpx
import pprint
from loguru import logger

from sigrun.commands.start_server_v2 import StartServer
from sigrun.commands.list_games import ListGames


APPLICATION_ID = os.getenv("APPLICATION_ID")
GUILD_ID = os.getenv("GUILD_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not (APPLICATION_ID and GUILD_ID and BOT_TOKEN):
    raise RuntimeError("Missing a required environment variable.")

BASE_URL = "https://discord.com/api/v10"
COMMANDS_URL = f"{BASE_URL}/applications/{APPLICATION_ID}/commands"
GUILD_COMMANDS_URL = (
    f"{BASE_URL}/applications/{APPLICATION_ID}/guilds/{GUILD_ID}/commands"
)
AUTH_HEADERS = {"Authorization": f"{BOT_TOKEN}"}


@click.group()
def sigrun():
    """The Sigrun Discord bot command line interface. Used to list and register commands
    with your application."""
    pass


# ################################
# # Configuration APIs
# ################################


@sigrun.command()
def list():
    """DISCORD API: List Sigrun's commands. Only global commands are supported."""
    r = httpx.get(COMMANDS_URL, headers=AUTH_HEADERS)
    if r.status_code != 200:
        logger.error(f"Failed to get registered commands: {pprint.pformat(r.json())}")
    else:
        logger.info(f"Registered commands: {pprint.pformat(r.json())}")


@sigrun.command()
def register():
    """DISCORD API: Register Sigrun's commands with your application. This only needs to
    be run once. It's idempotent, you can run it repeatedly."""
    for command in COMMANDS:
        logger.debug(f"Registering command {command.get_discord_metadata()}")
        r = httpx.post(
            COMMANDS_URL, json=command.get_discord_metadata(), headers=AUTH_HEADERS
        )
        if not (r.status_code == 201 or r.status_code == 200):
            logger.error(
                f"Failed to register {command.name}: {r.status_code} {pprint.pformat(r.json())}"
            )
        else:
            logger.info(f"Registered {command.name}.")


@sigrun.command()
@click.argument("command_id")
def delete(command_id: str):
    """DISCORD API: Delete the Sigrun command referenced by COMMAND_ID."""
    r = httpx.delete(COMMANDS_URL + f"/{command_id}", headers=AUTH_HEADERS)
    if r.status_code != 204:
        logger.error(
            f"Failed to delete {command_id}: {r.status_code} {pprint.pformat(r.json())}"
        )
    else:
        logger.info(f"Deleted {command_id}.")


@sigrun.command()
def update_valheim_image():
    raise NotImplementedError("TODO..")


# ################################
# # Bot Command CLI Interface
# ################################


@sigrun.command(help=ListGames.get_cli_description())
def list_games():
    command = ListGames({})
    logger.info(command.handler())


# @sigrun.command(help=ServerStatus.get_cli_description())
# def server_status():
#     command = ServerStatus({})
#     logger.info(command.handler())
#     if command.is_deferred():
#         logger.info(command.deferred_handler())


@sigrun.command(help=StartServer.get_cli_description())
@click.argument("game")
@click.argument("server_name")
@click.argument("server_password")
def start_server(game: str, server_name: str, server_password: str):
    # options = [
    #     {"name": ""}
    #     {"name": StartServerOptions.server_name.name, "value": server_name},
    #     {"name": StartServerOptions.server_password.name, "value": server_password},
    # ]
    command = StartServer(game, server_name, server_password)
    command.handler()
    if command.is_deferred():
        logger.info(command.deferred_handler())


# @sigrun.command(help=StopServer.get_cli_description())
# @click.argument("server_name")
# def stop_server(server_name: str):
#     options = [{"name": StopServerOptions.server_name.name, "value": server_name}]
#     command = StopServer(options)
#     logger.info(command.handler())
#     if command.is_deferred():
#         logger.info(command.deferred_handler())
