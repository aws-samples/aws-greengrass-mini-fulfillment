#!/usr/bin/env bash

cd ggd
chmod 755 arm.py
chmod 755 heartbeat.py
chmod 755 load_gg_profile.sh

./load_gg_profile.sh
screen -S arm -h 200 -d -m ./arm.py --frequency 0.1
screen -S heartbeat -h 200 -d -m ./heartbeat.py
screen -ls