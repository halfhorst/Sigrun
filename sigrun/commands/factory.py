from sigrun.commands.server_status import ServerStatus
from sigrun.commands.stop_server import StopServer
from sigrun.commands.start_server import StartServer

COMMANDS = [ServerStatus, StartServer, StopServer]
COMMAND_MAP = {cmd.name: type(cmd) for cmd in COMMANDS}


def get_command(name: str, options: dict):
    return COMMAND_MAP[name](options)
