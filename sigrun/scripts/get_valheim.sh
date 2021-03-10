#!/bin/bash

# Set STEAMCMD to path to steamcmd executable
# Set STEAM_LOGIN and STEAM_PASSWORD as environment_variables

valheim_appid=892970
valheim_dedicated_server=896660${STEAMCMD} +login ${STEAM_LOGIN} ${STEAM_PASSWORD} +force_install_dir /home/steam/SteamGames/Valheim +app_update $valheim_appid  +quit
${STEAMCMD} +login ${STEAM_LOGIN} ${STEAM_PASSWORD} +force_install_dir /home/steam/SteamGames/Valheim_dedicated_server +app_update $valheim_dedicated_server +quit
