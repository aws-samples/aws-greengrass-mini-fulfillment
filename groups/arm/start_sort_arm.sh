#!/usr/bin/env bash

cd ggd
chmod 755 load_gg_profile.sh
./load_gg_profile.sh

cd ../..
screen -S arm -h 200 -d -m python -m arm.ggd.arm sort_arm_ggd \
~/mini-fulfillment/groups/arm/sort_arm/cfg.json \
~/mini-fulfillment/groups/arm/sort_arm/ggd_certs/root-ca.pem \
~/mini-fulfillment/groups/arm/sort_arm/ggd_certs/sort_arm_ggd.pem \
~/mini-fulfillment/groups/arm/sort_arm/ggd_certs/sort_arm_ggd.prv \
~/mini-fulfillment/groups/arm/sort_arm/ggd_certs
screen -S heartbeat -h 200 -d -m python -m arm.ggd.heartbeat sort_heartbeat_ggd \
~/mini-fulfillment/groups/arm/sort_arm/cfg.json \
~/mini-fulfillment/groups/arm/sort_arm/ggd_certs/root-ca.pem \
~/mini-fulfillment/groups/arm/sort_arm/ggd_certs/sort_heartbeat_ggd.pem \
~/mini-fulfillment/groups/arm/sort_arm/ggd_certs/sort_heartbeat_ggd.prv \
~/mini-fulfillment/groups/arm/sort_arm/ggd_certs
screen -ls