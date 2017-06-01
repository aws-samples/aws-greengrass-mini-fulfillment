#!/usr/bin/env bash

screen -S belt -X at "#" stuff ^C
screen -S bridge -X at "#" stuff ^C
screen -S button -X at "#" stuff ^C
screen -S heartbeat -X at "#" stuff ^C
screen -S web -X at "#" stuff ^C
echo "all gg devices stopped"