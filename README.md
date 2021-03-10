# Sigrun

Sigrun is a Discord bot that helps you manage a Valheim server instance. She was motivated by problems keeping the valheim dedicated server application up to date in a server I ran for my friends. Sigrun also provides convenience commands to help you get steamcmd and valheim dedicated server on your box. Sigrun works by spawning and managing a Valheim server as a child process.

Sigrun is a 'personal' bot, not a public one. You need to create an application for your own server and run your own instance of the bot. You can just run it wherever you were planning to run your server.

## Discord Interactions

* `server-status`: Get the Valheim server's status and hardware usage.
* `server-down`: Shut the Valheim server down.
* `server-up`: Start the Valheim server up.
* `server-update`: Bring the Valheim server down, update it, and bring it back up.

* `check-backup`: NotImplemented. Get the most recent backup information.
* `make-backup`: NotImplemented. Create a backup in an S3 bucket.
* `wisdom`: NotImplemented. ???
* `weave-fate`: NotImplemented. ???

## Getting Started

1. Clone this repo
2. Install the python package using pip `pip install .`
3. Create your own environment file from the template and source it: `source <file>.env`.
    - You need to register an application + bot with Discord if you haven't already
4. Add your bot to your server. Use the generated link in the application interface.
5. Use Sigrun to get steamcmd and/or valheim if you don't have it on your server already.
5. Start the bot on your server: `sigrun run`. You can use `sigrun --help` to see all of Sigrun's options.

## Design

Sigrun spawns a Valheim dedicated server as a child process and allows you to manage it through Discord interactions (slash commands). The bot is split across two modules: `connection.py` that abstracts away the HTTP and Websocket/Gateway interfaces to the Discord API, and `bot.py` that holds the main event loop and interaction handlers. The HTTP and Websocket connections are handled using `aiohttp` and an event loop. Getting STEAMCMD, getting/updating Valheim, and running the server are handled by shell scripts packaged with the bot. All configuration is handled through environment variables.

There are many fully-featured Discord API wrappers out there, and you should use them. I wanted to work with the Discord API directly, for fun, so I did not.

I run this on a cloud server with SSH access. If you're just getting started with this stuff, note that you need to explicitly expose ports for the server to be accessible. TODO: mention the specifics.

## Configuration

Interacting with Steam, Discord and Valheim requires a good bit of configuration, and Sigrun handles it all through environment variables. 
