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
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, DROP_OLDEST

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

# These are fixed variables to determine which Greengrass Group to use until
# group discovery is improved
SORT_ARM_GROUP_NAME = 'sort_arm'
INV_ARM_GROUP_NAME = 'inv_arm'

mqttc_master = None
should_loop = True

bridged_topics = {
    "arm/#",
    "arm/errors",
    "arm/stages",
    "arm/telemetry"
}


def sorting_bridge(client, userdata, message):
    log.debug('[sort_bridge] subscr_topic:{0} msg:{1}'.format(
        message.topic, message.payload))
    mqttc_master.publish("sort/"+message.topic, message.payload, 0)


def inventory_bridge(client, userdata, message):
    log.debug('[inv_bridge] subscr_topic:{0} msg:{1}'.format(
        message.topic, message.payload))
    mqttc_master.publish("inv/"+message.topic, message.payload, 0)


def initialize(device_name, config_file, root_ca, certificate, private_key,
               group_ca_path):
    # read the config file
    cfg = GroupConfigFile(config_file)

    ggd_name = cfg['devices'][device_name]['thing_name']
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
    discovered, discovery_info = utils.ggc_discovery(
        thing_name=ggd_name, discovery_info_provider=dip, max_groups=3
    )

    local, remote = _find_cores(cfg, discovery_info, iot_endpoint)
    # Save each group's CAs to use as a CA file later
    local_core_ca_file = utils.save_group_ca(
        local['ca'][0], group_ca_path, local['core'].groupId
    )
    for r in remote:
        remote[r]['ca_file'] = utils.save_group_ca(
            remote[r]['ca'][0], group_ca_path, remote[r]['core'].groupId
        )

    # create and connect MQTT client pointed toward the Master Greengrass Core
    mqttc_m = AWSIoTMQTTClient(ggd_name)
    log.info("[initialize] local gca_file:{0} cert:{1}".format(
        local_core_ca_file, certificate))
    mqttc_m.configureCredentials(
        local_core_ca_file, private_key, certificate
    )
    mqttc_m.configureOfflinePublishQueueing(10, DROP_OLDEST)

    log.info("[initialize] Starting connection to Master Core")
    if utils.mqtt_connect(mqtt_client=mqttc_m, core_info=local['core']):
        log.info("[initialize] Connected to Master Core")
    else:
        log.error("[initialize] could not connect to Master Core")

    # create and connect MQTT clients pointed toward the remote Greengrass Cores
    mqttc_list = list()
    for r in remote:
        remote_mqttc = AWSIoTMQTTClient(ggd_name)
        log.info("[initialize] local gca_file:{0} cert:{1}".format(
            r, certificate))
        remote_mqttc.configureCredentials(
            remote[r]['ca_file'], private_key, certificate)
        remote_mqttc.configureOfflinePublishQueueing(10, DROP_OLDEST)
        log.info("[initialize] Starting connection to Remote Core")
        if utils.mqtt_connect(mqtt_client=remote_mqttc,
                              core_info=remote[r]['core']):
            log.info("[initialize] Connected to Remote Core:{0}".format(
                remote[r]['core'].coreThingArn
            ))
            mqttc_list.append(remote_mqttc)
        else:
            log.error(
                "[initialize] could not connect to Remote Core:{0}".format(
                    remote[r]['core'].coreThingArn
            ))

    return mqttc_m, mqttc_list


def _find_cores(cfg, discovery_info, iot_endpoint):
    local = dict()
    remote = dict()
    # Each group returned has a groupId which can compare to the configured
    # groupId in the config file. If the IDs match, the 'local' Group has been
    # found and therefore local core.
    # If the groupId's do not match, the group's name is use to determine the
    # type of group to which the bridge is connecting.
    group_list = discovery_info.getAllGroups()
    region = iot_endpoint.split('.')[2]
    for g in group_list:
        logging.info("[_find_cores] group_id:{0}".format(g.groupId))
        if g.groupId == cfg['group']['id']:
            # found the local core
            local_cores = g.coreConnectivityInfoList
            local['core'] = local_cores[0]  # just grab first core as local
            local['ca'] = g.caList
        else:
            remote_cores = g.coreConnectivityInfoList
            remote[g.groupId] = {
                'core': remote_cores[0],  # just grab first core as remote
                'ca': g.caList
            }

    logging.info("[_find_cores] local_core:{0} remote_cores:{1}".format(
        local, remote
    ))

    if len(local) == 2 and len(remote) == 2:
        return local, remote
    else:
        raise EnvironmentError("Couldn't find the bridge's Cores.")


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
    parser.add_argument('group_ca_path',
                        help="The directory path where the discovered Group CA "
                             "will be saved.")
    parser.add_argument('--debug', default=False, action='store_true',
                        help="Activate debug output.")

    pa = parser.parse_args()
    if pa.debug:
        log.setLevel(logging.DEBUG)

    mqttc_master, remote_mqttc_list = initialize(
        pa.device_name, pa.config_file, pa.root_ca, pa.certificate,
        pa.private_key, pa.group_ca_path
    )

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
    for m in remote_mqttc_list:
        m.disconnect()
        time.sleep(1)
    time.sleep(1)
