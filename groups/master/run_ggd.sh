#!/usr/bin/env bash

#cd ggd
#chmod 755 belt.py
#chmod 755 bridge.py
#chmod 755 button.py
#chmod 755 heartbeat.py
#chmod 755 web.py
#
#screen -S belt -h 200 -d -m ./belt.py --frequency 0.1
#screen -S bridge -h 200 -d -m ./bridge.py
#screen -S button -h 200 -d -m ./button.py box
#screen -S heartbeat -h 200 -d -m ./heartbeat.py
#screen -S web -h 200 -d -m ./web.py
#screen -ls

screen -S belt -h 200 -d -m python -m master.ggd.belt master/cfg.tmp.json --frequency 0.1
screen -S bridge -h 200 -d -m python -m master.ggd.bridge master/cfg.tmp.json
screen -S button -h 200 -d -m python -m master.ggd.button master/cfg.tmp.json
screen -S heartbeat -h 200 -d -m python -m master.ggd.heartbeat master/cfg.tmp.json
screen -S web -h 200 -d -m python -m master.ggd.web master/cfg.tmp.json
screen -ls
