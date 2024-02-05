#!/bin/bash

# check if block storage is already mounted
sudo file -s -L /dev/sdf
    # if it prints XFS filesystem then it's 
    # formatted


# Create file system and mount
sudo mkfs -t xfs /dev/sdf
sudo mkdir /games
sudo mount /dev/sdf /games