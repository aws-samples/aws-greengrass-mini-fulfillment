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

import os
import json
import time
import random
import socket
import argparse
import datetime
import logging

import ggd_config

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, DROP_OLDEST
from utils import mqtt_connect
from gg_group_setup import GroupConfigFile

dir_path = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger('heartbeat')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s|%(name)-8s|%(levelname)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

ggd_ca_file_path = "<invalid_cert>"


def heartbeat(config_file, topic, frequency=3):
    # read the config file
    cfg = GroupConfigFile(config_file)

    # determine heartbeat device's thing name and orient MQTT client to GG Core
    heartbeat_name = cfg['devices']['GGD_heartbeat']['thing_name']
    mqttc = AWSIoTMQTTClient(heartbeat_name)
    mqttc.configureEndpoint(ggd_config.inv_arm_ip, ggd_config.inv_arm_port)
    mqttc.configureCredentials(
        CAFilePath=dir_path + "/" + ggd_ca_file_path,
        KeyPath=dir_path + "/certs/GGD_heartbeat.private.key",
        CertificatePath=dir_path + "/certs/GGD_heartbeat.certificate.pem.crt"
    )

    mqttc.configureOfflinePublishQueueing(10, DROP_OLDEST)

    if mqtt_connect(mqttc):
        # MQTT client has connected to GG Core, start heartbeat messages
        try:
            start = datetime.datetime.now()
            while True:
                hostname = socket.gethostname()

                now = datetime.datetime.now()
                msg = {
                    "version": "2017-07-05",  # YYYY-MM-DD
                    "ggd_id": heartbeat_name,
                    "hostname": hostname,
                    "data": [
                        {
                            "sensor_id": "heartbeat",
                            "ts": now.isoformat(),
                            "duration": str(now - start)
                        }
                    ]
                }
                print("[hb] publishing heartbeat msg: {0}".format(msg))
                mqttc.publish(topic, json.dumps(msg), 0)
                time.sleep(random.random() * 10)

        except KeyboardInterrupt:
            log.info(
                "[__main__] KeyboardInterrupt ... exiting heartbeat")
        mqttc.disconnect()
        time.sleep(2)
    else:
        print("[hb] could not connect successfully via mqtt.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Greengrass device that generates heartbeat messages',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('config_file',
                        help="The config file.")
    parser.add_argument('ca_file_path',
                        help="CA File Path of Server Certificate.")
    parser.add_argument('--topic', default='/heart/beat',
                        help="Topic used to communicate arm telemetry.")

    args = parser.parse_args()
    ggd_ca_file_path = args.ca_file_path
    heartbeat(config_file=args.config_file, topic=args.topic)
