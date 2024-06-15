#!/bin/bash
echo ">>> Performing one-time Factorio server setup <<<"

# These are inserted by Python
# They will be standard across games
SERVER_NAME=PYTHON_SERVER_NAME
PASSWORD=PYTHON_PASSWORD

echo ">>> Setting up directories <<<"

GAME_ROOT="/usr/games/palworld"
mkdir -p ${GAME_ROOT}}
mkdir ${GAME_ROOT}/saves

echo ">>> Configuring server startup behavior <<<"

mkdir -p ${GAME_ROOT}/log
SERVER_WRAPPER=${GAME_ROOT}/wrapper.sh
cat <<EOF > ${SERVER_WRAPPER}
#!/bin/bash
rm -rf ${GAME_ROOT}/factorio
curl -L -o ${GAME_ROOT}/factorio.tar.xz https://factorio.com/get-download/stable/headless/linux64
tar xvf ${GAME_ROOT}/factorio.tar.xz -C ${GAME_ROOT}
rm ${GAME_ROOT}/factorio.tar.xz

if [ ! -f "${GAME_ROOT}/saves/${SERVER_NAME}.zip " ]; then
  ${GAME_ROOT}/factorio/bin/x64/factorio --create ${GAME_ROOT}/saves/${SERVER_NAME}.zip 
fi
${GAME_ROOT}/factorio/bin/x64/factorio --start-server ${GAME_ROOT}/saves/${SERVER_NAME}.zip 
EOF
chmod +x ${SERVER_WRAPPER}

SYSTEMD_SERVICE_FILE="/etc/systemd/system/factorio.service"
cat <<EOF > ${SYSTEMD_SERVICE_FILE}
[Unit]
Description=Factorio dedicated server

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
systemctl enable factorio.service

echo ">>> Starting the server <<<"
systemctl start factorio.service