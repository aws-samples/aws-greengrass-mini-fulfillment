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

from AWSIoTPythonSDK.core.greengrass.discovery.providers import \
    DiscoveryInfoProvider
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# import ggd_config
import utils
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="GGD that subscribes to topics from another GG Core.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('device_name',
                        help="The GGD device_name in the config file.")
    parser.add_argument('config_file',
                        help="The config file.")
    parser.add_argument('root_ca',
                        help="Root CA File Path of Cloud Server Certificate.")
    parser.add_argument('certificate',
                        help="File Path of GGD Certificate.")
    parser.add_argument('private_key',
                        help="File Path of GGD Private Key.")
    parser.add_argument('group_ca_dir',
                        help="The directory where the discovered Group CA will "
                             "be saved.")
    parser.add_argument('--debug', default=False, action='store_true',
                        help="Activate debug output.")

    pa = parser.parse_args()
    if pa.debug:
        log.setLevel(logging.DEBUG)

    # read the config file
    cfg = GroupConfigFile(pa.config_file)
    ggd_name = cfg['devices'][pa.device_name]['thing_name']
    iot_endpoint = cfg['misc']['iot_endpoint']

    # prep for discovery
    dip = DiscoveryInfoProvider()
    dip.configureEndpoint(iot_endpoint)
    dip.configureCredentials(
        caPath=pa.root_ca, certPath=pa.certificate, keyPath=pa.private_key
    )
    dip.configureTimeout(10)  # 10 sec
    logging.info("Discovery using CA:{0} cert:{1} prv_key:{2}".format(
        pa.root_ca, pa.certificate, pa.private_key
    ))

    discovered, discovery_info, group_list, group_ca_file = utils.ggc_discovery(
        thing_name=ggd_name, discovery_info_provider=dip,
        group_ca_path=pa.group_ca_path
    )

    # create an MQTT client oriented toward the Master Greengrass Core
    mqttc_master = AWSIoTMQTTClient(ggd_name)

    # create an MQTT client oriented toward the Sorting Arm Greengrass Core
    mqttc_sort_arm = AWSIoTMQTTClient(ggd_name)

    # create an MQTT client oriented toward the Inventory Arm Greengrass Core
    mqttc_inv_arm = AWSIoTMQTTClient(ggd_name)

    log.info("[bridge] Starting connection to Master Core")
    if utils.mqtt_connect(mqttc_master):
        log.info("[bridge] Connected to Master Core")
    else:
        log.error("[bridge] could not connect to Master/Conveyor Core")

    log.info("[bridge] Starting connection to Sorting Arm Core")
    if utils.mqtt_connect(mqttc_sort_arm):
        for topic in ggd_config.sort_bridge_topics:
            log.info("[bridge] bridging topic:{0}".format(topic))
            mqttc_sort_arm.subscribe(topic, 1, sorting_bridge)
    else:
        log.error("[bridge] could not connect to Sorting Arm Core")

    log.info("[bridge] Starting connection to Inventory Arm Core")
    if utils.mqtt_connect(mqttc_inv_arm):
        for topic in ggd_config.inv_bridge_topics:
            log.info("[bridge] bridging topic:{0}".format(topic))
            mqttc_inv_arm.subscribe(topic, 1, inventory_bridge)
    else:
        log.error("[bridge] could not connect to Inventory Arm Core")

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
