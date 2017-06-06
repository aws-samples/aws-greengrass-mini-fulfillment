#!/usr/bin/env bash

cd ..
screen -S belt -h 200 -d -m python -m master.ggd.belt master/cfg.tmp.json --frequency 0.1
screen -S bridge -h 200 -d -m python -m master.ggd.bridge master/cfg.tmp.json
screen -S button -h 200 -d -m python -m master.ggd.button master/cfg.tmp.json box
screen -S heartbeat -h 200 -d -m python -m master.ggd.heartbeat master/cfg.tmp.json
screen -S web -h 200 -d -m python -m master.ggd.web master/cfg.tmp.json
screen -ls
cd master
