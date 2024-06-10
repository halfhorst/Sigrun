#!/bin/bash
echo ">>> Performing one-time Abiotic Factor server setup <<<"

# These are inserted by Python
# They will be standard across games
SERVER_NAME=PYTHON_SERVER_NAME
PASSWORD=PYTHON_PASSWORD

echo ">>> Installing Steam <<<"
sudo add-apt-repository multiverse -y
sudo dpkg --add-architecture i386
sudo apt -q -y update
sudo apt -q -y upgrade
curl -sSL https://get.docker.com | sh

# echo steam steam/question select "I AGREE" | debconf-set-selections && \
#     echo steam steam/license note '' | debconf-set-selections && \
#     DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends \
#       libatomic1 libpulse-dev libpulse0 steamcmd net-tools ca-certificates gosu
# STEAMCMD="/usr/games/steamcmd"

GAME_ROOT="/usr/games/abiotic_factor"
# APP_ID=2857200
# echo "Installing Abiotic Factor under ${GAME_ROOT}"

mkdir -p ${GAME_ROOT} # \
    # && chown -R steam:steam ${GAME_ROOT}

# ${STEAMCMD} +force_install_dir ${GAME_ROOT} \
#                 +login anonymous \
#                 +app_update ${APP_ID} \
#                 +quit

echo ">>> Configuring server startup behavior <<<"

cat <<EOF > ${GAME_ROOT}/compose.yml
services:
  abiotic-server:
    image: "ghcr.io/pleut/abiotic-factor-linux-docker:latest"
    restart: unless-stopped
    volumes:
      - "./gamefiles:/server"
      - "./data:/server/AbioticFactor/Saved"
    environment:
      - MaxServerPlayers=6
      - Port=7777
      - QueryPort=27015
      - ServerPassword=${PASSWORD}
      - SteamServerName=${SERVER_NAME}
      - UsePerfThreads=true
      - NoAsyncLoadingThread=true
      - WorldSaveName=${SERVER_NAME}
      - AutoUpdate=true
    ports:
      - "7777:7777/udp"
      - "27015:27015/udp"
EOF

SERVER_WRAPPER=${GAME_ROOT}/wrapper.sh
cat <<EOF > ${SERVER_WRAPPER}
#!/bin/bash
docker compose up -d
EOF

chmod +x ${SERVER_WRAPPER}

SYSTEMD_SERVICE_FILE="/etc/systemd/system/abiotic_factor.service"
cat <<EOF > ${SYSTEMD_SERVICE_FILE}
[Unit]
Description=Abiotic Factor dedicated server

[Service]
Type=oneshot
ExecStart=${SERVER_WRAPPER}
KillSignal=SIGINT
WorkingDirectory=/usr/games/abiotic_factor
User=root

[Install]
WantedBy=multi-user.target
EOF

chmod +x ${SYSTEMD_SERVICE_FILE}
systemctl daemon-reload
systemctl enable abiotic_factor.service

### Starting the server ###
systemctl start abiotic_factor.service
