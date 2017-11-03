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
import argparse
import datetime
import threading
import collections
import logging

from cachetools import TTLCache
from .servo.servode import ServoProtocol, ServoGroup, Servo

import utils

"""
Greengrass Belt device

This Greengrass device controls the mini-fulfillment center conveyor belt. It 
accomplishes this using two threads: one thread to control and report 
upon the belt's movement through `stages` and a separate thread to read and 
report upon the belt's servo telemetry. 

The control stages that this belt device will execute in order, are:
* `roll` - the belt is in the rolling stage

To act in a coordinated fashion with the other Groups in the miniature 
fulfillment center, this device also subscribes to a device shadow in the Master 
Greengrass Group. The commands that are understood from the master 
shadow are:
* `run` - the belt will start the rolling stage
* `stop` - the belt will cease operation and stop

This device expects to be launched form a command line. To learn more about that 
command line type: `python belt.py --help`
"""

dir_path = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger('belt')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s|%(name)-8s|%(levelname)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

BELT_TELEMETRY_TOPIC = "convey/telemetry"
BELT_ERRORS_TOPIC = "convey/errors"
STAGE_TOPIC = "convey/stages"

commands = ['run', 'stop']
belt_ids = [10]  # when there is one conveyor, there is one servo ID
bone_servo_cache = TTLCache(maxsize=32, ttl=120)
should_loop = True
cmd_event = threading.Event()
cmd_event.clear()
ggd_name = 'Empty'


def shadow_mgr(payload, status, token):
    if payload == "REQUEST TIME OUT":
        log.debug(
            "[shadow_mgr] shadow 'REQUEST TIME OUT' tk:{0}".format(
                token))
        return

    log.debug("[shadow_mgr] shadow payload:{0} token:{1}".format(
        json.dumps(json.loads(payload), sort_keys=True), token))


def stage_message(stage, text='', stage_result=None):
    return json.dumps({
        "stage": stage,
        "addl_text": text,
        "stage_result": stage_result,
        "ts": datetime.datetime.now().isoformat(),
        "ggd_id": ggd_name
    })


