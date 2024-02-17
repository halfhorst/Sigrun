#!/bin/bash
echo "Setting up Seven Days to Die"

sudo add-apt-repository multiverse -y
sudo dpkg --add-architecture i386
sudo apt -q -y update
# sudo apt upgrade -y
echo steam steam/question select "I AGREE" | debconf-set-selections && \
    echo steam steam/license note '' | debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends \
      libatomic1 libpulse-dev libpulse0 steamcmd net-tools ca-certificates gosu
