#!/bin/bash
echo ">>> Performing initial Valheim setup <<<"

VALHEIM_DEDICATED_SERVER_DIR="/valheim"
VALHEIM_DEDICATED_SERVER_APP_ID=896660
STEAMCMD="/usr/games/steamcmd"

sudo add-apt-repository multiverse -y
sudo dpkg --add-architecture i386
sudo apt -q -y update

echo steam steam/question select "I AGREE" | debconf-set-selections && \
    echo steam steam/license note '' | debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends \
      libatomic1 libpulse-dev libpulse0 steamcmd net-tools ca-certificates gosu

# addgroup --gid 1000 steam && \
#     adduser --system --home /home/steam --shell /bin/false --uid 1000 --gid 1000 steam

mkdir -p ${VALHEIM_DEDICATED_SERVER_DIR} \
    && chown -R steam:steam ${VALHEIM_DEDICATED_SERVER_DIR}

${STEAMCMD} +force_install_dir ${VALHEIM_DEDICATED_SERVER_DIR} \
                +login anonymous \
                +app_update ${VALHEIM_DEDICATED_SERVER_APP_ID} \
                +quit


START_SERVER="
echo \"Inside the server script!\"
"
echo $START_SERVER > ${VALHEIM_DEDICATED_SERVER_DIR}/start_server.sh
chmod +x ${VALHEIM_DEDICATED_SERVER_DIR}/start_server.sh

mkdir -p ${VALHEIM_DEDICATED_SERVER_DIR}/log
echo "${VALHEIM_DEDICATED_SERVER_DIR}/start_server.sh >> ${VALHEIM_DEDICATED_SERVER_DIR}/log/valheim.log 2>&1" >> /etc/rc.local
chmod +x /etc/rc.local
