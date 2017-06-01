#!/usr/bin/env bash

screen -S heartbeat -X at "#" stuff ^C
screen -S arm -X at "#" stuff ^C
echo "all gg devices stopped"