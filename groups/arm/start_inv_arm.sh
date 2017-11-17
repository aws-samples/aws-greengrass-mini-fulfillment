#!/usr/bin/env bash

cd ggd
chmod 755 load_gg_profile.sh
./load_gg_profile.sh

cd ../..
screen -S arm -h 200 -d -m python -m arm.ggd.arm inv_arm_ggd \
~/mini-fulfillment/groups/arm/inv_arm/cfg.json \
~/mini-fulfillment/groups/arm/inv_arm/ggd_certs/root-ca.pem \
~/mini-fulfillment/groups/arm/inv_arm/ggd_certs/inv_arm_ggd.pem \
~/mini-fulfillment/groups/arm/inv_arm/ggd_certs/inv_arm_ggd.prv \
~/mini-fulfillment/groups/arm/inv_arm/ggd_certs
screen -S heartbeat -h 200 -d -m python -m arm.ggd.heartbeat inv_heartbeat_ggd \
~/mini-fulfillment/groups/arm/inv_arm/cfg.json \
~/mini-fulfillment/groups/arm/inv_arm/ggd_certs/root-ca.pem \
~/mini-fulfillment/groups/arm/inv_arm/ggd_certs/inv_heartbeat_ggd.pem \
~/mini-fulfillment/groups/arm/inv_arm/ggd_certs/inv_heartbeat_ggd.prv \
~/mini-fulfillment/groups/arm/inv_arm/ggd_certs
screen -ls