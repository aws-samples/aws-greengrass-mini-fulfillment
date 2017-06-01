#!/usr/bin/env python

# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not
# use this file except in compliance with the License. A copy of the License is
# located at
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

"""
Bridge messages from the sorting_arm core to this core.
"""

import json
import time
import logging
import argparse
import datetime

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

import ggd_config
from mqtt_utils import mqtt_connect

log = logging.getLogger('bridge')
# logging.basicConfig(datefmt='%(asctime)s - %(name)s:%(levelname)s: %(message)s')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s|%(name)-8s|%(levelname)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

GGD_NAME = "GGD_bridge"
# GGC_THING_NAME = 'Core'

mqttc_master = AWSIoTMQTTClient(GGD_NAME)
mqttc_master.configureTlsInsecure(True)
mqttc_master.configureEndpoint(
    ggd_config.master_core_ip, ggd_config.master_core_port)
mqttc_master.configureCredentials(
    CAFilePath="certs/master-server.crt",
    KeyPath="certs/GGD_bridge.private.key",
    CertificatePath="certs/GGD_bridge.certificate.pem.crt"
)

mqttc_sort_arm = AWSIoTMQTTClient(GGD_NAME)
mqttc_sort_arm.configureTlsInsecure(True)
mqttc_sort_arm.configureEndpoint(ggd_config.sort_arm_ip, ggd_config.sort_arm_port)
mqttc_sort_arm.configureCredentials(
    CAFilePath="certs/sort_arm-server.crt",
    KeyPath="certs/GGD_bridge.private.key",
    CertificatePath="certs/GGD_bridge.certificate.pem.crt"
)

mqttc_inv_arm = AWSIoTMQTTClient(GGD_NAME)
mqttc_inv_arm.configureTlsInsecure(True)
mqttc_inv_arm.configureEndpoint(ggd_config.inv_arm_ip, ggd_config.inv_arm_port)
mqttc_inv_arm.configureCredentials(
    CAFilePath="certs/inv_arm-server.crt",
    KeyPath="certs/GGD_bridge.private.key",
    CertificatePath="certs/GGD_bridge.certificate.pem.crt"
)

should_loop = True


def sorting_bridge(client, userdata, message):
    log.debug('[sort_bridge] subscr_topic:{0} msg:{1}'.format(
        message.topic, message.payload))
    mqttc_master.publish(message.topic, message.payload, 0)


def inventory_bridge(client, userdata, message):
    log.debug('[inv_bridge] subscr_topic:{0} msg:{1}'.format(
        message.topic, message.payload))
    mqttc_master.publish(message.topic, message.payload, 0)


def init():
    log.info("[bridge] Starting connection to Master/Conveyor Core")
    if mqtt_connect(mqttc_master):
        log.info("[bridge] Connected to Master/Conveyor Core")
    else:
        log.info("[bridge] could not connect to Master/Conveyor Core")

    log.info("[bridge] Starting connection to Sorting Arm Core")
    if mqtt_connect(mqttc_sort_arm):
        for topic in ggd_config.sort_bridge_topics:
            log.info("[bridge] bridging topic:{0}".format(topic))
            mqttc_sort_arm.subscribe(topic, 1, sorting_bridge)
    else:
        log.info("[bridge] could not connect to Sorting Arm Core")

    log.info("[bridge] Starting connection to Inventory Arm Core")
    if mqtt_connect(mqttc_inv_arm):
        for topic in ggd_config.inv_bridge_topics:
            log.info("[bridge] bridging topic:{0}".format(topic))
            mqttc_inv_arm.subscribe(topic, 1, inventory_bridge)
    else:
        log.info("[bridge] could not connect to Inventory Arm Core")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="GGD that subscribes to topics from another GG Core.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--debug', default=False, action='store_true',
                        help="Activate debug output.")
    args = parser.parse_args()
    if args.debug:
        log.setLevel(logging.DEBUG)

    init()

    try:
        start = datetime.datetime.now()
        while should_loop:
            time.sleep(0.1)
    except KeyboardInterrupt:
        log.info(
            "[__main__] KeyboardInterrupt ... setting should_loop=False")
        should_loop = False

    mqttc_master.disconnect()
    time.sleep(1)
    mqttc_sort_arm.disconnect()
    time.sleep(1)
    mqttc_inv_arm.disconnect()
    time.sleep(1)