def belt_message(servo_group):
    data = []
    for servo in servo_group:
        data.append({
            "sensor_id": "belt_id_{0:02d}".format(
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
            "torque_limit":
                servo_group[servo]['torque_limit']
        })

    msg = {
        "version": "2017-07-05",  # YYYY-MM-DD
        "data": data,
        "ggd_id": ggd_name
    }
    log.debug('[belt_message] msg:{0}'.format(msg))
    return msg


class BeltControlThread(threading.Thread):
    """
    The thread that sets up control interaction with the Servos.
    """

    # TODO move control into Lambda
    def __init__(self, servo_group, event, belt_speed, frequency,
                 mqtt_client, master_shadow, args=(), kwargs={}):
        super(BeltControlThread, self).__init__(
            name="belt_control_thread", args=args, kwargs=kwargs
        )
        self.sg = servo_group
        self.rolling = False
        self.cmd_event = event
        self.belt_speed = belt_speed
        self.frequency = frequency
        self.reversed = False
        self.active_state = 'initialized'
        self.last_state = 'initialized'
        self.control_stages = collections.OrderedDict()
        self.control_stages['roll'] = self.roll
        self.mqttc = mqtt_client
        self.master_shadow = master_shadow

        self.master_shadow.shadowRegisterDeltaCallback(self.shadow_mgr)
        log.debug("[bct.__init__] shadowRegisterDeltaCallback()")

    def _activate_command(self, cmd):
        self.last_state = self.active_state
        self.active_state = cmd
        log.info("[bct._activate_command] last_state='{0}' state='{1}'".format(
            self.last_state, cmd))

        if self.active_state == 'run':
            log.info("[bct._activate_command] START RUN")
            self.cmd_event.set()
        elif self.active_state == 'stop':
            log.info("[bct._activate_command] STOP")
            self.cmd_event.clear()

        # acknowledge the desired state is now reported
        self.master_shadow.shadowUpdate(json.dumps({
            "state": {
                "reported": {
                    "convey_cmd": cmd}
            }
        }), self.shadow_mgr, 5)
        return

    def _reverse_roll(self, should_reverse):
        stage_results = dict()
        stage_results['rolling'] = True

        if should_reverse:
            if self.reversed is False:
                self.sg.wheel_speed(self.belt_speed, cw=False)
                self.reversed = True
                self.mqttc.publish(
                    STAGE_TOPIC, stage_message(
                        "roll", 'reversed', stage_results), 0)
                log.info("[bct._reverse_roll] reversed belt")
            else:
                log.debug(
                    "[bct._reverse_roll] should_reverse=True but already reversed")
        else:
            if self.reversed:
                self.sg.wheel_speed(self.belt_speed)
                self.reversed = False
                self.mqttc.publish(
                    STAGE_TOPIC, stage_message(
                        "roll", 'not_reversed', stage_results), 0)
                log.info("[bct._reverse_roll] un-reversed belt")
            else:
                log.debug(
                    "[bct._reverse_roll] should_reverse=False, not reversed")

        # acknowledge the desired state is now reported
        self.master_shadow.shadowUpdate(json.dumps({
            "state": {
                "reported": {
                    "convey_reverse": should_reverse}
            }
        }), self.shadow_mgr, 5)
        return

    def shadow_mgr(self, payload, status, token):
        if payload == "REQUEST TIME OUT":
            log.error(
                "[bct.shadow_mgr] shadow 'REQUEST TIME OUT' tk:{0}".format(
                    token))
            return

        shady_values = json.loads(payload)
        log.debug("[bct.shadow_mgr] shadow payload:{0}".format(
            json.dumps(shady_values, sort_keys=True)))

        if 'convey_cmd' in shady_values['state']:
            cmd = shady_values['state']['convey_cmd']
            if cmd in commands:
                self._activate_command(cmd)
            else:
                log.debug("[bct.shadow_mgr] unknown command:{0}".format(cmd))
        if 'convey_reverse' in shady_values['state']:
            reverse = shady_values['state']['convey_reverse']
            log.info("[bct.shadow_mgr] convey_reverse val:{0}".format(reverse))
            self._reverse_roll(reverse)

    def roll(self):
        """
        The belt is in or should start the rolling stage.
        :return:
        """
        stage_results = dict()
        if self.rolling is False:
            if self.cmd_event.is_set():
                # for ss in self.sg:
                #     self.sg[ss].wheel_mode(True)
                #     self.sg[ss].wheel_speed(WHEEL_SPEED)
                self.sg.wheel_mode()
                self.sg.wheel_speed(self.belt_speed)

                self.rolling = True
                stage_results['rolling'] = True
        else:
            stage_results['rolling'] = True

        # publish stage message to reflect the belt is rolling and not reversed
        self.mqttc.publish(
            STAGE_TOPIC, stage_message(
                "roll", 'not_reversed', stage_results), 0)

        return stage_results

    def stop_belt(self):
        if self.active_state == 'stopped' or self.active_state == 'initialized':
            return

        stage_results = dict()
        self.sg.wheel_mode(False)
        self.active_state = 'stopped'
        log.info("[bct.stop_belt] active_state:{0}".format(self.active_state))

        if self.reversed:
            addl_text = 'reversed'
        else:
            addl_text = 'not_reversed'

        stage_results['rolling'] = self.rolling = False

        # publish stage message to reflect the belt is stopped
        self.mqttc.publish(
            STAGE_TOPIC, stage_message(
                "stop", addl_text, stage_results), 0)

    def run(self):
        while should_loop:
            for stage in self.control_stages:
                if self.cmd_event.is_set():
                    stage_result = self.control_stages[stage]()
                    log.debug("[bct.run] stage:'{0}' res:'{1}'".format(
                        stage, stage_result))
                else:
                    # Here is where the Belt will be stopped
                    self.stop_belt()

            # loop with frequency interval between possible control actions
            time.sleep(self.frequency)


class BeltTelemetryThread(threading.Thread):
    """
    The thread that sets up interaction with the Belt Servos.
    """

    def __init__(self, servo_group, frequency, mqtt_client, args=(), kwargs={}):
        super(BeltTelemetryThread, self).__init__(
            name="belt_telemetry_thread", args=args, kwargs=kwargs
        )
        self.sg = servo_group
        self.frequency = frequency
        self.mqttc = mqtt_client
        log.info("[btt.__init__] frequency:{0}".format(
            self.frequency))

    def run(self):
        while should_loop:
            msg = belt_message(self.sg)
            try:
                self.mqttc.publish(BELT_TELEMETRY_TOPIC, json.dumps(msg), 0)
                time.sleep(self.frequency)  # 0.1 == 10Hz
            except RuntimeError as re:
                log.error("[btt.run] RuntimeError:{0}".format(re))


def operate_belt(cli, mqtt_client, master_shadow):
    global should_loop

    with ServoProtocol() as sproto:
        for servo_id in belt_ids:
            sproto.ping(servo=servo_id)
    with ServoProtocol() as sp:
        sg = ServoGroup()
        sg['bone'] = Servo(sp, belt_ids[0], bone_servo_cache)

        # Use same Group with one read cache because only monitor thread reads
        btt = BeltTelemetryThread(sg,
                                  frequency=cli.control_frequency,
                                  mqtt_client=mqtt_client)
        bct = BeltControlThread(sg, event=cmd_event,
                                belt_speed=cli.speed,
                                frequency=cli.telemetry_frequency,
                                mqtt_client=mqtt_client,
                                master_shadow=master_shadow)

        btt.start()
        bct.start()

        try:
            start = datetime.datetime.now()
            while should_loop:
                time.sleep(0.1)
        except KeyboardInterrupt:
            log.info(
                "[__main__] KeyboardInterrupt ... setting should_loop=False")
            should_loop = False

        btt.join()
        bct.join()

    mqtt_client.disconnect()
    time.sleep(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Conveyor Belt control and telemetry',
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
    parser.add_argument('--control_frequency', default=0.5,
                        dest='control_frequency', type=float,
                        help="Modify the default control frequency.")
    parser.add_argument('--telemetry_frequency', default=1.0,
                        dest='telemetry_frequency', type=float,
                        help="Modify the default telemetry sample frequency.")
    parser.add_argument('--speed', default=950,
                        dest='speed', type=int,
                        help="Modify the default belt speed.")
    parser.add_argument('--debug', default=False, action='store_true',
                        help="Activate debug output.")
    pa = parser.parse_args()
    if pa.debug:
        log.setLevel(logging.DEBUG)

    client, shadow_client, mshadow, ggd_name = utils.local_core_shadow_connect(
        device_name=pa.device_name,
        config_file=pa.config_file,
        root_ca=pa.root_ca, certificate=pa.certificate,
        private_key=pa.private_key, group_ca_dir=pa.group_ca_dir
    )

    token = mshadow.shadowGet(shadow_mgr, 5)
    logging.debug("[core_connect] shadowGet() tk:{0}".format(token))

    operate_belt(cli=pa, mqtt_client=client, master_shadow=mshadow)
