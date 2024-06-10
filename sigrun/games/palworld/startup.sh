#!/bin/bash
echo ">>> Performing one-time Palworld server setup <<<"

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

GAME_ROOT="/usr/games/palworld"
APP_ID=2394010
echo "Installing Palworld under ${GAME_ROOT}"

mkdir -p ${GAME_ROOT} \
    && chown -R steam:steam ${GAME_ROOT}

${STEAMCMD} +force_install_dir ${GAME_ROOT} \
                +login anonymous \
                +app_update ${APP_ID} \
                +quit

echo ">>> Configuring server startup behavior <<<"

mkdir -p ${GAME_ROOT}/log
SERVER_WRAPPER=${GAME_ROOT}/wrapper.sh
cat <<EOF > ${SERVER_WRAPPER}
#!/bin/bash
${STEAMCMD} +force_install_dir ${GAME_ROOT} \
                +login anonymous \
                +app_update ${APP_ID} \
                +quit
${GAME_ROOT}/PalServer.sh
EOF
chmod +x ${SERVER_WRAPPER}

SYSTEMD_SERVICE_FILE="/etc/systemd/system/palworld.service"
cat <<EOF > ${SYSTEMD_SERVICE_FILE}
[Unit]
Description=Palworld dedicated server

[Service]
Type=simple
ExecStart=${SERVER_WRAPPER}
KillSignal=SIGINT
WorkingDirectory=/usr/games/palworld
User=root

[Install]
WantedBy=multi-user.target
EOF

chmod +x ${SYSTEMD_SERVICE_FILE}
systemctl daemon-reload
systemctl enable palworld.service

### Starting the server ###
systemctl start palworld.service