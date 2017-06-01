#!/usr/bin/env bash

echo "[begin] copying GGC certs"
echo "sudo cp certs/inv_arm-server.crt /greengrass/configuration/certs/server.crt"
sudo cp certs/inv_arm-server.crt /greengrass/configuration/certs/server.crt
echo "sudo cp certs/inv_arm-server-private.key /greengrass/configuration/certs/server.key"
sudo cp certs/inv_arm-server-private.key /greengrass/configuration/certs/server.key
echo "sudo cp certs/cloud*.* /greengrass/configuration/certs"
sudo cp certs/cloud*.* /greengrass/configuration/certs
echo "sudo cp certs/root-ca.pem /greengrass/configuration/certs"
sudo cp certs/root-ca.pem /greengrass/configuration/certs
echo "[end] copying GGC certs"
