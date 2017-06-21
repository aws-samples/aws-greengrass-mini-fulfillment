#!/usr/bin/env bash

cur_dir=$(pwd)
cd ggd/servo/DynamixelSDK-3.4.3/c/build/linux_sbc
echo "[begin] making Dynamixel SDK library"
make
echo "[end] making Dynamixel SDK library"
cd ${cur_dir}