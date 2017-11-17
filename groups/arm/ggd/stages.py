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
This file dictates the specifics of the motion of the arms.

Additionally, this file contains an ArmStages object that is instantiated by the
Greengrass Arm device every time a new stage is to be processed. Additionally, 
this file contains a command-line supporting manual operation and tuning of an 
arm through one stage at a time.
 
Note: At this point in time, tuning of an arm requires modifications to the 
servo values contained in this file.
"""
import math
import time
import logging
import argparse
import threading
import numpy.ma as ma

from decimal import Decimal, ROUND_HALF_UP
from servo.servode import Servo, ServoGroup, ServoProtocol

from image_processor import ImageProcessor
from . import arm_servo_ids

log = logging.getLogger('stages')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s|%(name)-8s|%(levelname)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

HOME_BASE = 450  # servo value of the 'home' position of the base servo
HOME_STRAIGHT = 512  # servo value of the 'straight' position of the base servo
HOME_FEMUR_1 = 520  # value of the 'home' position of the first femur servo
HOME_FEMUR_2 = 520  # value of the 'home' position of the second femur servo
HOME_TIBIA = 420  # servo value of the 'home' position of the tibia
OPEN_EFFECTOR = 500  # servo value of the 'open' position of the end effector
GRAB_EFFECTOR = 290  # servo value of 'grab' position of the end effector
POSITION_MARGIN = 75  # how close does the servo need to get the goal position
NO_BOX_FOUND = {'x': None, 'y': None}
MIN_OBJECT_SIZE = 200  # smallest object to try to pickup
MAX_IMAGE_WIDTH = 96  # used for coordinate calculations and camera constraint
MAX_IMAGE_HEIGHT = 96  # used for coordinate calculations and camera constraint


def cart2polar(x, y, degrees=True):
    """
    Convert cartesian X and Y to polar RHO and THETA.
    :param x: x cartesian coordinate
    :param y: y cartesian coordinate
    :param degrees: True = return theta in degrees, False = return theta in
        radians. [default: True]
    :return: r, theta
    """
    rho = ma.sqrt(x ** 2 + y ** 2)
    theta = ma.arctan2(y, x)
    if degrees:
        theta *= (180 / math.pi)

    return rho, theta


def polar2cart(rho, theta):
    """
    Convert polar coordinates to cartesian coordinated.

    :param rho: polar rho coordinate
    :param theta: polar theta coordinate in degrees
    :return:
    """
    x = rho * ma.cos(theta)
    y = rho * ma.sin(theta)
    return x, y


def cartesian_goals(x, y):
    """
    Use a cartesian coordinate system to calculate goals from given X and Y
    values.

    :param x: x cartesian coordinate
    :param y: y cartesian coordinate
    :return: cartesian derived base, fibia, and tibia servo goal values
    """
    # Convert 2D X and Y into usable numbers
    two_d_y_as_float = float(y)
    two_d_y_as_percent = float(two_d_y_as_float / 100)
    two_d_x_as_float = float(x)
    two_d_x_as_percent = float(two_d_x_as_float / 100)
    # Base maths
    # A - Turn X into a percent
    # B - Multiply X against the total travel of ThreeD_Base
    # C - Take the MAX of ThreeD_Base + B
    three_d_base_max = 780  # Then pad it some (740 + another say 40)
    three_d_base_min = 328  # Then pad it some (288 - another say 40)
    three_d_base_travel = three_d_base_max - three_d_base_min
    bg = int(
        three_d_base_max - (three_d_base_travel * two_d_x_as_percent)) - 60
    logging.info("[cartesian_goals] Base goal position is:{0}".format(bg))
    # Femur maths
    # A - Turn Y into a percent
    # B - Multiply Y against the total travel of ThreeD_Base
    # C - Take the MAX of ThreeD_Elbow - B
    three_d_femur_max = 451  # Then pad it some (550 + another say 40)
    three_d_femur_min = 363  # Then pad it some (420 - another say 40)
    three_d_femur_travel = three_d_femur_max - three_d_femur_min
    fg = int(
        three_d_femur_max - (three_d_femur_travel * two_d_y_as_percent))
    logging.info("[cartesian_goals] Femur goal position is:{0}".format(fg))
    # Tibia maths
    # A - Turn X into a percent
    # B - Multiply X against the total travel of threeD_femur
    # C - Take the MAX of threeD_Elbow + B
    three_d_tibia_max = 420  # Then pad it some (370 + another say 40)
    three_d_tibia_min = 150  # Then pad it some (135 - another say 40)
    three_d_tibia_travel = three_d_tibia_max - three_d_tibia_min
    tg = int(
        three_d_tibia_min + (three_d_tibia_travel * two_d_y_as_percent))
    logging.info("[cartesian_goals] Tibia goal position is:{0}".format(tg))
    return bg, fg, tg


def polar_goals(x, y):
    """
    Use a polar coordinate system to calculate goals from given X and Y
    values.

    :param x: x cartesian coordinate
    :param y: y cartesian coordinate
    :return: polar coordinate derived base, fibia, and tibia servo goal values
    """
    if y < 0:
        raise ValueError("Cannot accept negative Y values.")

    # base servo value which represents 0 degrees. Strongly dependent upon
    # physical construction, servo installation and location of arm
    polar_axis = 210
    polar_180_deg = 810  # base servo value which represents 180 degrees
    polar_diff = polar_180_deg - polar_axis

    x_shift = Decimal(MAX_IMAGE_WIDTH / 2).quantize(
        exp=Decimal('1.0'), rounding=ROUND_HALF_UP)
    log.info("[polar_goals] x_shift:{0}".format(x_shift))
    # shift origin of x, y to center of base
    shifted_x = x - x_shift
    log.info("[polar_goals] new_x:{0} new_y:{1}".format(shifted_x, y))

    # horizontal kicker to overcome what we think is image parallax
    if 40 < abs(shifted_x) < 10:
        shifted_x *= 1.25
    elif 90 < abs(shifted_x) < 40:
        shifted_x *= 1.40

    # convert shifted x and y to rho and theta
    rho, theta = cart2polar(int(shifted_x), int(y))
    log.info("[polar_goals] r:{0} theta:{1}".format(rho, theta))

    # convert theta into base rotation goal
    bg = int((polar_diff / 180) * theta + polar_axis)
    # ensure base goal does not go beyond the 180 or 0 servo rotation boundaries
    if bg > polar_180_deg:
        bg = polar_180_deg
    if bg < polar_axis:
        bg = polar_axis

    bg_cart, fg, tg = cartesian_goals(x, y)
    # Return polar coordinates for base and cartesian for arm goals. We found
    # this combination to work best through experimentation over hours of
    # operation.
    return bg + 20, fg, tg


class ArmStages(object):
    def __init__(self, servo_group):
        super(ArmStages, self).__init__()
        self.sg = servo_group

    def stage_stop(self):
        log.info("[stage_stop] _begin_")

        self.sg.goal_position([
            512,  # first servo value
            500,  # second servo value
            500,  # third servo value
            135,  # fourth servo value
            OPEN_EFFECTOR  # fifth servo value
        ], block=True, margin=POSITION_MARGIN)

        # add little sleepy motion in end effector for fun
        self.sg['effector']['goal_position'] = GRAB_EFFECTOR
        time.sleep(0.4)
        self.sg['effector']['goal_position'] = GRAB_EFFECTOR + 100
        time.sleep(0.4)
        self.sg['effector']['goal_position'] = GRAB_EFFECTOR
        time.sleep(0.4)
        self.sg['effector']['goal_position'] = GRAB_EFFECTOR + 30
        time.sleep(0.4)
        self.sg['effector']['goal_position'] = GRAB_EFFECTOR

        log.info("[stage_stop] _end_")

    def stage_home(self, should_run=None):
        """
        The arm will go to the ready position.

        :param should_run: a `threading.Event` that tells the stage to continue
            if `is_set()` is True
        :return: a dict containing this stage's results
        """
        log.info("[stage_home] _begin_")
        stage_results = dict()
        if len(self.sg) is not 5:
            log.error("[stage_home] Unexpected sg length:{0}".format(
                len(self.sg)))
            return stage_results

        # start at the middle-out position for all servos
        self.sg.goal_position([
            HOME_BASE,  # first servo value
            HOME_FEMUR_1,  # second servo value
            HOME_FEMUR_2,  # third servo value
            HOME_TIBIA,  # fourth servo value
            OPEN_EFFECTOR  # fifth servo value
        ], block=True, margin=POSITION_MARGIN)

        stage_results['reached_home'] = True
        log.info("[stage_home] _end_")
        return stage_results

    def stage_find(self, should_run=None):
        """
        The arm is actively using the end-effector camera to find objects of the
        correct size.

        :param should_run: a `threading.Event` that tells the stage to continue
            if `is_set()` is True
        :return: a dict containing this stage's results
        """
        log.info("[stage_find] _begin_")
        r = dict()

        ip = ImageProcessor(res_width=MAX_IMAGE_WIDTH,
                            res_height=MAX_IMAGE_HEIGHT)
        ip.capture_frame()

        log.info('[stage_find] max_pixel_count is:{0}'.format(
            ip.max_pixel_count))
        # check to see if the image processor found an object that is larger
        # than the minimum object size we want to try to pickup
        if ip.max_pixel_count > MIN_OBJECT_SIZE:
            print('largest object is:{0}'.format(ip.largest_object_id))
            print('largest object X coord is:{0}'.format(ip.largest_X))
            print('largest object Y coord is:{0}'.format(ip.largest_Y))
            r['x'] = ip.largest_X
            r['y'] = ip.largest_Y
            r['filename'] = ip.filename
            log.info("[stage_find] found object at x:{0} y:{1}".format(
                r['x'], r['y']))
            ip.close()
            log.info("[stage_find] _end_")
            return r
        else:
            # did not find an object larger than the minimum size - return
            # NO_BOX_FOUND
            log.info("[stage_find] no object larger than:{0}".format(
                MIN_OBJECT_SIZE))
            ip.close()
            log.info("[stage_find] _end_")
            return NO_BOX_FOUND

    def stage_pick(self, should_run=None,
                   cli=None, previous_results=None, cartesian=True):
        """
        The arm has found an object and will attempt to pick-up that object.

        :param should_run: a `threading.Event` that tells the stage to continue
            if `is_set()` is True
        :param cli: the cli values to use for the pick
        :param previous_results: a dict containing previous stage results
            pertinent to this stage
        :param cartesian: use cartesian (True) or polar coordinates (False) for
            the pick
        :return: a dict containing this stage's results
        """
        log.info("[stage_pick] _begin_")

        stage_results = dict()
        x = y = 0

        # if value is received from the CLI, use that as pickup goal target
        if cli is not None:
            x = cli.x
            y = cli.y
            if cli.polar is not None and cli.polar:
                cartesian = False

        # if value is received from previous results, use as pickup goal target
        if previous_results is not None:
            x = previous_results['x']
            y = previous_results['y']

        if cartesian:
            # use cartesian coordinates to calculate goals
            log.info("[stage_pick] x:{0} y:{1} cartesian pickup".format(x, y))
            base_goal, femur_goal, tibia_goal = cartesian_goals(x, y)
            log.info("[stage_pick] cart base:{0} femur:{1} tibia:{2}".format(
                base_goal, femur_goal, tibia_goal))
        else:
            # use polar coordinates to calculate goals
            log.info("[stage_pick] x:{0} y:{1} polar pickup".format(x, y))
            base_goal, femur_goal, tibia_goal = polar_goals(x, y)
            log.info(
                "[stage_pick] polar base:{0} femur:{1} tibia:{2}".format(
                    base_goal, femur_goal, tibia_goal))

        # ensure there are the expected number of servos in the ServoGroup
        if len(self.sg) is not 5:
            log.error("[stage_pick] Unexpected sg length:{0}".format(
                len(self.sg)))
            return stage_results

        # OPEN EFFECTOR/CLAW
        #####################################################
        self.sg.goal_position([
            HOME_BASE,
            HOME_FEMUR_1,
            HOME_FEMUR_2,
            HOME_TIBIA,
            OPEN_EFFECTOR
        ], block=False, margin=POSITION_MARGIN)
        time.sleep(.5)

        # go to PICK READY location
        ######################################################
        self.sg.goal_position([
            base_goal,
            HOME_FEMUR_1,
            HOME_FEMUR_2,
            HOME_TIBIA,
            OPEN_EFFECTOR
        ], block=False, margin=POSITION_MARGIN)
        time.sleep(.5)

        self.sg.write_values("moving_speed", [140, 140, 140, 140, 140])
        stage_results['slow_down'] = True

        # go to down-most open PICK location
        ######################################################
        self.sg.goal_position([
            base_goal,
            femur_goal,
            femur_goal,
            tibia_goal,
            OPEN_EFFECTOR
        ], block=False, margin=POSITION_MARGIN)
        time.sleep(.5)

        # change effector to the GRAB location
        ######################################################
        self.sg['effector']['goal_position'] = GRAB_EFFECTOR
        time.sleep(.5)

        # TODO: ensure something has been grabbed using torque feedback

        # the pick-up is now complete
        stage_results['pick_complete'] = True
        log.info("[stage_pick] _end_")

        return stage_results

    def stage_sort(self, should_run=None):
        """
        The arm has grabbed an object and will place that object at the sort
        position.

        :param should_run: a `threading.Event` that tells the stage to continue
            if `is_set()` is True
        :return: a dict containing this stage's results
        """
        log.info("[stage_sort] _begin_")
        stage_results = dict()

        sort_base = 512
        sort_femur_1 = 280
        sort_femur_2 = 280
        sort_tibia = 675

        # ensure there are the expected number of servos in the ServoGroup
        if len(self.sg) is not 5:
            log.error("[stage_sort] Unexpected sg length:{0}".format(
                len(self.sg)))
            return stage_results

        # slow down the move speed of all servos to reduce dropped objects
        ######################################################
        self.sg.write_values("moving_speed", [150, 150, 150, 150, 150])
        stage_results['slow_down'] = True

        # go to SORT "high" location
        ######################################################
        self.sg.goal_position([
            sort_base,  # first servo value
            HOME_FEMUR_1,  # second servo value
            HOME_FEMUR_2,  # third servo value
            sort_tibia,  # fourth servo value
            GRAB_EFFECTOR  # fifth servo value
        ], block=False, margin=POSITION_MARGIN)
        time.sleep(0.5)
        stage_results['raise_complete'] = True

        # go to SORT "extended" location
        ######################################################
        self.sg.goal_position([
            sort_base,  # first servo value
            sort_femur_1,  # second servo value
            sort_femur_2,  # third servo value
            sort_tibia,  # fourth servo value
            GRAB_EFFECTOR  # fifth servo value
        ], block=True, margin=POSITION_MARGIN + 15)
        time.sleep(0.5)
        stage_results['reach_complete'] = True

        # open the end effector/claw to drop object
        ######################################################
        self.sg['effector']['goal_position'] = OPEN_EFFECTOR
        time.sleep(0.5)

        # go to SORT "away" location
        ######################################################
        self.sg.goal_position([
            sort_base,  # first servo value
            sort_femur_1 + 150,  # second servo value
            sort_femur_2 + 150,  # third servo value
            HOME_TIBIA,  # fourth servo value
            OPEN_EFFECTOR  # fifth servo value
        ], block=False, margin=POSITION_MARGIN)

        # increase move speed of all servos to normal
        ######################################################
        self.sg.write_values("moving_speed", [200, 200, 200, 200, 200])
        stage_results['slow_down'] = False

        # the sort stage is now complete
        stage_results['sort_complete'] = True
        log.info("[stage_sort] _end_")
        return stage_results


def all_stages(servo_group, should_run, cli=None, previous_results=None):
    arm_stage = ArmStages(servo_group=servo_group)
    home_res = arm_stage.stage_home(should_run=should_run)
    find_res = arm_stage.stage_find(should_run=should_run)
    pick_res = arm_stage.stage_pick(should_run=should_run,
                                    cli=cli, previous_results=find_res)


def cli_home(servo_group, should_run, cli=None, previous_results=None):
    arm_stage = ArmStages(servo_group=servo_group)
    arm_stage.stage_home(should_run)


def cli_find(servo_group, should_run, cli=None, previous_results=None):
    arm_stage = ArmStages(servo_group=servo_group)
    arm_stage.stage_find(should_run)


def cli_pick(servo_group, should_run, cli=None, previous_results=None):
    arm_stage = ArmStages(servo_group=servo_group)
    arm_stage.stage_pick(should_run, cli, previous_results)


def cli_sort(servo_group, should_run, cli=None, previous_results=None):
    arm_stage = ArmStages(servo_group=servo_group)
    arm_stage.stage_sort(should_run)


def cli_stop(servo_group, should_run, cli=None, previous_results=None):
    arm_stage = ArmStages(servo_group=servo_group)
    arm_stage.stage_stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Mini Fulfillment Arm stages - command line interface',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers()

    home_parser = subparsers.add_parser(
        'home',
        description='Tell arm to move to HOME position.')
    home_parser.set_defaults(func=cli_home)

    find_parser = subparsers.add_parser(
        'find',
        description='Tell arm to FIND a box.'
    )
    find_parser.set_defaults(func=cli_find)

    pick_parser = subparsers.add_parser(
        'pick',
        description='Tell arm to PICKup a box.'
    )
    pick_parser.add_argument('x', default=0, nargs='?', type=int,
                             help="The 'X' coordinate to pickup a box.")
    pick_parser.add_argument('y', default=0, nargs='?', type=int,
                             help="The 'Y' coordinate to pickup a box.")
    pick_parser.add_argument('--polar', action='store_true',
                             help="Use polar coordinates to pickup a box.")
    pick_parser.set_defaults(func=cli_pick)

    sort_parser = subparsers.add_parser(
        'sort',
        description='Tell arm to SORT a box.'
    )
    sort_parser.set_defaults(func=cli_sort)

    args = parser.parse_args()

    with ServoProtocol() as sp:
        sg = ServoGroup()
        sg['base'] = Servo(sp, arm_servo_ids[0])
        sg['femur01'] = Servo(sp, arm_servo_ids[1])
        sg['femur02'] = Servo(sp, arm_servo_ids[2])
        sg['tibia'] = Servo(sp, arm_servo_ids[3])
        sg['effector'] = Servo(sp, arm_servo_ids[4])

        event = threading.Event()
        event.set()
        res = args.func(sg, event, args)
        print("Stage: {0} result: {1}".format(args.func, res))
