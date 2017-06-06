#!/usr/bin/env python

import math
import time
import logging
import argparse
import threading
import numpy.ma as ma

from decimal import Decimal, ROUND_HALF_UP
from .servo.servode import Servo, ServoGroup, ServoProtocol

from image_processor import ImageProcessor

import ggd_config


log = logging.getLogger('stages')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s|%(name)-8s|%(levelname)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

HOME_BASE = 450
HOME_STRAIGHT = 512
HOME_FEMUR_1 = 520
HOME_FEMUR_2 = 520
HOME_TIBIA = 420
OPEN_EFFECTOR = 500
GRAB_EFFECTOR = 290
POSITION_MARGIN = 75
NO_BOX_FOUND = {'x': None, 'y': None}
MIN_OBJECT_SIZE = 200
MAX_IMAGE_WIDTH = 96
MAX_IMAGE_HEIGHT = 96


def cart2polar(x, y, degrees=True):
    """
    Convert cartesian X and Y to r theta.
    :param x: x cartesian coordinate
    :param y: y cartesian coordinate
    :param degrees: True = return theta in degrees, False = return theta in
        radians
    :return: r, theta
    """
    r = ma.sqrt(x ** 2 + y ** 2)
    theta = ma.arctan2(y, x)
    if degrees:
        theta *= (180 / math.pi)

    return r, theta


def polar2cart(r, theta):
    x = r * ma.cos(theta)
    y = r * ma.sin(theta)
    return x, y


def cartesian_goals(x, y):
    # Convert 2D X and Y into usable numbers
    TwoD_Y_as_Float = float(y)
    TwoD_Y_as_Percent = float(TwoD_Y_as_Float / 100)
    TwoD_X_as_Float = float(x)
    TwoD_X_as_Percent = float(TwoD_X_as_Float / 100)
    # Base maths
    # A - Turn X into a percent
    # B - Multiply X against the total travel of ThreeD_Base
    # C - Take the MAX of ThreeD_Base + B
    threeD_base_max = 780  # Then pad it some (740 + another say 40)
    threeD_base_min = 328  # Then pad it some (288 - another say 40)
    threeD_base_travel = threeD_base_max - threeD_base_min
    bg = int(
        threeD_base_max - (threeD_base_travel * TwoD_X_as_Percent)) - 60
    print("Base goal position is: ", bg)
    # Femur maths
    # A - Turn Y into a percent
    # B - Multiply Y against the total travel of ThreeD_Base
    # C - Take the MAX of ThreeD_Elbow - B
    threeD_femur_max = 451  # Then pad it some (550 + another say 40)
    threeD_femur_min = 363  # Then pad it some (420 - another say 40)
    threeD_femur_travel = threeD_femur_max - threeD_femur_min
    fg = int(
        threeD_femur_max - (threeD_femur_travel * TwoD_Y_as_Percent))
    print("Femur goal position is: ", fg)
    # Tibia maths
    # A - Turn X into a percent
    # B - Multiply X against the total travel of threeD_femur
    # C - Take the MAX of threeD_Elbow + B
    threeD_tibia_max = 420  # Then pad it some (370 + another say 40)
    threeD_tibia_min = 150  # Then pad it some (135 - another say 40)
    threeD_tibia_travel = threeD_tibia_max - threeD_tibia_min
    tg = int(
        threeD_tibia_min + (threeD_tibia_travel * TwoD_Y_as_Percent))
    print("Tibia goal position is: ", tg)
    return bg, fg, tg


