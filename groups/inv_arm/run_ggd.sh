#!/usr/bin/env bash

cd ggd
chmod 755 load_gg_profile.sh
./load_gg_profile.sh

cd ../..
screen -S heartbeat -h 200 -d -m python -m inv_arm.ggd.arm inv_arm/cfg.tmp.json --frequency 0.1
screen -S heartbeat -h 200 -d -m python -m inv_arm.ggd.heartbeat inv_arm/cfg.tmp.json
screen -ls