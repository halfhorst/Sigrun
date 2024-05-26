from .create_server import CreateServer
from .list_games import ListGames
from .list_servers import ListServers
from .server_status import ServerStatus
from .start_server import StartServer
from .stop_server import StopServer

COMMANDS = {
    CreateServer.get_discord_name(): CreateServer,
    ListGames.get_discord_name(): ListGames,
    ListServers.get_discord_name(): ListServers,
    ServerStatus.get_discord_name(): ServerStatus,
    StartServer.get_discord_name(): StartServer,
    StopServer.get_discord_name(): StopServer,
}
