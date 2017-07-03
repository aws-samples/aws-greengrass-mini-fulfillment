#!/usr/bin/env bash

cp master-server*.* master/certs
cp sort_arm-server*.* arm/sort_arm
cp inv_arm-server*.* arm/inv_arm
echo master/ggd/certs arm/inv_arm/ggd_certs arm/sort_arm/ggd_certs | xargs -n 1 cp master-server.crt
echo master/ggd/certs arm/inv_arm/ggd_certs | xargs -n 1 cp inv_arm-server.crt
echo master/ggd/certs arm/sort_arm/ggd_certs | xargs -n 1 cp sort_arm-server.crt
rm master-server*.*
rm sort_arm-server*.*
rm inv_arm-server*.*