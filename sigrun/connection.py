import aiohttp
import asyncio
import json

from enum import IntEnum
from loguru import logger


class DiscordConnectionException(Exception):
    pass


class DiscordActivityType(IntEnum):
    PLAYING = 0
    STREAMING = 1
    LISTENING = 2
    CUSTOM = 4  # "{emoji} {text}"
    COMPETING_IN = 5


class DiscordOp(IntEnum):
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


class DiscordPayload:
    def __init__(self, op, s=None, d=None, t=None):
        try:
            self.op = DiscordOp(op)
        except ValueError:
            raise RuntimeError(f"Unhandled op: {op}")
        self.s = s
        self.d = d
        self.t = t

    def to_json(self):
        return {**vars(self), **{"op": int(self.op)}}

    def __str__(self):
        return f"{{op: {self.op!s}; t: {self.t}; s: {self.s}; d: {self.d}}}"


class DiscordConnection:
    """
    A class representing a Websocket connection to Discord's Gateway.

    It abstracts away all connection details from it's client. It bubbles up
    interaction commands and consumes everything else to maintain the
    connection. The bot client ends up quite simple: It sends its commands
    and handles them as they are received.

    Abstract both HTTP and Websocket communication with Discord
    provides hooks for registering event handlers

    """

    BASE_URL = "https://discord.com/api/v8"

    def __init__(self, loop, session, websocket,
                 application_id, guild_id, bot_token):
        self.loop = loop
        self.session = session
        self.websocket = websocket
        self.application_id = application_id
        self.guild_id = guild_id
        self.bot_token = bot_token

        self.is_open = False

        self.keep_alive_task = None
        self.heartbeat_ack = True
        self.session_id = None
        self.sequence = None

    @classmethod
    async def create(cls, loop, application_id, guild_id, bot_token):
        session = aiohttp.ClientSession(headers={"Authorization": bot_token})

        websocket_url = await cls.get_websocket_url(session, cls.BASE_URL)
        logger.info(
            "Websocket URL acquired. "
            f"Establishing connection with {websocket_url}"
        )
        websocket = await session.ws_connect(websocket_url)

        gateway = cls(loop, session, websocket,
                      application_id, guild_id, bot_token)

        return gateway

    @staticmethod
    async def get_websocket_url(session, base_url, version=8, encoding="json"):
        response = await session.get(f"{base_url}/gateway")
        if not response.ok:
            raise RuntimeError("Failed to get Websocket URL")
        payload = await response.json()

        return f"{payload['url']}/?v={version}&encoding={encoding}"

    async def connect(self):
        logger.info("Handshaking with the Discord Gateway")

        message = await self.get_message()
        if message.op != DiscordOp.HELLO:
            raise RuntimeError("Failed to receive Hello message")
        heartbeat_interval = message.d["heartbeat_interval"]

        logger.info("Starting heartbeat routine")
        if self.keep_alive_task not in asyncio.all_tasks():
            self.keep_alive_task = self.loop.create_task(
                self.keep_alive(int(heartbeat_interval) / 1000)
            )

        message = await self.get_message()
        if message.op != DiscordOp.HEARTBEAT_ACK:
            raise RuntimeError("Failed to receive heartbeat ACK")

        await self.identify()

        message = await self.get_message()
        if message.t != "READY":
            raise RuntimeError("Identify payload was invalid")
        self.session_id = message.d["session_id"]
        self.is_open = True

    async def disconnect(self):
        await self.session.close()

    async def keep_alive(self, duration):
        while True:
            if not self.heartbeat_ack:
                logger.info("Failed to receive ACK")
                # TODO: Close and reconnect
            await self.heartbeat()
            self.heartbeat_ack = False
            await asyncio.sleep(duration)

    def skim_message(self, message: DiscordPayload):
        """We skim messages for maintenance info here."""
        if message.op == DiscordOp.HEARTBEAT_ACK:
            self.heartbeat_ack = True
        if message.s is not None:
            self.sequence = message.s
        return message

    async def get_interaction(self):
        message = await self.get_message()
        if message.op == DiscordOp.DISPATCH:
            if message.t == "INTERACTION_CREATE":
                return message

    async def get_message(self):
        message = await self.websocket.receive()
        if message.type == aiohttp.WSMsgType.TEXT:
            translated_message = DiscordPayload(**json.loads(message.data))
            logger.info(f"Received message {translated_message}")
            return self.skim_message(translated_message)
        elif (message.type == aiohttp.WSMsgType.CLOSED
              or message.type == aiohttp.WSMsgType.CLOSE):
            logger.info("Received Closed message. Attempting to Reconnect")
            # TODO: What does reconnect entail?
            await self.reconnect()
            self.is_open = False

    async def reconnect(self):
        # TODO: Close connection if possible
        # TODO: Re-connect
        # TODO: Send RESUME
        # TODO: Replay all events until RESUMED
        await self.identify()
        logger.info("Reconnect is not currently implemented")

    async def send_gateway_command(self, payload):
        payload = DiscordPayload(**payload)
        logger.info(f"Sending message: {payload}")
        await self.websocket.send_json(payload.to_json())

    async def identify(self):
        await self.send_gateway_command(
            {
                "op": DiscordOp.IDENTIFY,
                "d": {
                    "token": self.bot_token,
                    "intents": 513,
                    "properties": {
                        "$os": "linux",
                        "$browser": "Sigrun",
                        "$device": "Sigrun",
                    },
                },
            }
        )

    async def update_presence(self, name: str, type: DiscordActivityType):
        await self.send_gateway_command({"op": DiscordOp.PRESENCE_UPDATE,
                                         "d": {
                                             "activities": [{
                                                 "name": name,
                                                 "type": type
                                             }],
                                             "status": "online",
                                             "afk": False
                                         }})

    async def heartbeat(self):
        await self.send_gateway_command({"op": DiscordOp.HEARTBEAT, "d": None})

    async def post_command(self, name, description):
        payload = {"name": name, "description": description}
        command_url = (f"{self.BASE_URL}/applications/{self.application_id}/"
                       f"guilds/{self.guild_id}/commands")

        logger.info(f"Posting command: {payload} to {command_url}")
        response = await self.session.post(command_url, json=payload)
        if not response.ok:
            logger.warning(f"Failed to post command: {response}")
        return response.ok

    async def get_commands(self):
        command_url = (f"{self.BASE_URL}/applications/{self.application_id}/"
                       f"guilds/{self.guild_id}/commands")
        logger.info(f"Requesting commands from {command_url}")
        response = await self.session.get(command_url)
        if not response.ok:
            logger.warning("Failed to retrieve command list")
        return await response.json()

    async def delete_command(self, command_id):
        command_url = (f"{self.BASE_URL}/applications/{self.application_id}/"
                       f"guilds/{self.guild_id}/commands/{command_id}")
        logger.info(f"Deleting command {command_id}")
        response = await self.session.delete(command_url)
        if not response.ok:
            logger.warning(f"Failed to delete {command_id}")
        return response.ok

    async def post_message(self, channel_id, content=None,
                           title=None, description=None):
        payload = {"tts": False}
        if content is not None:
            payload["content"] = content

        if title and description:
            payload["embed"] = {"title": title, "description": description}

        message_url = f"{self.BASE_URL}/channels/{channel_id}/messages"
        response = await self.session.post(message_url, json=payload)
        if not response.ok:
            logger.warning("Failed to post message.")
        return response.ok

    # responding-to-an-interaction
    # https: // discord.com/developers/docs/interactions/slash-commands
    # https://discord.com/developers/docs/interactions/slash-commands#interaction-response

    async def post_interaction_response(self):
        pass
