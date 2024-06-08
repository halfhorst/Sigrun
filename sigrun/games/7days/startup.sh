#!/bin/bash
echo ">>> Performing one-time Seven Days to Die setup <<<"

# These are inserted by Python
# They will be standard across games
SERVER_NAME=PYTHON_SERVER_NAME
PASSWORD=PYTHON_PASSWORD

echo ">>> Installing Steam <<<"
sudo add-apt-repository multiverse -y
sudo dpkg --add-architecture i386
sudo apt -q -y update
sudo apt -q -y upgrade

# For server config manipulation
sudo apt -q -y install xmlstarlet

echo steam steam/question select "I AGREE" | debconf-set-selections && \
    echo steam steam/license note '' | debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends \
      libatomic1 libpulse-dev libpulse0 steamcmd net-tools ca-certificates gosu
STEAMCMD="/usr/games/steamcmd"

echo "Installing 7 Days to Die under ${SEVEN_DAYS_ROOT}"
GAME_ROOT="/usr/games/sevendaystodie"
APP_ID=294420

mkdir -p ${GAME_ROOT} \
    && chown -R steam:steam ${GAME_ROOT}

${STEAMCMD} +force_install_dir ${GAME_ROOT} \
            +login anonymous \
            +app_update ${APP_ID} \
            +quit

echo ">>> Configuring server behavior <<<"
xmlstarlet ed -L -u "//property[@name='ServerName']/@value" -v "${SERVER_NAME}" serverconfig.xml
xmlstarlet ed -L -u "//property[@name='ServerPassword']/@value" -v "${SERVER_PASSWORD}" serverconfig.xml
xmlstarlet ed -L -u "//property[@name='XPMultiplier']/@value" -v "150" serverconfig.xml
xmlstarlet ed -L -u "//property[@name='PlayerKillingMode']/@value" -v "0" serverconfig.xml

echo ">>> Configuring server startup behavior <<<"
SERVER_WRAPPER=${GAME_ROOT}/wrapper.sh
cat <<EOF > ${SERVER_WRAPPER}
#!/bin/bash
${STEAMCMD} +force_install_dir ${GAME_ROOT} \
                +login anonymous \
                +app_update ${APP_ID} \
                +quit
${GAME_ROOT}/startserver.sh -configfile=${GAME_ROOT}/serverconfig.xml
EOF
chmod +x ${SERVER_WRAPPER}

SYSTEMD_SERVICE_FILE="/etc/systemd/system/sevendaystodie.service"
cat <<EOF > ${SYSTEMD_SERVICE_FILE}
[Unit]
Description=7 Days to Die dedicated server

[Service]
Type=simple
ExecStart=${SERVER_WRAPPER}
KillSignal=SIGINT
WorkingDirectory=/usr/games/sevendaystodie
User=root

[Install]
WantedBy=multi-user.target
EOF

chmod +x ${SYSTEMD_SERVICE_FILE}
systemctl daemon-reload
systemctl enable sevendaystodie.service

### Starting the server ###
systemctl start sevendaystodie.service