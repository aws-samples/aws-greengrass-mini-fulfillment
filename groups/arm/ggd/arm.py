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
Greengrass Arm device

This Greengrass device controls the mini-fulfillment center 3D printed robotic 
arm. It accomplishes this using two threads: one thread to control and report 
upon the arm's movement through `stages` and a separate thread to read and 
report upon each of the arm's servo telemetry. 

The control stages that the arm device will execute in order, are:
* `home` - the arm is in or has returned to the ready position
* `find` - the arm is actively using the end-effector camera to find objects of 
    the correct size
* `pick` - the arm has found an object and will attempt to pick-up that object
* `sort` - the arm has grabbed an object and will place that object at the sort 
    position

To act in a coordinated fashion with the other Group's in the 
miniature fulfillment center, this device also subscribes to device shadow in 
the Master Greengrass Group. The commands that are understood from the master 
shadow are:
* `run` - the arm will start executing the stages in order
* `stop` - the arm will cease operation and go to the stop position

This device expects to be launched form a command line. To learn more about that 
command line type: `python arm.py --help`
"""

import os
import json
import time
import requests
import logging
import argparse
import datetime
import threading
import collections
from cachetools import TTLCache
from requests import ConnectionError
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, AWSIoTMQTTShadowClient

from AWSIoTPythonSDK.core.greengrass.discovery.providers import \
    DiscoveryInfoProvider
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, DROP_OLDEST
import utils
from . import arm_servo_ids
from gg_group_setup import GroupConfigFile

from stages import ArmStages, NO_BOX_FOUND
from servo.servode import Servo, ServoProtocol, ServoGroup


dir_path = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger('arm')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s|%(name)-8s|%(levelname)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

commands = ['run', 'stop']

should_loop = True

ggd_name = 'Empty'
cmd_event = threading.Event()
cmd_event.clear()

base_servo_cache = TTLCache(maxsize=32, ttl=120)
femur01_servo_cache = TTLCache(maxsize=32, ttl=120)
femur02_servo_cache = TTLCache(maxsize=32, ttl=120)
tibia_servo_cache = TTLCache(maxsize=32, ttl=120)
eff_servo_cache = TTLCache(maxsize=32, ttl=120)


def shadow_mgr(payload, status, token):
    log.info("[shadow_mgr] shadow payload:{0} token:{1}".format(
        json.dumps(json.loads(payload), sort_keys=True), token))


def initialize(device_name, config_file, root_ca, certificate, private_key,
               group_ca_path):
    global ggd_name

    cfg = GroupConfigFile(config_file)
    local = dict()
    remote = dict()

    # determine heartbeat device's thing name and endpoint for MQTT clients
    ggd_name = cfg['devices'][device_name]['thing_name']
    iot_endpoint = cfg['misc']['iot_endpoint']

    # Discover Greengrass Core
    dip = DiscoveryInfoProvider()
    dip.configureEndpoint(iot_endpoint)
    dip.configureCredentials(
        caPath=root_ca, certPath=certificate, keyPath=private_key
    )
    dip.configureTimeout(10)  # 10 sec
    log.info("Discovery using CA: {0} certificate: {1} prv_key: {2}".format(
        root_ca, certificate, private_key
    ))
    # Now discover the groups in which this device is a member.
    # The arm should only be in two groups. The local and master groups.
    discovered, discovery_info = utils.ggc_discovery(
        ggd_name, dip, retry_count=10, max_groups=2
    )

    # Each group returned has a groupId which can compare to the configured
    # groupId in the config file. If the IDs match, the 'local' Group has been
    # found and therefore local core.
    # If the groupId's do not match, the 'remote' or 'master' group has been
    # found.
    group_list = discovery_info.getAllGroups()
    for g in group_list:
        logging.info("[initialize] group_id:{0}".format(g.groupId))
        if g.groupId == cfg['group']['id']:
            local_cores = g.coreConnectivityInfoList
            local['core'] = local_cores[0]  # just grab first core as local
            local['ca'] = g.caList
        else:
            remote_cores = g.coreConnectivityInfoList
            remote['core'] = remote_cores[0]  # just grab first core as remote
            remote['ca'] = g.caList

    if len(local) > 1 and len(remote) > 1:
        logging.info("[initialize] local_core:{0} remote_core:{1}".format(
            local, remote
        ))
    else:
        raise EnvironmentError("Couldn't find the arm's Cores.")

    # just save one of the group's CAs to use as a CA file later
    local_core_ca_file = utils.save_group_ca(
        local['ca'][0], group_ca_path, local['core'].groupId
    )
    remote_core_ca_file = utils.save_group_ca(
        remote['ca'][0], group_ca_path, remote['core'].groupId
    )

    # Greengrass Cores discovered, now connect to Cores from this Device
    # get a client to send telemetry
    local_mqttc = AWSIoTMQTTClient(ggd_name)
    log.info("[initialize] local gca_file:{0} cert:{1}".format(
        local_core_ca_file, certificate))
    local_mqttc.configureCredentials(
        local_core_ca_file, private_key, certificate
    )
    local_mqttc.configureOfflinePublishQueueing(10, DROP_OLDEST)

    if not utils.mqtt_connect(mqtt_client=local_mqttc, core_info=local['core']):
        raise EnvironmentError("Connection to GG Core MQTT failed.")

    # get a shadow client to receive commands
    master_shadow_client = AWSIoTMQTTShadowClient(ggd_name)
    log.info("[initialize] remote ca_file:{0} cert:{1}".format(
        local_core_ca_file, certificate))
    remote_mqttc = master_shadow_client.getMQTTConnection()
    remote_mqttc.configureCredentials(
        remote_core_ca_file, private_key, certificate
    )

    if not utils.mqtt_connect(mqtt_client=master_shadow_client,
                              core_info=remote['core']):
        raise EnvironmentError("Connection to Master Shadow failed.")

    # create and register the shadow handler on delta topics for commands
    # with a persistent connection to the Master shadow
    master_shadow = master_shadow_client.createShadowHandlerWithName(
        cfg['misc']['master_shadow_name'], True)
    log.info("[initialize] created handler for shadow name: {0}".format(
        cfg['misc']['master_shadow_name']
    ))
    token = master_shadow.shadowGet(shadow_mgr, 5)
    log.info("[initialize] shadowGet() tk:{0}".format(token))

    return local_mqttc, remote_mqttc, master_shadow


def _stage_message(stage, text='', stage_result=None):
    return json.dumps({
        "stage": stage,
        "addl_text": text,
        "stage_result": stage_result,
        "ts": datetime.datetime.now().isoformat(),
        "ggd_id": ggd_name
    })


def _arm_message(servo_group):
    data = []
    for servo in servo_group:
        log.debug("[_arm_message] servo:{0}".format(servo))
        data.append({
            "sensor_id": "arm_servo_id_{0:02d}".format(
                servo_group[servo].servo_id),
            "ts": datetime.datetime.now().isoformat(),
            "present_speed":
                servo_group[servo]['present_speed'],
            "present_position":
                servo_group[servo]['present_position'],
            "present_load":
                servo_group[servo]['present_load'],
            "goal_position":
                servo_group[servo]['goal_position'],
            "moving":
                servo_group[servo]['moving'],
            "present_temperature":
                servo_group[servo]['present_temperature'],
            "torque_limit":
                servo_group[servo]['torque_limit']
        })

    msg = {
        "version": "2017-06-08",
        "data": data,
        "ggad_id": ggd_name
    }
    return msg


class ArmControlThread(threading.Thread):
    """
    Thread that controls interaction with the Servos through assorted stages.
    """
    # TODO move control into Lambda pending being able to access serial port

    def __init__(self, servo_group, event, stage_topic, mqtt_client,
                 master_shadow, args=(), kwargs={}):
        super(ArmControlThread, self).__init__(
            name="arm_control_thread", args=args, kwargs=kwargs
        )
        self.sg = servo_group
        log.debug("[act.__init__] servo_group:{0}".format(self.sg))
        self.cmd_event = event
        self.active_state = 'initialized'
        self.last_state = 'initialized'
        self.control_stages = collections.OrderedDict()
        self.control_stages['home'] = self.home
        self.control_stages['find'] = self.find
        self.control_stages['pick'] = self.pick
        self.control_stages['sort'] = self.sort
        self.stage_topic = stage_topic
        self.mqtt_client = mqtt_client
        self.master_shadow = master_shadow
        self.found_box = None

        self.master_shadow.shadowRegisterDeltaCallback(self.shadow_mgr)
        log.debug("[arm.__init__] shadowRegisterDeltaCallback()")

    def _activate_command(self, cmd):
        """Use the shared `threading.Event` instance to signal a mini
        fulfillment shadow command to the running Control thread.
        """
        self.last_state = self.active_state
        self.active_state = cmd
        log.info("[arm._activate_command] last_state='{0}' state='{1}'".format(
            self.last_state, cmd))

        if self.active_state == 'run':
            log.info("[arm._activate_command] START RUN")
            self.cmd_event.set()
        elif self.active_state == 'stop':
            log.info("[arm._activate_command] STOP")
            self.cmd_event.clear()
        return

    def shadow_mgr(self, payload, status, token):
        """
        Process mini fulfillment shadow commands from the Master shadow.

        :param payload: the shadow payload to process
        :param status: the accepted, rejected, or delta status of the invocation
        :param token: the token used for tracing this shadow request
        :return:
        """
        log.debug("[arm.shadow_mgr] shadow payload:{0}".format(
            json.dumps(json.loads(payload), sort_keys=True)))

        if payload == "REQUEST TIME OUT":
            log.error(
                "[arm.shadow_mgr] shadow 'REQUEST TIME OUT' tk:{0}".format(
                    token))
            return

        shady_vals = json.loads(payload)
        if 'sort_arm_cmd' in shady_vals['state']:
            cmd = shady_vals['state']['sort_arm_cmd']
            if cmd in commands:
                self._activate_command(cmd)

                # acknowledge the desired state is now reported
                self.master_shadow.shadowUpdate(json.dumps({
                    "state": {
                        "reported": {
                            "sort_arm_cmd": cmd}
                    }
                }), self.shadow_mgr, 5)
            else:
                log.warning(
                    "[arm.shadow_mgr] unknown command:{0}".format(cmd))

    def home(self):
        log.debug("[act.home] [begin]")
        arm = ArmStages(self.sg)
        self.mqtt_client.publish(
            self.stage_topic, _stage_message("home", "begin"), 0
        )
        stage_result = arm.stage_home()
        self.mqtt_client.publish(
            self.stage_topic, _stage_message("home", "end", stage_result), 0
        )
        log.debug("[act.home] [end]")
        return stage_result

    def find(self):
        log.debug("[act.find] [begin]")
        arm = ArmStages(self.sg)
        loop = True
        self.found_box = NO_BOX_FOUND
        stage_result = NO_BOX_FOUND
        self.mqtt_client.publish(
            self.stage_topic, _stage_message("find", "begin"), 0
        )
        while self.cmd_event.is_set() and loop is True:
            stage_result = arm.stage_find()
            if stage_result['x'] and stage_result['y']:  # X & Y start as none
                log.info("[act.find] found box:{0}".format(stage_result))
                self.found_box = stage_result
                log.info("[act.find] self.found_box:{0}".format(
                    self.found_box))
                loop = False
            else:
                log.info("[act.find] self.found_box:{0}".format(
                    self.found_box
                ))
                log.info("[act.find] no box:{0}".format(stage_result))
                time.sleep(1)

        # TODO get image upload working with discovery based interaction
        # # upload the image file just before stage complete
        # if 'filename' in stage_result:
        #     filename = stage_result['filename']
        #
        #     url = 'http://' + ggd_config.master_core_ip + ":"
        #     url = url + str(ggd_config.master_core_port) + "/upload"
        #     files = {'file': open(filename, 'rb')}
        #     try:
        #         log.info('[act.find] POST to URL:{0} file:{1}'.format(
        #             url, filename))
        #         r = requests.post(url, files=files)
        #         log.info("[act.find] POST image file response:{0}".format(
        #             r.status_code))
        #     except ConnectionError as ce:
        #         log.error("[act.find] Upload Image connection error:{0}".format(
        #             ce
        #         ))

        self.mqtt_client.publish(
            self.stage_topic, _stage_message("find", "end", stage_result), 0
        )

        log.info("[act.find] outside self.found_box:{0}".format(self.found_box))
        log.debug("[act.find] [end]")
        return stage_result

    def pick(self):
        log.debug("[act.pick] [begin]")
        arm = ArmStages(self.sg)
        self.mqtt_client.publish(
            self.stage_topic, _stage_message("pick", "begin"), 0
        )
        pick_box = self.found_box
        self.found_box = NO_BOX_FOUND
        log.info("[act.pick] pick_box:{0}".format(pick_box))
        log.info("[act.pick] self.found_box:{0}".format(self.found_box))
        stage_result = arm.stage_pick(previous_results=pick_box,
                                      cartesian=False)
        self.mqtt_client.publish(
            self.stage_topic, _stage_message("pick", "end", stage_result), 0
        )
        log.debug("[act.pick] [end]")
        return stage_result

    def sort(self):
        log.debug("[act.sort] [begin]")
        arm = ArmStages(self.sg)
        self.mqtt_client.publish(
            self.stage_topic, _stage_message("sort", "begin"), 0
        )
        stage_result = arm.stage_sort()
        self.mqtt_client.publish(
            self.stage_topic, _stage_message("sort", "end", stage_result), 0
        )
        log.debug("[act.sort] [end]")
        return stage_result

    def emergency_stop_arm(self):
        if self.active_state == 'stopped' or \
                self.active_state == 'initialized':
            return

        if 'present_position' in base_servo_cache:
            stop_positions = [
                base_servo_cache['present_position'],
                femur01_servo_cache['present_position'],
                femur02_servo_cache['present_position'],
                tibia_servo_cache['present_position'],
                eff_servo_cache['present_position']
            ]
            log.info("[emergency_stop_arm] stop_positions:{0}".format(
                stop_positions))
            self.sg.write_values(
                register='goal_position', values=stop_positions)
            self.active_state = 'stopped'
            log.info("[emergency_stop_arm] active_state:{0}".format(
                self.active_state))
        else:
            log.error("[emergency_stop_arm] no 'present_position' cache value")

    def stop_arm(self):
        arm = ArmStages(self.sg)
        if self.active_state == 'stopped' or \
                self.active_state == 'initialized':
            return

        arm.stage_stop()
        self.active_state = 'stopped'
        log.info("[stop_arm] active_state:{0}".format(
            self.active_state))

    def run(self):
        while should_loop:
            for stage in self.control_stages:
                if self.cmd_event.is_set():
                    stage_result = self.control_stages[stage]()
                    log.info("[run] stage:'{0}' res:'{1}'".format(
                        stage, stage_result))
                else:
                    # Here is where the Arm will be stopped
                    self.stop_arm()

            # 1/3rd of a second while iterating on control behavior
            time.sleep(0.3)


class ArmTelemetryThread(threading.Thread):
    """
    The thread that sets up telemetry interaction with the Servos.
    """

    def __init__(self, servo_group, frequency, telemetry_topic,
                 mqtt_client, args=(), kwargs={}):
        super(ArmTelemetryThread, self).__init__(
            name="arm_telemetry_thread", args=args, kwargs=kwargs
        )
        self.sg = servo_group
        self.frequency = frequency
        self.telemetry_topic = telemetry_topic
        self.mqtt_client = mqtt_client
        log.info("[att.__init__] frequency:{0}".format(
            self.frequency))

    def run(self):
        while should_loop:
            msg = _arm_message(self.sg)
            self.mqtt_client.publish(self.telemetry_topic, json.dumps(msg), 0)
            time.sleep(self.frequency)  # sample rate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Arm control and telemetry',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('device_name',
                        help="The arm's GGD device_name stored in config_file.")
    parser.add_argument('config_file',
                        help="The config file.")
    parser.add_argument('root_ca',
                        help="Root CA File Path of Server Certificate.")
    parser.add_argument('certificate',
                        help="File Path of GGD Certificate.")
    parser.add_argument('private_key',
                        help="File Path of GGD Private Key.")
    parser.add_argument('group_ca_path',
                        help="The directory where the discovered Group CA will "
                             "be saved.")
    parser.add_argument('--stage_topic', default='/arm/stages',
                        help="Topic used to communicate arm stage messages.")
    parser.add_argument('--telemetry_topic', default='/arm/telemetry',
                        help="Topic used to communicate arm telemetry.")
    parser.add_argument('--frequency', default=1.0,
                        dest='frequency', type=float,
                        help="Modify the default telemetry sample frequency.")
    parser.add_argument('--debug', default=False, action='store_true',
                        help="Activate debug output.")
    pa = parser.parse_args()
    if pa.debug:
        log.setLevel(logging.DEBUG)
        logging.getLogger('servode').setLevel(logging.DEBUG)

    local_mqtt, remote_mqtt, m_shadow = initialize(
        pa.device_name, pa.config_file, pa.root_ca, pa.certificate,
        pa.private_key, pa.group_ca_path
    )

    with ServoProtocol() as sp:
        for servo_id in arm_servo_ids:
            sp.ping(servo=servo_id)

        sg = ServoGroup()
        sg['base'] = Servo(sp, arm_servo_ids[0], base_servo_cache)
        sg['femur01'] = Servo(sp, arm_servo_ids[1], femur01_servo_cache)
        sg['femur02'] = Servo(sp, arm_servo_ids[2], femur02_servo_cache)
        sg['tibia'] = Servo(sp, arm_servo_ids[3], tibia_servo_cache)
        sg['effector'] = Servo(sp, arm_servo_ids[4], eff_servo_cache)

        # Use same ServoGroup with one read cache because only the telemetry
        # thread reads
        amt = ArmTelemetryThread(
            sg, frequency=pa.frequency, telemetry_topic=pa.telemetry_topic,
            mqtt_client=local_mqtt
        )
        act = ArmControlThread(
            sg, cmd_event, stage_topic=pa.stage_topic,
            mqtt_client=remote_mqtt, master_shadow=m_shadow
        )
        amt.start()
        act.start()

        try:
            start = datetime.datetime.now()
            while should_loop:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("[__main__] KeyboardInterrupt ... setting should_loop=False")
            should_loop = False

        amt.join()
        act.join()

    local_mqtt.disconnect()
    remote_mqtt.disconnect()
    time.sleep(2)
