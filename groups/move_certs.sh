#!/usr/bin/env bash

cp master-server*.* master/certs
cp sort_arm-server*.* sort_arm/certs
cp inv_arm-server*.* inv_arm/certs
echo master/ggd/certs inv_arm/ggd/certs sort_arm/ggd/certs | xargs -n 1 cp master-server.crt
echo master/ggd/certs inv_arm/ggd/certs | xargs -n 1 cp inv_arm-server.crt
echo master/ggd/certs sort_arm/ggd/certs | xargs -n 1 cp sort_arm-server.crt
rm master-server*.*
rm sort_arm-server*.*
rm inv_arm-server*.*