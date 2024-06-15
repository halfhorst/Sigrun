import sys

import click

from sigrun.commands import (
    CreateServer,
    ListGames,
    ListServers,
    ServerStatus,
    StartServer,
    StopServer,
)
from sigrun.exceptions import GameNotFoundError


@click.group(invoke_without_command=True)
def sigrun():
    """The Sigrun Discord bot command line interface.
    Used to list and register commands with your application."""


@sigrun.command(help=ListGames.get_cli_description())
def list_games():
    ListGames().handler()


@sigrun.command(help=ServerStatus.get_cli_description())
@click.argument("game")
@click.argument("server_name")
def server_status(game: str, server_name: str):
    ServerStatus(game, server_name).handler()


@sigrun.command(help=ListServers.get_cli_description())
@click.option("-g", "--game")
def list_servers(game: str = ""):
    ListServers(game).handler()


@sigrun.command(help=CreateServer.get_cli_description())
@click.argument("game")
@click.argument("server_name")
@click.argument("password")
def create_server(game: str, server_name: str, password: str):
    try:
        CreateServer(game, server_name, password).handler()
    except GameNotFoundError:
        sys.exit(1)


@sigrun.command(help=StartServer.get_cli_description())
@click.argument("instance_id")
def start_server(instance_id: str):
    StartServer(instance_id).handler()


@sigrun.command(help=StopServer.get_cli_description())
@click.argument("instance_id")
def stop_server(instance_id: str):
    StopServer(instance_id).handler()
