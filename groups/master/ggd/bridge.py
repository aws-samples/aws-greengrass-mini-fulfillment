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
Bridge messages from the arm cores to this core.
"""
import os
import time
import logging
import argparse
import datetime

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

import ggd_config
from mqtt_utils import mqtt_connect
from gg_group_setup import GroupConfigFile

dir_path = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger('bridge')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s|%(name)-8s|%(levelname)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

ggd_name = 'Empty'

mqttc_master = None
mqttc_sort_arm = None
mqttc_inv_arm = None
should_loop = True


def sorting_bridge(client, userdata, message):
    log.debug('[sort_bridge] subscr_topic:{0} msg:{1}'.format(
        message.topic, message.payload))
    mqttc_master.publish("/sort"+message.topic, message.payload, 0)


def inventory_bridge(client, userdata, message):
    log.debug('[inv_bridge] subscr_topic:{0} msg:{1}'.format(
        message.topic, message.payload))
    mqttc_master.publish("/inv"+message.topic, message.payload, 0)


def init_bridge():
    log.info("[bridge] Starting connection to Master Core")
    if mqtt_connect(mqttc_master):
        log.info("[bridge] Connected to Master Core")
    else:
        log.error("[bridge] could not connect to Master/Conveyor Core")

    log.info("[bridge] Starting connection to Sorting Arm Core")
    if mqtt_connect(mqttc_sort_arm):
        for topic in ggd_config.sort_bridge_topics:
            log.info("[bridge] bridging topic:{0}".format(topic))
            mqttc_sort_arm.subscribe(topic, 1, sorting_bridge)
    else:
        log.error("[bridge] could not connect to Sorting Arm Core")

    log.info("[bridge] Starting connection to Inventory Arm Core")
    if mqtt_connect(mqttc_inv_arm):
        for topic in ggd_config.inv_bridge_topics:
            log.info("[bridge] bridging topic:{0}".format(topic))
            mqttc_inv_arm.subscribe(topic, 1, inventory_bridge)
    else:
        log.error("[bridge] could not connect to Inventory Arm Core")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="GGD that subscribes to topics from another GG Core.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--debug', default=False, action='store_true',
                        help="Activate debug output.")
    parser.add_argument('config_file',
                        help="The config file.")

    args = parser.parse_args()
    if args.debug:
        log.setLevel(logging.DEBUG)

    # read the config file
    cfg = GroupConfigFile(args.config_file)
    ggd_name = cfg['devices']['GGD_bridge']['thing_name']

    # create an MQTT client oriented toward the Master Greengrass Core
    mqttc_master = AWSIoTMQTTClient(ggd_name)
    mqttc_master.configureEndpoint(
        ggd_config.master_core_ip, ggd_config.master_core_port)
    mqttc_master.configureCredentials(
        CAFilePath=dir_path + "/certs/master-server.crt",
        KeyPath=dir_path + "/certs/GGD_bridge.private.key",
        CertificatePath=dir_path + "/certs/GGD_bridge.certificate.pem.crt"
    )

    # create an MQTT client oriented toward the Sorting Arm Greengrass Core
    mqttc_sort_arm = AWSIoTMQTTClient(ggd_name)
    mqttc_sort_arm.configureEndpoint(
        ggd_config.sort_arm_ip, ggd_config.sort_arm_port)
    mqttc_sort_arm.configureCredentials(
        CAFilePath=dir_path + "/certs/sort_arm-server.crt",
        KeyPath=dir_path + "/certs/GGD_bridge.private.key",
        CertificatePath=dir_path + "/certs/GGD_bridge.certificate.pem.crt"
    )

    # create an MQTT client oriented toward the Inventory Arm Greengrass Core
    mqttc_inv_arm = AWSIoTMQTTClient(ggd_name)
    mqttc_inv_arm.configureEndpoint(
        ggd_config.inv_arm_ip, ggd_config.inv_arm_port)
    mqttc_inv_arm.configureCredentials(
        CAFilePath=dir_path + "/certs/inv_arm-server.crt",
        KeyPath=dir_path + "/certs/GGD_bridge.private.key",
        CertificatePath=dir_path + "/certs/GGD_bridge.certificate.pem.crt"
    )

    init_bridge()

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
