#!/usr/bin/env bash

echo "[begin] copying Inventory Arm GGC certs"
echo "sudo cp inv_arm/inv_arm-core.pem /greengrass/certs"
sudo cp inv_arm/inv_arm-core.pem /greengrass/certs
echo "sudo cp inv_arm/inv_arm-core.prv /greengrass/certs"
sudo cp inv_arm/inv_arm-core.prv /greengrass/certs
echo "sudo cp inv_arm/root-ca.pem /greengrass/certs"
sudo cp inv_arm/root-ca.pem /greengrass/certs
echo "[end] copying certs"
