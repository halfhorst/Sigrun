import click

from loguru import logger

from sigrun.commands.base import Command, Context
from sigrun.commands.start_server import StartServer
from sigrun.commands.list_games import ListGames


@click.group()
def sigrun():
    """The Sigrun Discord bot command line interface. Used to list and register commands
    with your application."""


@sigrun.command(help=ListGames.get_cli_description())
def list_games():
    ListGames({}, context=Context.CLI).handler()

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