def polar_goals(x, y):
    if y < 0:
        raise ValueError("Cannot accept negative Y values.")

    polar_axis = 210
    polar_180_deg = 810
    polar_diff = polar_180_deg - polar_axis

    x_shift = Decimal(MAX_IMAGE_WIDTH / 2).quantize(
        exp=Decimal('1.0'), rounding=ROUND_HALF_UP)
    log.info("[polar_goals] x_shift:{0}".format(x_shift))
    # shift origin of x, y to center of base
    shifted_x = x - x_shift
    log.info("[polar_goals] new_x:{0} new_y:{1}".format(shifted_x, y))

    # horizontal kicker to overcome what we think is parallax
    if 40 < abs(shifted_x) < 10:
        shifted_x *= 1.25
    elif 90 < abs(shifted_x) < 40:
        shifted_x *= 1.40

    # convert shifted x and y to rho and theta
    rho, theta = cart2polar(int(shifted_x), int(y))
    log.info("[polar_goals] r:{0} theta:{1}".format(rho, theta))

    # convert theta into base rotation goal
    bg = int((polar_diff / 180) * theta + polar_axis)
    if bg > polar_180_deg:
        bg = polar_180_deg
    if bg < polar_axis:
        bg = polar_axis

    bg_cart, fg, tg = cartesian_goals(x, y)
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

        # little sleepy motion in the end effector for fun
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

        :param should_run: a threading.Event that tells the stage to continue if
            is_set() is True
        :return: a dict containing this stage's results
        """
        log.info("[stage_home] _begin_")
        stage_results = dict()
        if len(self.sg) is not 5:
            log.error("[stage_hello] Unexpected sg length:{0}".format(
                len(self.sg)))
            return stage_results

        # # start at the middle-out position for all servos
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

        :param should_run: a threading.Event that tells the stage to continue if
            is_set() is True
        :return: a dict containing this stage's results
        """
        log.info("[stage_find] _begin_")
        r = dict()

        ip = ImageProcessor(res_width=MAX_IMAGE_WIDTH,
                            res_height=MAX_IMAGE_HEIGHT)
        ip.capture_frame()

        log.info('[stage_find] max_pixel_count is:{0}'.format(
            ip.max_pixel_count))
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
            log.info("[stage_find] no object larger than:{0}".format(
                MIN_OBJECT_SIZE))
            ip.close()
            log.info("[stage_find] _end_")
            return NO_BOX_FOUND

    def stage_pick(self, should_run=None,
                   cli=None, previous_results=None, cartesian=True):
        """

        :param should_run: a `threading.Event` that tells the stage to continue if
            `is_set()` is True
        :param cli: the cli values to use for the pick
        :param previous_results: a dict containing previous stage results pertinent
            to this stage
        :param cartesian: use cartesian (True) or polar coordinates (False) for
            the pick
        :return: a dict containing this stage's results
        """
        log.info("[stage_pick] _begin_")

        stage_results = dict()
        x = y = 0

        if cli is not None:
            x = cli.x
            y = cli.y
            if cli.polar is not None and cli.polar:
                cartesian = False

        if previous_results is not None:
            x = previous_results['x']
            y = previous_results['y']

        if cartesian:
            # if cartesian:
            log.info("[stage_pick] x:{0} y:{1} cartesian pickup".format(x, y))
            base_goal, femur_goal, tibia_goal = cartesian_goals(x, y)
            log.info("[stage_pick] cart base:{0} femur:{1} tibia:{2}".format(
                base_goal, femur_goal, tibia_goal))
        else:
            log.info("[stage_pick] x:{0} y:{1} polar pickup".format(x, y))
            base_goal, femur_goal, tibia_goal = polar_goals(x, y)
            log.info(
                "[stage_pick] polar base:{0} femur:{1} tibia:{2}".format(
                    base_goal, femur_goal, tibia_goal))

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

        # go to Down Open Pick location
        ######################################################
        self.sg.goal_position([
            base_goal,
            femur_goal,
            femur_goal,
            tibia_goal,
            OPEN_EFFECTOR
        ], block=False, margin=POSITION_MARGIN)
        time.sleep(.5)

        # Go to Grab location
        ######################################################
        self.sg['effector']['goal_position'] = GRAB_EFFECTOR
        time.sleep(.5)

        stage_results['pick_complete'] = True
        log.info("[stage_pick] _end_")

        return stage_results

    def stage_sort(self, should_run=None):
        """

        :param should_run: a threading.Event that tells the stage to continue if
            is_set() is True
        :return: a dict containing this stage's results
        """
        log.info("[stage_sort] _begin_")
        stage_results = dict()

        sort_base = 512
        sort_femur_1 = 280
        sort_femur_2 = 280
        sort_tibia = 675

        if len(self.sg) is not 5:
            log.error("[stage_sort] Unexpected sg length:{0}".format(
                len(self.sg)))
            return stage_results

        self.sg.write_values("moving_speed", [150, 150, 150, 150, 150])
        stage_results['slow_down'] = True

        self.sg.goal_position([
            sort_base,  # first servo value
            HOME_FEMUR_1,  # second servo value
            HOME_FEMUR_2,  # third servo value
            sort_tibia,  # fourth servo value
            GRAB_EFFECTOR  # fifth servo value
        ], block=False, margin=POSITION_MARGIN)
        time.sleep(0.5)
        stage_results['raise_complete'] = True

        # end at the middle-out position for all servos
        self.sg.goal_position([
            sort_base,  # first servo value
            sort_femur_1,  # second servo value
            sort_femur_2,  # third servo value
            sort_tibia,  # fourth servo value
            GRAB_EFFECTOR  # fifth servo value
        ], block=True, margin=POSITION_MARGIN + 15)
        time.sleep(0.5)
        stage_results['reach_complete'] = True

        self.sg['effector']['goal_position'] = OPEN_EFFECTOR
        time.sleep(0.5)

        self.sg.goal_position([
            sort_base,  # first servo value
            sort_femur_1 + 150,  # second servo value
            sort_femur_2 + 150,  # third servo value
            HOME_TIBIA,  # fourth servo value
            OPEN_EFFECTOR  # fifth servo value
        ], block=False, margin=POSITION_MARGIN)

        self.sg.write_values("moving_speed", [200, 200, 200, 200, 200])
        stage_results['slow_down'] = False

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
        description='Sorting Hat Sorting Arm stages - command line interface',
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
                             help="The 'X' coordinate to pickup a box at.")
    pick_parser.add_argument('y', default=0, nargs='?', type=int,
                             help="The 'Y' coordinate to pickup a box at.")
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
        sg['base'] = Servo(sp, ggd_config.arm_servo_ids[0])
        sg['femur01'] = Servo(sp, ggd_config.arm_servo_ids[1])
        sg['femur02'] = Servo(sp, ggd_config.arm_servo_ids[2])
        sg['tibia'] = Servo(sp, ggd_config.arm_servo_ids[3])
        sg['effector'] = Servo(sp, ggd_config.arm_servo_ids[4])

        event = threading.Event()
        event.set()
        res = args.func(sg, event, args)
        print("Stage: {0} result: {1}".format(args.func, res))
