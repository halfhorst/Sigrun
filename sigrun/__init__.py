from sigrun.bot import RiseAndGrind, ServerStatus, StartServer, StopServer

COMMANDS = {cmd.name: cmd for cmd in [ServerStatus, StartServer, StopServer, RiseAndGrind]}

