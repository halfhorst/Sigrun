#!/bin/bash
echo ">>> Performing one-time Valheim server setup <<<"

# These are inserted by Python
# They will be standard across games
SERVER_NAME=PYTHON_SERVER_NAME
PASSWORD=PYTHON_PASSWORD

echo ">>> Installing Steam <<<"
sudo add-apt-repository multiverse -y
sudo dpkg --add-architecture i386
sudo apt -q -y update
sudo apt -q -y upgrade

echo steam steam/question select "I AGREE" | debconf-set-selections && \
    echo steam steam/license note '' | debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends \
      libatomic1 libpulse-dev libpulse0 steamcmd net-tools ca-certificates gosu
STEAMCMD="/usr/games/steamcmd"

GAME_ROOT="/usr/games/valheim"
APP_ID=896660
echo ">>> Installing Valheim under ${GAME_ROOT} <<<"

mkdir -p ${GAME_ROOT} \
    && chown -R steam:steam ${GAME_ROOT}

${STEAMCMD} +force_install_dir ${GAME_ROOT} \
                +login anonymous \
                +app_update ${APP_ID} \
                +quit

echo ">>> Configuring server startup behavior <<<"

cat <<EOF > ${GAME_ROOT}/start_server.sh
#!/bin/bash
export templdpath=\${LD_LIBRARY_PATH}
export LD_LIBRARY_PATH=./linux64:\${LD_LIBRARY_PATH}

${GAME_ROOT}/valheim_server.x86_64 \
    -name ${SERVER_NAME} \
    -port 2456 \
    -world ${SERVER_NAME} \
    -password ${PASSWORD} \
    -logFile ${GAME_ROOT}/log/${SERVER_NAME}.log \
    -savedir ${GAME_ROOT}/server_data \
    -public 0 \
    -batchmode \
    -nographics \
    -crossplay

export LD_LIBRARY_PATH=\${templdpath}
EOF
chmod +x ${GAME_ROOT}/start_server.sh

mkdir -p ${GAME_ROOT}/log
SERVER_WRAPPER=${GAME_ROOT}/wrapper.sh
cat <<EOF > ${SERVER_WRAPPER}
#!/bin/bash
${STEAMCMD} +force_install_dir ${GAME_ROOT} \
                +login anonymous \
                +app_update ${APP_ID} \
                +quit
${GAME_ROOT}/start_server.sh
EOF
chmod +x ${SERVER_WRAPPER}

SYSTEMD_SERVICE_FILE="/etc/systemd/system/valheim.service"
cat <<EOF > ${SYSTEMD_SERVICE_FILE}
[Unit]
Description=Valheim dedicated server

[Service]
Type=simple
ExecStart=${SERVER_WRAPPER}
KillSignal=SIGINT
WorkingDirectory=${GAME_ROOT}
User=root

[Install]
WantedBy=multi-user.target
EOF

chmod +x ${SYSTEMD_SERVICE_FILE}
systemctl daemon-reload
systemctl enable valheim.service

echo ">>> Starting the server <<<"
systemctl start valheim.service