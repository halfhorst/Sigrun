import asyncio
import atexit
import datetime
import os
import signal
import traceback
import subprocess
import threading

import pkg_resources
import psutil
from loguru import logger

from sigrun.connection import (DiscordActivityType,
                               DiscordConnection,
                               DiscordConnectionException)


class Sigrun:
    """
    Sigrun is a Discord bot for managing Valheim servers.
    It instantiates a Discord connection, indicates its commands, and
    handles them. The Discord connection manages all low-level details,
    bubbling up only interactions for this bot to handle.

    The main function of Sigrun is to manage a Valheim server. On init
    it spawns the valheim server and records the PID. This PID is used
    to implement Sigrun's commands.

    A mutex is used to protect against conccurent manipulation of the PID.

    """

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.loop.add_signal_handler(
            signal.SIGINT, lambda: self.log_and_stop("SIGINT"))
        self.loop.add_signal_handler(
            signal.SIGTERM, lambda: self.log_and_stop("SIGTERM")
        )
        self.loop.set_exception_handler(self.exception_handler)

        self.credentials = self.get_credentials()

        self.task_handlers = {"server-status": self.handle_server_status,
                              "server-update": self.handle_server_update,
                              "server-down": self.handle_server_down,
                              "server-up": self.handle_server_up}

        self.lock = threading.Lock()
        self.lock_message = ("I can't do that right now. Someone else "
                             "has asked to manipulate the server.")

        self.server_script = pkg_resources.resource_filename("sigrun",
                                                             "scripts/test_run.sh")
        self.update_script = pkg_resources.resource_filename("sigrun",
                                                             "scripts/test_update.sh")
        self.server_proc = None

    def start_server(self) -> bool:
        """Attempts to start the server. Sets `server_proc` to the popen object.
        Will fail and return False if a server is already running,
        otherwise returns True."""
        logger.info("Starting the Valheim server")

        if self.server_proc is not None:
            logger.warning("Start server requested but the server is running")
            return False

        self.server_proc = subprocess.Popen(self.server_script)
        return True

    def stop_server(self) -> bool:
        """Attempts to stop the Valheim server. Sets `server_proc` to None.
        Will fail and return false if a server is not running, otherwise
        returns True."""
        logger.info("Stopping the Valheim server")

        if self.server_proc is None:
            logger.warning("Stop server requested but server is not running")
            return False

        self.server_proc = None
        return True

    def update_server(self) -> bool:
        """Attmpts to update the Valheim server. Will fail and return False
        if the server is running, otherwise returns True."""
        logger.info("Updating the valheim server")

        if self.server_proc is not None:
            logger.warning("Update server requested but the server is running")
            return False

        update_proc = subprocess.Popen(self.update_script)
        update_proc.wait()
        if update_proc.returncode:
            logger.warning("Update server script failed")
            return False
        return True

    def get_credentials(self):
        if "BOT_TOKEN" not in os.environ:
            raise RuntimeError(
                "Please complete and source your environment file.")
        elif "APPLICATION_ID" not in os.environ:
            raise RuntimeError(
                "Please complete and source your environment file.")
        elif "GUILD_ID" not in os.environ:
            raise RuntimeError(
                "Please complete and source your environment file.")
        return {"bot_token": os.environ["BOT_TOKEN"],
                "application_id": os.environ["APPLICATION_ID"],
                "guild_id": os.environ["GUILD_ID"]}

    def run(self):
        """This is the main event loop. Sigrun starts the underlying Valheim
        server and then adds a coordinating task to the async event loop
        and runs it. The coordinating task orders the discord connection
        and the message handling loop.
        """
        self.start_server()

        async def _run():
            discord_connection = await DiscordConnection.create(
                self.loop,
                self.credentials["application_id"],
                self.credentials["guild_id"],
                self.credentials["bot_token"],
            )
            atexit.register(discord_connection.disconnect)

            try:
                await asyncio.wait_for(discord_connection.connect(),
                                       timeout=60)
            except asyncio.TimeoutError:
                self.loop.stop()
                raise RuntimeError("Failed to initiate connect to discord")

            # for command in self.commands:
            #     await discord_connection.post_command(**command)

            # self.loop.create_task(self.update_presence(discord_connection))

            # TODO: Consider splitting this such that gets or handles can fail
            while discord_connection.is_open:
                try:
                    message = await discord_connection.get_interaction()
                except DiscordConnectionException as e:
                    logger.exception(f"Encountered a connection error {e}")
                    continue
                if message is not None:
                    command_name = message.d["data"]["name"]
                    await self.async_handle_command(command_name,
                                                    discord_connection,
                                                    message.d)

        self.loop.create_task(_run())

        try:
            # TODO: I think this can be something different
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.log_and_stop("KeyboardInterrupt")

    # def get_registered_commands(self):
    #     async def _list():
    #         discord_connection = await DiscordConnection.create(
    #             self.loop,
    #             self.credentials["application_id"],
    #             self.credentials["guild_id"],
    #             self.credentials["bot_token"],
    #         )
    #         commands = await discord_connection.get_commands()
    #         await discord_connection.disconnect()
    #         return commands
    #     return asyncio.run(_list())

    # def register_commands(self, commands):
    #     async def _register():
    #         discord_connection = await DiscordConnection.create(
    #             self.loop,
    #             self.credentials["application_id"],
    #             self.credentials["guild_id"],
    #             self.credentials["bot_token"],
    #         )
    #         for command in commands:
    #             await discord_connection.post_command(**command)
    #         await discord_connection.disconnect()
    #     return asyncio.run(_register())

    # def delete_command(self, name):
    #     async def _delete():
    #         discord_connection = await DiscordConnection.create(
    #             self.loop,
    #             self.credentials["application_id"],
    #             self.credentials["guild_id"],
    #             self.credentials["bot_token"],
    #         )
    #         success = await discord_connection.delete_command(name)
    #         await discord_connection.disconnect()
    #         return success
    #     return asyncio.run(_delete())

    def log_and_stop(self, signame):
        logger.info(f"Received {signame}. Cleaning up")
        self.stop_server()
        self.loop.stop()
        # What about the websocket?

    def exception_handler(self, loop, context):
        """We don't stop the bot or the server on an exception,
        so you can continue to play even if the Sigrun fails to function."""
        # TODO: Getting the full traceback is pain :(
        exception = context.get("exception")
        logger.error(f"Encountered unexpected error {str(exception)}")

    @property
    def commands(self):
        return [
            {
                "name": "server-status",
                "description": "Get the Valheim server's status and "
                               "hardware statistics."
            },
            {
                "name": "server-update",
                "description": "Bring the Valheim server down, update it, "
                               "and bring it back up."
            },
            {
                "name": "server-down",
                "description": "Shut the Valheim server down."
            },
            {
                "name": "server-up",
                "description": "Start the Valheim server up."
            }
        ]

    async def async_handle_command(self, command, conn, data):
        """A coroutine that handles an interaction synchronously.
        TODO: The right way to ack an interaction is to post a specific
        response payload, not a message :(
        """
        message = self.task_handlers[command](data)
        if message is not None:
            await conn.post_message(data['channel_id'], content=message)

    def handle_server_status(self, data):
        logger.info("Handling server-status interaction")

        if not self.lock.acquire(blocking=False):
            return self.lock_message

        if self.server_proc is None:
            return "The server is not currently running."

        psutil_proc = psutil.Process(self.server_proc.pid)

        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(
            psutil_proc.create_time())
        mem_usage = psutil_proc.memory_info().rss / 1.e9  # report in Gb
        cpu_utilization = psutil_proc.cpu_percent()

        return ("The server is running! Here are some stats :wink: \n"
                f"Uptime: {uptime} [hours:minutes:days]\n"
                f"Memory usage: {mem_usage} [Gb]\n"
                f"CPU Utilization: {cpu_utilization:.4f} %")

    def handle_server_update(self, data):
        logger.info("Handling server-update interaction")

        if not self.lock.acquire(blocking=False):
            return self.lock_message

        if not self.stop_server():
            self.lock.release()
            return "I failed to stop the server: disappointed:"

        if not self.update_server():
            self.lock.release()
            return ("I stopped the server, but I couldn't update "
                    "it :disappointed:")

        if not self.start_server():
            self.lock.release()
            return ("I stopped and updated the server! But I failed "
                    "to start it again :disappointed:")

        self.lock.release()
        return "The server has been updated!"

    def handle_server_down(self, data):
        logger.info("Handling server-down interaction")

        if not self.lock.acquire(blocking=False):
            return self.lock_message

        if not self.stop_server():
            message = "I failed to stop the server :disappointed:"
        else:
            message = "The server has been stopped!"

        self.lock.release()
        return message

    def handle_server_up(self, data):
        logger.info("Handling server-up interaction")

        if not self.lock.acquire(blocking=False):
            return self.lock_message

        if not self.start_server():
            message = "I failed to start the server :disappointed:"
        else:
            message = "The server has been started!"

        self.lock.release()
        return message

    async def update_presence(self, conn):
        """A coroutine that updates Sigrun's presence every 12 hours"""
        presences = [("Valheim", DiscordActivityType.PLAYING)]
        index = 0
        while True:
            name, type = presences[index]
            await conn.update_presence(name, type)
            await asyncio.sleep(60 * 60 * 12)
            index = (index + 1) % len(presences)
