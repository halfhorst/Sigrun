# Sigrun

Sigrun is a Discord bot that helps you manage dedicated servers for games, like Valheim or 7 Days to Die. I built it because I didn't want to pay for idle servers I was maintaining for my friends, but hosting solutions seem pretty good so the benefits of this setup are debatable. Sigrun is a 'personal' bot, not a public one you can add to your own guild. You need to create a Discord application yourself, for your own server, and run your own instance of the bot on your own AWS account.

Currently, Sigrun supports **Valheim**, **7 Days to Die**, and contains untested startup scripts for **Palworld**, **Abiotic Factor**, and **Factorio**. Adding new games has been very simple. It only requires writing a new startup script and defining a small amount of metadata.

> [!CAUTION]
> This a personal project and I develop it like one. I don't guarantee mainline is in a working state or any development cadence.

> [!CAUTION]
> This bot incurs AWS costs that are potentially unbounded. You can create arbitrarily many EC2 instances and EBS volumes, and you can run them forever. Use it at your own risk.

## TODO
- Do some real error handling around calls into AWS
- A watchdog Lambda `cron` to shutdown long-running servers
- Game-specific server configuration through `create-server`
- A copy-world command that dumps to S3 with an expiration date and provid a presigned URL
    - Eliminate EBS entirely?
- A small on-server API for active player data

## Getting Started

### Pre-requisites

You need the aws cdk cli, you need python, you need an AWS account with credentials setup. The easiest way to setup credentials is with the aws cli.

### Bootstrapping the Bot

**Note**: Deployment of the Lambda must happen from a Linux machine, because the bot package relies on system specific packages (PyNaCl) that must match the Lambda runtime.

1. Create a discord application in their dev portal. Fill out your own `sigrun.env` with the details from your application and source it.
2. Install this python package however you like. I used poetry.
3. Run `sigrun register`. This will register Sigrun's commands with your application.
4. Add your bot to your server using the generated link in the application interface.
5. Deploy the infrastructure with cdk. `cd` into the cdk directory and run `deploy.sh`. This will bundle up the lambda code into an artifact and then deploy everything for you.
    - export `AWS_PROFILE` to control where the cloud services are deployed. Consider creating a role or account specifically for this bot.
    - deployment must occur on a linux machine. This is because the discord package relies on a system-dependent package (PyNaCl) that must be compatible witht he Lambda runtime.
6. Log into the console and grab Sigrun's URL from ApiGateway. Give this to your application as the "Interactions Endpoint Url."

At this point, you should be able to execute commands against Sigrun using either the CLI or Discord interactions.

## Interface

Sigrun provides the same interface for controlling server from the command line and from discord. The command line also has an additional interface for managing your discord application, e.g. registering / deleting commands. This allows Sigrun to register itself with your Discord application, and should only need to be done once.

### Command Line

**Server control.** Use `sigrun --help` for CLI documentation.

- `sigrun list-games` - Print the games Sigrun currently supports.
- `sigrun create-server` - Bootstrap a new game server.
- `sigrun server-status` - Get the status and instance IDs of the servers Sigrun is currently managing.
- `sigrun start-server` - Startup an existing game server using its instance ID.
- `sigrun stop-server` - Stop an existing game server using its instance ID.

**Discord control.** Use `sigrun_discord --help` for CLI documentation.

- `sigrun_discord register` -- Automatically register Sigrun's commands with your Discord application.
- `sigrun_discord list` -- List the metadata associated with your Discord applications commands. This will give you command ids.
- `sigrun_discord delete [COMMAND_IDS]` -- Delete a particular Discord command.

## Instance logging

The instance startup script logs to `/var/log/cloud-init-output.log`. The systemd logs can be examined from a logfile or systemd directly. Depending on the startup script, some games may log somewhere under the game root, e.g. `/etc/games/{game}/log/*`. Since every game makes use of systemd to configure auto-start, you can always check the systemd logs: `journalctl -u {game}.service`.

## History

Originally, Sigrun was a little bit over-complicated, running on serverless fargate with async SQS/SNS processing to get around the Discord bot response time requirements. I ditched serverless containers for a simple EC2 server that's provisioned once and then started and stopped. It's simpler, faster, far easier to debug, and cheaper. I also ditched external storage (DDB) for instance metadata in favor of querying EC2 metadata on demand and using tags, which is again far easier and not at risk of becoming inconsistent.
