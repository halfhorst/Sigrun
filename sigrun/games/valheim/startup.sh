#!/bin/bash
echo ">>> Performing one-time Valheim server setup <<<"

# These are inserted by Python
# They will be standard across games
SERVER_NAME=PYTHON_SERVER_NAME
PASSWORD=PYTHON_PASSWORD

### Install steam ###
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

### Install Valheim ###
VALHEIM_ROOT="/usr/games/valheim"
VALHEIM_APP_ID=896660
echo "Installing Valheim under ${VALHEIM_ROOT}"

mkdir -p ${VALHEIM_ROOT} \
    && chown -R steam:steam ${VALHEIM_ROOT}

${STEAMCMD} +force_install_dir ${VALHEIM_ROOT} \
                +login anonymous \
                +app_update ${VALHEIM_APP_ID} \
                +quit

### Setup startup functionality ###
echo ">>> Configuring server startup behavior <<<"

# mkdir -p ${VALHEIM_ROOT}/log

cat <<EOF > ${VALHEIM_ROOT}/start_server.sh
#!/bin/bash
export templdpath=\${LD_LIBRARY_PATH}
export LD_LIBRARY_PATH=./linux64:\${LD_LIBRARY_PATH}

${VALHEIM_ROOT}/valheim_server.x86_64 \
    -name ${SERVER_NAME} \
    -port 2456 \
    -world ${SERVER_NAME} \
    -password ${PASSWORD} \
    -logFile ${VALHEIM_ROOT}/log/${SERVER_NAME}.log \
    -savedir ${VALHEIM_ROOT}/server_data \
    -public 1 \
    -batchmode \
    -nographics \
    -crossplay

export LD_LIBRARY_PATH=\${templdpath}
EOF
chmod +x ${VALHEIM_ROOT}/start_server.sh

mkdir -p ${VALHEIM_ROOT}/log
SERVER_WRAPPER=${VALHEIM_ROOT}/wrapper.sh
cat <<EOF > ${SERVER_WRAPPER}
#!/bin/bash
${STEAMCMD} +force_install_dir ${VALHEIM_ROOT} \
                +login anonymous \
                +app_update ${VALHEIM_APP_ID} \
                +quit
${VALHEIM_ROOT}/start_server.sh >> ${VALHEIM_ROOT}/log/${SERVER_NAME}.log
EOF
chmod +x ${SERVER_WRAPPER}

SYSTEMD_SERVICE_FILE="/etc/systemd/system/valheim.service"
cat <<EOF > ${SYSTEMD_SERVICE_FILE}
[Unit]
Description=Valheim dedicated server

[Service]
ExecStart=${SERVER_WRAPPER}
Type=simple

[Install]
WantedBy=multi-user.target
EOF

chmod +x ${SYSTEMD_SERVICE_FILE}
systemctl daemon-reload
systemctl enable valheim.service

### Starting the server ###
systemctl start valheim.service