#!/usr/bin/env bash

cd ggd
chmod 755 load_gg_profile.sh
./load_gg_profile.sh

cd ../..
screen -S arm -h 200 -d -m python -m arm.ggd.arm cfg.tmp.json "inv_arm/inv_arm-server.crt" --frequency 0.1
screen -S heartbeat -h 200 -d -m python -m arm.ggd.heartbeat cfg.tmp.json "inv_arm/inv_arm-server.crt"
screen -ls