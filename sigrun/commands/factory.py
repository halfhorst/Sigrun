# from typing import List

# from sigrun.commands.base import BaseCommand
# from sigrun.commands.server_status import ServerStatus
# from sigrun.commands.stop_server import StopServer
# from sigrun.commands.start_server import StartServer

# COMMANDS = [ServerStatus, StartServer, StopServer]


# def get_command(name: str, options: List[dict]) -> BaseCommand:
#     if name == ServerStatus.name:
#         return ServerStatus(options)
#     if name == StartServer.name:
#         return StartServer(options)
#     if name == StopServer.name:
#         return StopServer(options)

#     raise RuntimeError(f"Unknown command {name} encountered")
