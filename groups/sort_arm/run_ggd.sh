#!/usr/bin/env bash

cd ggd
chmod 755 load_gg_profile.sh
./load_gg_profile.sh

cd ../..
screen -S arm -h 200 -d -m python -m sort_arm.ggd.arm sort_arm/cfg.tmp.json "ggd/certs/sort_arm-server.crt" --frequency 0.1
screen -S heartbeat -h 200 -d -m python -m sort_arm.ggd.heartbeat sort_arm/cfg.tmp.json "ggd/certs/sort_arm-server.crt"
screen -ls