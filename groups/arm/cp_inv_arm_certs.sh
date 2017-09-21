#!/usr/bin/env bash

echo "[begin] copying Inventory Arm GGC certs"
#echo "sudo cp inv_arm/inv_arm-server.crt /greengrass/configuration/certs/server.crt"
#sudo cp inv_arm/inv_arm-server.crt /greengrass/configuration/certs/server.crt
#echo "sudo cp inv_arm/inv_arm-server-private.key /greengrass/configuration/certs/server.key"
#sudo cp inv_arm/inv_arm-server-private.key /greengrass/configuration/certs/server.key
echo "sudo cp inv_arm/cloud*.* /greengrass/configuration/certs"
sudo cp inv_arm/cloud*.* /greengrass/configuration/certs
echo "sudo cp inv_arm/root-ca.pem /greengrass/configuration/certs"
sudo cp inv_arm/root-ca.pem /greengrass/configuration/certs
echo "[end] copying certs"
