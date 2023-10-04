# Sigrun

Sigrun is a Discord bot that helps you manage a Valheim server instance. It was motivated by money. Specifically, I didn't want to pay for an idle server I was maintaining for my friends. Sigrun is a 'personal' bot, not a public one you can add to your own guild. You need to create a Discord application yourself, for your own server, and run your own instance of the bot.

**This a personal project and I develop it like one. I may break it without warning or do other unruly things.**

## TODO

- Explore provisioning an ec2 instance and just triggering start/stop
  - use cheaper EBS in this case
- Fix "already initiated bug"
  - attempting to start a server twice is indistinguishable from the bot correctly
    checking in on the status of an instance it started
- Add command to copy world data to S3 with an expiration date and provid a presigned URL
- Avoid writing ephemeral data to DDB and just query it on demand
- Add a connection API to the host
- Explore a service discovery url

## Getting Started

### Pre-requisites

You need the aws cdk cli, you need python, and you need Docker. You also need an AWS account and a credential setup. The easiest way to do that is with the aws cli.

### Process

1. Create a discord application in their dev portal. Fill out your own `sigrun.env` with the details from your application and source it.
2. Install this python package however you like. I used poetry.
3. Run `sigrun register`. This will register Sigrun's commands with your application.
4. Add your bot to your server. Use the generated link in the application interface.
5. Deploy the infrastructure with cdk. `cd` into the cdk directory and run `deploy.sh`. This will bundle up the lambda code into an artifact and then deploy everything for you.
    - You may want to create a role distinctly for this bot and use its credentials during this process.
6. Log into the console and grab Sigrun's URL from ApiGateway. Give this to your application as the "Interactions Endpoint Url."

A couple manual quirks still exist. New release coming soon 😉
1. You need to go to your IAM console and give the lambda invocation role full permissions for ECS and DynamoDb and read permissions for VPC.
2. adding the application id to the lambda code.

At this point, you should be able to execute commands against Sigrun using either the CLI or Discord interactions, and start a Valheim server instance.

## Interface

### Command Line

Use `sigrun --help` for command line documentation. The available commands are:

* `delete`: Delete a registered command from your application. This is just for dev convenience.
* `list`: List the commands registered to your application. This is just for dev convenience.
* `register`: Register all of Sigrun's commands with your application.
* `server-status`: Get the Valheim server's status and hardware usage.
* `start-server`: Shut the Valheim server down.
* `stop-server`: Start the Valheim server up.

### Discord Interactions

`server-status`, `start-server`, and `stop-server` are the interactions available to the Discord application. They are identical to the CLI commands.

## TODO
- Figure out fargate permissions in CDK
- monitor and report active connections.
- move application id from lambda handler into a secret
- implement the watchdog container for auto-shutdown.

## Design

Originally, the plan for Sigrun was for a persistent bot built from the bottom-up with no Discord wrapper, manually handling the entirety of the discord gateway interaction. That was fun to learn but a huge painbutt. It still exists on a different branch.

That design was overhauled in favor of something that works _now_ instead of something that is a fun project. The new bot is all serverless. It uses a Lambda function to handle all the Discord interactions (the interactions endpoint is rad) and a Fargate service to run the actual game server, with an elastic file system providing persistence. This means each game amounts to a Dockerfile that executes a server, and it should be relatively easy to add more. In short, you tell Sigrun you want to start a server and the Lambda function starts a fargate task of the correct family. The code is not game-agnostic at this point but it was written with that (mostly) in mind. Taking the final step should be minimal work. Server information is dumped into a record in DynamoDb and manipulated on startup/shutdown. Server information is read from these records and mixed with live fargate data to determine currently running worlds and their IP addresses. I found DynamoDb to be much easier than mounting and dealing with server data in EFS (Lambda in VPC == no boto3 for free), and I think it will scale to new features better, too.

A clear enhancement of this setup is to start a sidecar container that monitors connections to the game server container and automatically shuts down the fargate task when no one is connected. The existing infrastructure I've seen do that uses a load balancer for monitoring connections. I eschewed a load balancer for cost, so I'd have to find another way.

```
                                               Sigrun
                                             ┌─Stack ─┐                    ┌─World─Server─Stack────────┐
                                             │        │                    │                           │
                       ┌───────┐          ┌──┴────────┴────────────────────┴───────────────────────────┴─┐
                       │       │ Endpoint │                                                              │
                       │       │ Based    │  ┌─API────┐                    ┌─────────────┐ ┌───────────┐ │
                       │       │ Bot      │  │ Gateway│                    │ ECS/Fargate │ │Elastic    │ │
                       │   D   └──────────┼──►        │                    │             │ │File       │ │
                       │       ◄──────────┼──┐        │   server-status    │ ┌─Valheim─┐ │ │System     │ │
                       │   I   │          │  └─────▲┌─┘ ┌─stop-server──────┴─► Server  │ │ │           │ │
   ┌─Discord─┐         │       │          │        ││   │                    │ Task    │ │ ├───────────┤ │
   │ User    │Slash Cmd│   S   │          │  ANY / ││   │             ┌────┬─►         │===│ Persistent│ │
   │         ├─────────►       │          │        ││   │             │    │ └─▲───────┘ │ │ Game Data │ │
   │         │         │   C   │          │  ┌─────┘▼─┐ │             │    │   │Monitor  │ └───────────┘ │
   │         ◄─────────┤       │          │  │        ├─┘             │    │   │& Kill   │               │
   │         │ Response│   O   │          │  Lambda   │   ┌────┐  ┌───┴──┐ │   │         │               │
   └─────────┘         │       │          │  │        ├───► SQS├──►Lambda│ │ ┌─┴───────┐ │               │
                       │   R   │          │  └───▲────┘   └────┘  └───┬──┘ │ │Watchdog │ │               │
                       │       │          │      │                    │    │ │Task     │ │               │
                       │   D   │          │      └────start-server────┘    │ └─────────┘ │               │
                       │       │          │                                │             │               │
                       │       │          │          async to meet         └─────────────┘               │
                       │       │          │          Discord response                                    │
                       │       │          │          deadline                                            │
                       └───────┘          └──────────────────────────────────────────────────────────────┘
```
