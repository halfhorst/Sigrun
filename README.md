# Sigrun

Sigrun is a Discord bot that helps you manage dedicated servers for games, like Valheim or 7 Days to Die. It was motivated by money. Specifically, I didn't want to pay for an idle server I was maintaining for my friends. Sigrun is a 'personal' bot, not a public one you can add to your own guild. You need to create a Discord application yourself, for your own server, and run your own instance of the bot on your own AWS account.

Current games supported: Valheim, 7 Days to Die. Adding new games should be as simple as writing a new startup script for them. That was the goal, anyways

**This a personal project and I develop it like one. I don't guarantee mainline is in a working state or any development cadence.**

## TODO
- Error handling AWS calls 
- A watchdog Lambda `cron` to shutdown long-running servers
- Enable game-specific server configuration through `create-server`
- Add command to copy world data to S3 with an expiration date and provid a presigned URL
    - Eliminate EBS entirely?
- Add a connection API to the host

## Getting Started

### Pre-requisites

You need the aws cdk cli, you need python, you need an AWS account with credentials setup. The easiest way to setup credentials is with the aws cli.

### Process

1. Create a discord application in their dev portal. Fill out your own `sigrun.env` with the details from your application and source it.
2. Install this python package however you like. I used poetry.
3. Run `sigrun register`. This will register Sigrun's commands with your application.
4. Add your bot to your server. Use the generated link in the application interface.
5. Deploy the infrastructure with cdk. `cd` into the cdk directory and run `deploy.sh`. This will bundle up the lambda code into an artifact and then deploy everything for you.
    - You may want to create a role distinctly for this bot and use its credentials during this process.
    - You have to do this from a Linux machine so that the site packages (specifically PyNaCl) that are zipped up are compatible with the lambda runtime, because Python isn't actually totally portable
6. Log into the console and grab Sigrun's URL from ApiGateway. Give this to your application as the "Interactions Endpoint Url."

A couple manual quirks still exist. New release coming soon 😉
1. You need to go to your IAM console and give the lambda invocation role full permissions for ECS and DynamoDb and read permissions for VPC.
2. adding the application id to the lambda code.

At this point, you should be able to execute commands against Sigrun using either the CLI or Discord interactions, and start a Valheim server instance.

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

## Design

Originally, the plan for Sigrun was for a persistent bot built from the bottom-up with no Discord wrapper, manually handling the entirety of the discord gateway interaction. That was fun to learn but a huge painbutt. It still exists on a different branch.

The cloud infrastructure was similarly over-complicated at first. It was serverless fargate and async processing using SQS/SNS to get around the Discor bot response time requirements. 

Ultimately, I ditched it for a simple EC2 server that's provisioned once and then started and stopped. It is simpler, faster, far easier to debug, and cheaper. Fargate was pointless. I also ditched external storage for isntance metadata (DDB) in favor of querying servers on demand and storing a little information in tags, which is again far easier with EC2 than Fargate. This was very beneficial because external storage was at risk of becoming inconsistent.

Two things I'd like to do in the future is setup a cloud cron job that shuts down service in case you forget, and an on-instance API that lets me query for information like the number of active users.

## Debugging the instance

The instance startup script logs to `/var/log/cloud-init-output.log`. The systemd logs can be examined from a logfile or systemd directly. Either `cat` the logs at `/etc/games/{game}/log/*` or make systemd do it: `journalctl -u {game}.service`.
