from typing import List, Dict

STRING_OPTION_TYPE = 3


class DiscordOption:
    # The option name as shown to the user
    name: str

    # The option's value
    value: str

    def __init__(self, name: str):
        self.name = name


class StartServerOptions:
    """Define options interface, serialize/de-serialize, and discord metadata"""
    server_name = DiscordOption('server-name')
    server_password = DiscordOption('server-password')

    def __init__(self, name: str, password: str):
        self.server_name.value = name
        self.server_password.value = password

    @staticmethod
    def get_discord_metadata() -> List[Dict]:
        return [
            {
                "type": STRING_OPTION_TYPE,
                "name": StartServerOptions.server_name.name,
                "description": "The name of the server. This will be used for the seed and will " +
                               "show up in Valheim's server list.",
                "required": True,
            },
            {
                "type": STRING_OPTION_TYPE,
                "name": StartServerOptions.server_password.name,
                "description": "The server password.",
                "required": True
            }
        ]

    @staticmethod
    def from_dict(options: List[dict]):
        options = {option['name']: option['value'] for option in options}
        return StartServerOptions(options[StartServerOptions.server_name.name],
                                  options[StartServerOptions.server_password.name])


class StopServerOptions:
    server_name = DiscordOption('server-name')

    def __init__(self, name: str):
        self.server_name.value = name

    @staticmethod
    def get_discord_metadata() -> List[Dict]:
        return [{
            "type": STRING_OPTION_TYPE,
            "name": StopServerOptions.server_name.name,
            "description": "The name of the world to stop. Check world-status to see what is currently up.",
            "required": True,
        }]

    @staticmethod
    def from_dict(options: List[dict]):
        options = {option['name']: option['value'] for option in options}
        return StopServerOptions(options[StopServerOptions.server_name.name])
