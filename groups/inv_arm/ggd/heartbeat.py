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
# import fire
import random
import socket
import argparse
import datetime
import logging

import ggd_config

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, DROP_OLDEST
from ..group_config import GroupConfigFile

dir_path = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger('heartbeat')
# logging.basicConfig(datefmt='%(asctime)s - %(name)s:%(levelname)s: %(message)s')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s|%(name)-8s|%(levelname)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

GGD_HEARTBEAT_TOPIC = "/heart/beat"


def mqtt_connect(client):
    connected = False
    try:
        client.connect()
        connected = True
    except socket.error as se:
        print("SE:{0}".format(se))
        # TODO add some retry logic
    return connected

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='SH Arm control and telemetry',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('config_file',
                        help="The config file.")

    args = parser.parse_args()
    cfg = GroupConfigFile(args.config_file)

    heartbeat_name = cfg['GGD_heartbeat']['thing_name']
    mqttc = AWSIoTMQTTClient(heartbeat_name)
    # mqttc.configureTlsInsecure(True)
    mqttc.configureEndpoint(ggd_config.inv_arm_ip, ggd_config.inv_arm_port)
    mqttc.configureCredentials(
        CAFilePath=dir_path + "/certs/master-server.crt",
        KeyPath=dir_path + "/certs/GGD_heartbeat.private.key",
        CertificatePath=dir_path + "/certs/GGD_heartbeat.certificate.pem.crt"
    )

    mqttc.configureOfflinePublishQueueing(10, DROP_OLDEST)

    if mqtt_connect(mqttc):
        try:
            start = datetime.datetime.now()
            while True:
                hostname = socket.gethostname()

                now = datetime.datetime.now()
                msg = {
                    "version": "2016-11-01",
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
                mqttc.publish(
                    GGD_HEARTBEAT_TOPIC,
                    json.dumps(msg), 0
                )
                time.sleep(random.random() * 10)

        except KeyboardInterrupt:
            log.info(
                "[__main__] KeyboardInterrupt ... exiting heartbeat")
        mqttc.disconnect()
        time.sleep(2)
    else:
        print("[hb] could not connect successfully via mqtt.")

