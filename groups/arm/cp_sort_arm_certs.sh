#!/usr/bin/env bash

echo "[begin] copying Sort Arm GGC certs"
echo "sudo cp sort_arm/sort_arm-server.crt /greengrass/configuration/certs/server.crt"
sudo cp sort_arm/sort_arm-server.crt /greengrass/configuration/certs/server.crt
echo "sudo cp sort_arm/sort_arm-server-private.key /greengrass/configuration/certs/server.key"
sudo cp sort_arm/sort_arm-server-private.key /greengrass/configuration/certs/server.key
echo "sudo cp sort_arm/cloud*.* /greengrass/configuration/certs"
sudo cp sort_arm/cloud*.* /greengrass/configuration/certs
echo "sudo cp sort_arm/root-ca.pem /greengrass/configuration/certs"
sudo cp sort_arm/root-ca.pem /greengrass/configuration/certs
echo "[end] copying certs"
