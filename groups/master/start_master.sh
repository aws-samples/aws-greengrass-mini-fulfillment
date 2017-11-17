#!/usr/bin/env bash

master_dir=$(pwd)

cd ggd
chmod 755 load_gg_profile.sh
./load_gg_profile.sh

cd ${master_dir}
cd ..
screen -S belt -h 200 -d -m python \
-m master.ggd.belt belt_ggd \
~/mini-fulfillment/groups/master/cfg.json \
~/mini-fulfillment/groups/master/ggd/certs/root-ca.pem \
~/mini-fulfillment/groups/master/ggd/certs/belt_ggd.pem \
~/mini-fulfillment/groups/master/ggd/certs/belt_ggd.prv \
~/mini-fulfillment/groups/master/ggd/certs
screen -S bridge -h 200 -d -m python -m master.ggd.bridge bridge_ggd \
~/mini-fulfillment/groups/master/cfg.json \
~/mini-fulfillment/groups/master/ggd/certs/root-ca.pem \
~/mini-fulfillment/groups/master/ggd/certs/bridge_ggd.pem \
~/mini-fulfillment/groups/master/ggd/certs/bridge_ggd.prv \
~/mini-fulfillment/groups/master/ggd/certs
screen -S button -h 200 -d -m python \
-m master.ggd.button button_ggd \
~/mini-fulfillment/groups/master/cfg.json \
~/mini-fulfillment/groups/master/ggd/certs/root-ca.pem \
~/mini-fulfillment/groups/master/ggd/certs/button_ggd.pem \
~/mini-fulfillment/groups/master/ggd/certs/button_ggd.prv \
~/mini-fulfillment/groups/master/ggd/certs box
screen -S heartbeat -h 200 -d -m python \
-m master.ggd.heartbeat heartbeat_ggd \
~/mini-fulfillment/groups/master/cfg.json \
~/mini-fulfillment/groups/master/ggd/certs/root-ca.pem \
~/mini-fulfillment/groups/master/ggd/certs/heartbeat_ggd.pem \
~/mini-fulfillment/groups/master/ggd/certs/heartbeat_ggd.prv \
~/mini-fulfillment/groups/master/ggd/certs --frequency 0.1
screen -S web -h 200 -d -m python \
-m master.ggd.web web_ggd \
~/mini-fulfillment/groups/master/cfg.json \
~/mini-fulfillment/groups/master/ggd/certs/root-ca.pem \
~/mini-fulfillment/groups/master/ggd/certs/web_ggd.pem \
~/mini-fulfillment/groups/master/ggd/certs/web_ggd.prv \
~/mini-fulfillment/groups/master/ggd/certs
screen -ls
cd ${master_dir}
