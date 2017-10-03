#!/usr/bin/env bash

echo "[begin] copying Sort Arm GGC certs"
echo "sudo cp sort_arm/sort_arm-core.pem /greengrass/certs"
sudo cp sort_arm/sort_arm-core.pem /greengrass/certs
echo "sudo cp sort_arm/sort_arm-core.prv /greengrass/certs"
sudo cp sort_arm/sort_arm-core.prv /greengrass/certs
echo "sudo cp sort_arm/root-ca.pem /greengrass/configuration/certs"
sudo cp sort_arm/root-ca.pem /greengrass/certs
echo "[end] copying certs"
