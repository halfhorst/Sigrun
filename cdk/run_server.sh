#!/bin/sh

cd ${VALHEIM_DEDICATED_SERVER_DIR}

export templdpath=$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=./linux64:$LD_LIBRARY_PATH

# server/unity seems to be trying to use a UI
export TERM=xterm

mkdir -p ${DATA_MOUNT_ROOT}/valheim

# Tip: Make a local copy of this script to avoid it being overwritten by steam.
# NOTE: Minimum password length is 5 characters & Password cant be in the server name.
# NOTE: You need to make sure the ports 2456-2458 is being forwarded to your server through your local router & firewall.
./valheim_server.x86_64 -batchmode -nographics \
                        -name ${VALHEIM_SERVER_NAME} \
                        -port ${VALHEIM_GAME_PORT} \
                        -world ${VALHEIM_SERVER_NAME} \
                        -password ${VALHEIM_SERVER_PASSWORD} \
                        -savedir ${DATA_MOUNT_ROOT}/valheim \
                        -public 1

# run server in background using job system
# then monitor here and kill?
# try crontab to run periodically?
# https://stackoverflow.com/questions/360201/how-do-i-kill-background-processes-jobs-when-my-shell-script-exits

export LD_LIBRARY_PATH=$templdpath
