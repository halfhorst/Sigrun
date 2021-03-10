import os
import subprocess

import click
import pkg_resources
from loguru import logger

from sigrun.bot import Sigrun


@click.group()
def sigrun():
    """The Sigrun Discord bot interface."""
    pass


# TODO: There will be configuration here, at very least Valheim server data location.
# Add args that default to env vars
@sigrun.command()
def run():
    """Start Sigrun"""
    sigbot = Sigrun()
    sigbot.run()


# @sigrun.command()
# def get_registered_commands():
#     """List the guild commands already registered to Sigrun"""
#     logger.disable("sigrun")
#     sigbot = Sigrun()
#     commands = sigbot.get_registered_commands()
#     pprint.pprint(commands, sort_dicts=False)
#     sigbot.loop.close()


# @sigrun.command()
# def get_sigrun_commands():
#     """List the commands that Sigrun supports"""
#     sigbot = Sigrun()
#     pprint.pprint(sigbot.commands, sort_dicts=False)


# @sigrun.command()
# @click.option("--name")
# @click.option("--all", is_flag=True, default=False)
# def register_command(all, name):
#     """Register one of Sigrun's commands"""
#     sigbot = Sigrun()
#     if all:
#         sigbot.register_commands(sigbot.commands)
#     elif name:
#         command = [d for d in sigbot.commands if d['name'] == name]
#         if len(command) == 0:
#             raise ValueError(f"command {name} not recognized")
#         sigbot.register_commands(command)


# @ sigrun.command()
# @ click.argument("command_id")
# def delete_command(command_id):
#     """Unregister one of Sigrun's commands"""
#     sigbot = Sigrun()
#     sigbot.delete_command(command_id)
#     sigbot.loop.close()


@ sigrun.command()
def get_steamcmd():
    """Download STEAMCMD"""
    raise NotImplementedError

    required_env_vars = ["STEAMCMD", "STEAM_LOGIN", "STEAM_PASSWORD"]
    for env_var in required_env_vars:
        if env_var not in os.environ:
            raise RuntimeError("Please source your env file.")

    script = pkg_resources.resource_filename(
        "sigrun", "scripts/get_steamcmd.sh")
    popen = subprocess.Popen(script)
    popen.wait()


@ sigrun.command()
def get_valheim():
    """Download valheim and valheim dedicated server"""
    raise NotImplementedError

    required_env_vars = ["STEAMCMD", "STEAM_LOGIN", "STEAM_PASSWORD"]
    for env_var in required_env_vars:
        if env_var not in os.environ:
            raise RuntimeError("Please source your env file.")

    script = pkg_resources.resource_filename(
        "sigrun", "scripts/get_valheim.sh")
    popen = subprocess.Popen(script)
    popen.wait()
