#!/usr/bin/env python

from __future__ import print_function

import time
import logging
import datetime
import argparse
import threading
import collections
from .dynamixel_functions import *

__version__ = '0.1.0'

log = logging.getLogger('servode')
log.addHandler(logging.NullHandler())

# Protocol version
PROTOCOL_V = 1  # Set protocol version used with the Dynamixel AX-12

# Default setting
BAUDRATE_PERM = 1000000
BAUDRATE_TEMP = 500000
AX_12_TYPE = 'AX-12'
MX_TYPE = 'MX'
TRUE = 1
FALSE = 0
ON = 1
OFF = 0

# Check which port is being used on your controller
# ex) Windows: "COM1"   Linux: "/dev/ttyUSB0"
DEVICENAME = "/dev/ttyUSB0".encode('utf-8')

COMM_SUCCESS = 0  # Communication Success result value
COMM_TX_FAIL = -1001  # Communication Tx Failed

# Dynamixel control table addresses
dxl_control = {
    "model_number": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 0,
        "comm_bytes": 2,
        "access": "r"
    },
    "firmware_version": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 2,
        "comm_bytes": 1,
        "access": "r"
    },
    "ID": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 3,
        "comm_bytes": 1,
        "access": "rw"
    },
    "baud_rate": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 4,
        "comm_bytes": 1,
        "access": "rw"
    },
    "return_delay": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 5,
        "comm_bytes": 1,
        "access": "rw"
    },
    "cw_angle_limit": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 6,
        "comm_bytes": 2,
        "access": "rw"
    },
    "ccw_angle_limit": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 8,
        "comm_bytes": 2,
        "access": "rw"
    },
    "highest_limit_temperature": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 11,
        "comm_bytes": 1,
        "access": "rw"
    },
    "lowest_limit_voltage": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 12,
        "comm_bytes": 1,
        "access": "rw"
    },
    "highest_limit_voltage": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 13,
        "comm_bytes": 1,
        "access": "rw"
    },
    "max_torque": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 14,
        "comm_bytes": 2,
        "access": "rw"
    },
    "status_return_level": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 16,
        "comm_bytes": 1,
        "access": "rw"
    },
    "alarm_LED": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 17,
        "comm_bytes": 1,
        "access": "rw"
    },
    "alarm_shutdown": {
        "addr_type": "EEPROM",
        "volatile": False,
        "address": 18,
        "comm_bytes": 1,
        "access": "rw"
    },
    "torque_enable": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 24,
        "comm_bytes": 1,
        "access": "rw"
    },
    "LED": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 25,
        "comm_bytes": 1,
        "access": "rw"
    },
    "cw_compliance_margin": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 26,
        "comm_bytes": 1,
        "access": "rw"
    },
    "ccw_compliance_margin": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 27,
        "comm_bytes": 1,
        "access": "rw"
    },
    "cw_compliance_slope": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 28,
        "comm_bytes": 1,
        "access": "rw"
    },
    "ccw_compliance_slope": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 29,
        "comm_bytes": 1,
        "access": "rw"
    },
    "goal_position": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 30,
        "comm_bytes": 2,
        "access": "rw"
    },
    "moving_speed": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 32,
        "comm_bytes": 2,
        "access": "rw"
    },
    "torque_limit": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 34,
        "comm_bytes": 2,
        "access": "rw"
    },
    "present_position": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 36,
        "comm_bytes": 2,
        "access": "r"
    },
    "present_speed": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 38,
        "comm_bytes": 2,
        "access": "r"
    },
    "present_load": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 40,
        "comm_bytes": 2,
        "access": "r"
    },
    "present_voltage": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 42,
        "comm_bytes": 1,
        "access": "r"
    },
    "present_temperature": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 43,
        "comm_bytes": 1,
        "access": "r"
    },
    "registered_instruction": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 44,
        "comm_bytes": 1,
        "access": "r"
    },
    "moving": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 46,
        "comm_bytes": 1,
        "access": "r"
    },
    "lock": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 47,
        "comm_bytes": 1,
        "access": "rw"
    },
    "punch": {
        "addr_type": "RAM",
        "volatile": True,
        "address": 48,
        "comm_bytes": 2,
        "access": "rw"
    }
}


class Servo(object):

    def __init__(self, sp, servo_id=1, read_cache=None):
        """

        :param sp: the ServoProtocol to use with this Servo
        :param servo_id: the ID of the servo on the servo protocol chain
        :param read_cache: a cache in which the latest values read from a
           register will be placed. Each value is stored with key 'register'.
        """
        super(Servo, self).__init__()
        self._wheel_mode = False
        self.enable_torque = True
        self.servo_id = servo_id
        self.sp = sp
        self.read_cache = read_cache
        self._status = {}
        log.debug("[Servo.__init__] read_cache:{0}".format(read_cache))

    def _fill_status(self, result):
        self._status = result
        log.debug("[_fill_status] servo_id:{0} status:{0}".format(
            self.servo_id, self._status))
        return self._status

    def get_status(self, status_value=None):
        if len(self._status) > 0:
            if not status_value:
                return self._status
            else:
                return self._status[status_value]
        else:
            return None

    def wheel_mode(self, enable=True):
        if self._wheel_mode == enable:
            return

        if enable:
            self.write("cw_angle_limit", 0)
            self.write("ccw_angle_limit", 0)
            self._wheel_mode = True
            log.info("[wheel_mode] wrote enable=True registers")
        else:
            self.write("cw_angle_limit", 4)
            self.write("ccw_angle_limit", 42)
            self._wheel_mode = False
            log.info("[wheel_mode] wrote enable=False registers")

    def wheel_speed(self, speed=512, cw=True):
        """
        Set the Servo's wheel speed. If the servo is not in wheel mode it will
        be placed into wheel mode.

        :param speed: value between 0-1023
        :param cw: True > clockwise or False > counter-clockwise
        :return:
        """
        if (0 <= speed <= 1023) is False:
            raise ValueError("Invalid speed value:{0}".format(speed))

        self.wheel_mode()

        set_speed = speed
        if cw is False:
            set_speed = 1024 + speed

        self.sp.write_register(self.servo_id, "moving_speed", set_speed)
        log.info("[wheel_speed] wrote speed value:{0}".format(set_speed))

    def new_id(self, new_id):
        if (0 <= new_id <= 252) is False:
            raise ValueError("Invalid new_id value:{0}".format(new_id))
        self.sp.write_register(self.servo_id, "ID", new_id)
        log.info("[new_id] servo_id:{0} given new_id value:{1}".format(
            self.servo_id, new_id))
        self.servo_id = new_id

    def read(self, register):
        result = self.sp.read_register(self.servo_id, register)
        # self._fill_status(result)
        if self.read_cache is not None:
            self.read_cache[register] = result['value']
        return result['value']

    def write(self, register, value):
        result = self.sp.write_register(self.servo_id, register, value)
        # self._fill_status(result)

    def __getitem__(self, name):
        return self.read(name)

    def __setitem__(self, key, val):
        self.write(key, val)


class ServoGroup(object):
    """
    A Group of Servos that will remain in order while interacting with or
    iterating over them.
    """
    POSITION_MARGIN = 50

    def __init__(self):
        super(ServoGroup, self).__init__()
        self.servos = collections.OrderedDict()
        self._wheel_mode = False

    def __len__(self):
        return len(self.servos)

    def __getitem__(self, name):
        return self.servos[name]

    def __setitem__(self, key, val):
        self.servos[key] = val

    def __iter__(self):
        return iter(self.servos)

    def __repr__(self):
        dictrepr = self.servos.__repr__()
        return '{0}({1})'.format(type(self).__name__, dictrepr)

    def _get_sp(self):
        log.debug("[_get_sp] _begin_")
        sp = None
        for key in self.servos:
            sp = self.servos[key].sp
            break
        return sp

    @property
    def servo_ids(self):
        """
        Get a list of the ids that are in this group.
        :return: the list of ids
        """
        ids = list()
        for key in self.servos:
            ids.append(self.servos[key].servo_id)
        return ids

    def wheel_mode(self, enable=True):
        if self._wheel_mode == enable:
            return

        if enable:
            self.write("cw_angle_limit", 0)
            self.write("ccw_angle_limit", 0)
            self._wheel_mode = True
            log.info("[ServoGroup.wheel_mode] wrote enable=True registers")
        else:
            self.write("cw_angle_limit", 4)
            self.write("ccw_angle_limit", 42)
            self._wheel_mode = False
            log.info("[ServoGroup.wheel_mode] wrote enable=False registers")

    def wheel_speed(self, speed=512, cw=True):
        """
        Set the Servo Group's wheel speed. If the group's servos are not in
        wheel mode they will be placed into wheel mode.

        :param speed: value between 0-1023
        :param cw: True > clockwise or False > counter-clockwise
        :return: None
        """
        if (0 <= speed <= 1023) is False:
            raise ValueError("Invalid speed value:{0}".format(speed))

        if not self._wheel_mode:
            self.wheel_mode()

        set_speed = speed
        if cw is False:
            set_speed = 1024 + speed

        self.write("moving_speed", set_speed)
        log.info("[ServoGroup.wheel_speed] wrote speed value:{0}".format(
            set_speed))

    def write(self, register, value):
        """
        Write the value into the register on all the servos in the group.

        :param register: the register to write
        :param value: the value to write to the register
        :return: True if success, False if not
        """
        log.debug(
            '[ServoGroup.write] register:{0} value:{1} servo count:{2}'.format(
                register, value, len(self)))
        sp = self._get_sp()
        return sp.sync_write(
            register=register,
            value=value,
            servo_list=self.servo_ids
        )

    def write_values(self, register, values):
        """
        Write the list of values to the register on every servo in the
        ServoGroup.
        Note: the length of the values list should equal the length of the
        ServoGroup

        :param register:
        :param values: the list of values to write in servo order
        :return: None
        """
        t = 0
        log.debug(
            '[ServoGroup.write_values] len(self):{0} len(values):{1}'.format(
                len(self), len(values)))

        for servo in self.servos.values():
            if t < min(len(self), len(values)):
                log.info(
                    "[ServoGroup.write_values] servo:{0} values[{1}]:{2}".format(
                        servo, t, values[t]
                    ))
                servo.write(register, values[t])
            else:
                log.warn(
                    "[ServoGroup.write_values] more group members than values.")
            t += 1

    def goal_position(self, goal_positions,
                      block=False,
                      should_run=None,
                      margin=POSITION_MARGIN):
        """

        :param goal_positions: the list of goal position values to write in
            servo order
        :param block: Validate that present_position for each servo is within
            `margin` of the goal position. Block until validation occurs.
        :param should_run: `threading.Event` used to interrupt block if
            necessary, will be cleared when goal position is met.
        :param margin:
        :return:
        """
        log.info("[goal_position] requested positions:{0}".format(
            goal_positions))

        self.write_values('goal_position', goal_positions)

        event = should_run
        if block is True and event is None:
            log.info("[goal_position] using local event")
            event = threading.Event()
            event.clear()
            event.set()

        if block:
            while event.is_set():
                close = dict()
                i = 0
                for servo in self.servos:
                    s = self.servos[servo]
                    pos = s['present_position']
                    goal = goal_positions[i]
                    log.debug(
                        "[goal_position] 'present_position' id:{0} is:{1}".format(
                            s.servo_id, pos))

                    horseshoes = margin + goal
                    hand_grenades = goal - margin
                    if hand_grenades < 0:
                        hand_grenades = 0

                    # we are close enough when servo position is between
                    # horseshoes and hand grenades
                    if horseshoes > pos > hand_grenades:
                        close[servo] = pos
                    i += 1

                if len(close) == len(self.servos):
                    # all servos close when the dict has a value per servo
                    event.clear()

                log.info("[goal_position] actual close positions:{0}".format(
                    close))
                time.sleep(0.5)


class ServoProtocol(object):
    """
    A Pythonic implementation of a ServoProtocol.
    """
    ROBOTIS = 'ROBOTIS'
    ROBOTIS_STATUS = {
        "instr_error":       int('01000000', 2),
        "overload_error":    int('00100000', 2),
        "checksum_error":    int('00010000', 2),
        "range_error":       int('00001000', 2),
        "overheat_error":    int('00000100', 2),
        "angle_limit_error": int('00000010', 2),
        "input_volt_error":  int('00000001', 2)
    }

    def _get_error_status_map(self):
        # only support ROBOTIS, so simply return the ROBOTIS status for now.
        if self.manufacturer == ServoProtocol.ROBOTIS:
            return ServoProtocol.ROBOTIS_STATUS

    def _result_to_status(self, result_packet):
        log.debug("[result_to_status] result_packet:{0}".format(result_packet))
        status = dict()
        status_map = self._get_error_status_map()
        for key in status_map:
            log.debug("[result_to_status] checking result bit:{0}".format(
                status_map[key]))
            if status_map[key] & result_packet:
                status[key] = True
            else:
                status[key] = False
        log.debug("[result_to_status] status:{0}".format(status))
        return status

    def __init__(self, baud_rate=BAUDRATE_PERM, manufacturer=ROBOTIS,
                 servo_type=AX_12_TYPE, protocol_version=PROTOCOL_V,
                 lock=threading.Lock()):
        """

        :param baud_rate:
        :param manufacturer:
        :param servo_type:
        :param protocol_version:
        """
        super(ServoProtocol, self).__init__()
        if servo_type == AX_12_TYPE:
            self.servo_type = servo_type
        else:
            raise NotImplementedError("servo_type:{0} not understood.".format(
                servo_type))
        if protocol_version == PROTOCOL_V:
            self.protocol_version = protocol_version
        else:
            raise NotImplementedError("protocol_version:{0} not supported.".format(
                protocol_version))

        self.lock = lock
        self.baud_rate = baud_rate
        self.manufacturer = manufacturer
        self.port_num = portHandler(DEVICENAME)
        packetHandler()  # Initialize PacketHandler Structs

    def __enter__(self):
        log.debug("[ServoProtocol.__enter__] Connection information")

        # Open port
        if openPort(self.port_num):
            log.debug("[ServoProtocol.__enter__] opened port:{0}".format(
                self.port_num))
        else:
            raise IOError("[ServoProtocol.__enter__] Failed to open the port!")

        # Set port baudrate to PERM
        if setBaudRate(self.port_num, self.baud_rate):
            log.debug("[ServoProtocol.__enter__] Set baud rate to: {0}".format(
                self.baud_rate))
        else:
            log.debug(
                "[ServoProtocol.__enter__] Failed to change the baud rate!")
            return

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        log.debug("[ServoProtocol.__exit__] closing dxl port")
        closePort(self.port_num)
        # self.lock.release()

    def factory_reset(self, servo):
        """

        :param servo: the servo or servo id to have a factory reset
        :return: None
        """
        if isinstance(servo, Servo):
            sid = servo.servo_id
        else:
            sid = servo

        log.debug("[factory_reset] Try reset:{0}".format(sid))
        factoryReset(self.port_num, self.protocol_version, sid, 0x00)
        with self.lock:
            last_result = getLastTxRxResult(
                self.port_num, self.protocol_version)
            if last_result != COMM_SUCCESS:
                log.error("[factory_reset] Aborted")
                printTxRxResult(self.protocol_version, last_result)

            error_result = getLastRxPacketError(
                self.port_num, self.protocol_version)
            if error_result:
                self._result_to_status(error_result)
                printRxPacketError(self.protocol_version, error_result)
                log.error("[factory_reset] Error:{0}".format(error_result))

        # Wait for reset
        log.debug("[factory_reset] Wait for reset...")
        time.sleep(1)
        log.debug("[factory_reset] Reset complete.")

    def ping(self, servo):
        """

        :param servo: the servo or servo id to be pinged
        :return: None
        """
        if isinstance(servo, Servo):
            sid = servo.servo_id
        else:
            sid = servo

        with self.lock:
            dxl_model_number = pingGetModelNum(
                self.port_num, self.protocol_version, sid)

            last_result = getLastTxRxResult(self.port_num,
                                                self.protocol_version)
            if last_result != COMM_SUCCESS:
                printTxRxResult(self.protocol_version, last_result)
                log.error(
                    "[ping] Communication unsuccessful:{0}".format(last_result))

            error_result = getLastRxPacketError(
                self.port_num, self.protocol_version)
            if error_result:
                self._result_to_status(error_result)
                printRxPacketError(self.protocol_version, error_result)
                log.error("[ping] Error:{0}".format(error_result))

        return dxl_model_number

    def read_register(self, servo, register):
        """

        :param servo: a Servo object or an integer servo_id
        :param register: the register from which to read a value
        :return: a dict containing:
            { "value": <the value read from the register>,
              "status": <a dict containing the status bit states>
            }
        """
        value = ''
        result = {
            "value": value,
            "status": {}
        }

        if isinstance(servo, Servo):
            sid = servo.servo_id
        else:
            sid = servo

        with self.lock:
            if dxl_control[register]['comm_bytes'] == 1:
                value = read1ByteTxRx(
                    self.port_num, self.protocol_version, sid,
                    dxl_control[register]['address']
                )
            elif dxl_control[register]['comm_bytes'] == 2:
                value = read2ByteTxRx(
                    self.port_num, self.protocol_version, sid,
                    dxl_control[register]['address']
                )

            last_result = getLastTxRxResult(
                self.port_num, self.protocol_version
            )
            if last_result != COMM_SUCCESS:
                printTxRxResult(self.protocol_version, last_result)
                log.error("[read_register] Comm unsuccessful:{0}".format(
                    last_result))

            # Comms might be successful but we could still be in an error
            # state. So, check for error packet after every read
            error_result = getLastRxPacketError(
                self.port_num, self.protocol_version)
            if error_result:
                result['status'] = self._result_to_status(error_result)
                printRxPacketError(self.protocol_version, error_result)
                log.error("[read_register] Error:{0}".format(error_result))
            else:
                log.debug(
                    "[read_register] error_result:{0}".format(error_result))

        result['value'] = value
        return result

    def bulk_read(self, read_blocks):
        """

        :param read_blocks: a list of dicts in the following format which
        describe which registers to read from which servos.
         { "blocks": [
                { "servo_id": sid, "register": register },
                { "servo_id": sid, "register": register },
                ...
            ]
         }
        :return: new read_blocks dict now with values included.
        { "blocks": [
            { "servo_id": sid, "register": register,
                "value": value, "ts": timestamp },
            { "servo_id": sid, "register": register,
                "value": value, "ts": timestamp },
                ...
            ]
         }
        """
        if self.servo_type == AX_12_TYPE and \
                self.protocol_version == PROTOCOL_V:
            raise NotImplementedError("AX-12 Servos do not support bulk_read.")

        response = {"blocks": []}
        group_num = groupBulkRead(self.port_num, self.protocol_version)
        log.info("[bulk_read] read group_num:{0}".format(group_num))

        for block in read_blocks['blocks']:
            # loop through blocks to add each as a param to the bulk_read group
            sid = block['servo_id']
            register = block['register']
            last_result = groupBulkReadAddParam(
                group_num, sid,
                dxl_control[register]['address'],
                dxl_control[register]['comm_bytes']
            )
            if last_result != 1:
                err = "[bulk_read] add read param fail on servo_id:{0}".format(
                    sid
                )
                log.error(err)
                raise IOError(err)

        groupBulkReadTxRxPacket(group_num)
        ts = datetime.datetime.now().isoformat()

        last_result = getLastTxRxResult(self.port_num,
                                            self.protocol_version)
        if last_result != COMM_SUCCESS:
            printTxRxResult(self.protocol_version, last_result)

        for block in read_blocks['blocks']:
            # loop through each block to see if the bulk result is available
            sid = block['servo_id']
            register = block['register']
            last_result = groupBulkReadIsAvailable(
                group_num, sid,
                dxl_control[register]['address'],
                dxl_control[register]['comm_bytes']
            )
            if last_result != 1:
                err = "[bulk_read] bulk_read not available servo_id:{0}".format(
                    sid
                )
                log.error(err)
                raise IOError(err)

        blocks = list()
        for block in read_blocks['blocks']:
            sid = block['servo_id']
            register = block['register']
            val = groupBulkReadGetData(
                group_num, sid,
                dxl_control[register]['address'],
                dxl_control[register]['comm_bytes']
            )
            blocks.append({
                "servo_id": sid, "register": register,
                "value": val, "ts": ts
            })

        response['blocks'] = blocks
        return response

    def write_register(self, servo, register, value):
        """

        :param servo: a Servo object or an integer servo_id
        :param register: the register from which to read a value
        :param value: the value to write to the register
        :return: a dict containing:
            { "error": <the error, if an error exists>,
              "status": <a dict containing the status bit states>
            }
        """
        result = {"status": {}}

        if isinstance(servo, Servo):
            sid = servo.servo_id
        else:
            sid = servo

        log.debug("[write_register] servo id:{0} reg:'{1}' reg_addr:{2}".format(
            sid, register, dxl_control[register]['address']))

        with self.lock:
            if dxl_control[register]['access'] == "r":
                raise IOError(
                    "register:'{0}' cannot be written".format(register))

            if dxl_control[register]['comm_bytes'] == 1:
                write1ByteTxRx(
                    self.port_num, self.protocol_version, sid,
                    dxl_control[register]['address'], value)
            elif dxl_control[register]['comm_bytes'] == 2:
                write2ByteTxRx(
                    self.port_num, self.protocol_version, sid,
                    dxl_control[register]['address'], value)

            last_result = getLastTxRxResult(
                self.port_num, self.protocol_version
            )
            if last_result != COMM_SUCCESS:
                printTxRxResult(self.protocol_version, last_result)
                log.error("[write_register] Comm unsuccessful:{0}".format(
                    last_result))

            # Comms might be successful but we could still be in an error
            # state. So, check for error packet after every read
            error_result = getLastRxPacketError(
                self.port_num, self.protocol_version)
            if error_result:
                result['status'] = self._result_to_status(error_result)
                printRxPacketError(self.protocol_version, error_result)
                log.error("[write_register] Error:{0}".format(error_result))
            else:
                log.debug(
                    "[write_register] register:'{0}' written".format(register))

        return result

    def sync_write(self, register, value, servo_list):
        """
        Write the same value to the same register, synchronously to every Servo
        in the servo_list.

        :param register:
        :param value:
        :param servo_list:
        :return:
        """
        result = False
        with self.lock:
            group_num = groupSyncWrite(
                self.port_num, self.protocol_version,
                dxl_control[register]['address'],
                dxl_control[register]['comm_bytes']
            )
            log.info("[sync_write] reg:'{0}' value:{1}".format(
                register, value))
            log.info("[sync_write] servo_list:{0}".format(servo_list))

            for servo in servo_list:
                if isinstance(servo, Servo):
                    sid = servo.servo_id
                else:
                    sid = servo

                add_parm = groupSyncWriteAddParam(
                    group_num, sid,
                    value,
                    dxl_control[register]['comm_bytes']
                )

                if add_parm is False:
                    log.error(
                        "[sync_write] ERROR servo_id:{0} add register:{1}", sid)
                    return False
                else:
                    log.debug("[sync_write] added param to sync write")

            groupSyncWriteTxPacket(group_num)

            last_result = getLastTxRxResult(
                self.port_num, self.protocol_version
            )
            if last_result != COMM_SUCCESS:
                printTxRxResult(self.protocol_version, last_result)
                log.error(
                    "[sync_write] Comm unsuccessful:{0}".format(last_result))
            else:
                result = True

        return result


def read_all_servo_registers(cli, servo_type='AX-12'):
    with ServoProtocol(servo_type=servo_type) as sp:
        s = Servo(sp=sp, servo_id=cli.servo_id)
        for register in sorted(dxl_control):
            value = s[register]
            log.info("Registry entry:'{0}' has value: {1}".format(
                register, value))
            stat = s.get_status()
            if stat:
                log.info("Registry entry:'{0}' read has status: {1}".format(
                    register, stat))


def wheel_test(cli):
    with ServoProtocol() as sp:
        s = Servo(sp, servo_id=cli.servo_id)
        s.wheel_mode()
        s.wheel_speed(512)
        time.sleep(15)
        s.wheel_speed(512, cw=False)
        time.sleep(15)
        s.wheel_speed(0)


def blink_led(cli):
    with ServoProtocol() as sp:
        i = 0
        while i < 15:
            s = Servo(sp=sp, servo_id=cli.servo_id)
            s.write("LED", ON)
            time.sleep(1)
            s.write("LED", OFF)
            time.sleep(1)
            i += 1


def read_register(cli):
    log.info("Read register: '{0}'".format(cli.register))
    with ServoProtocol() as sp:
        if cli.sid is None:
            cli.sid = [1]

        for sid in cli.sid:
            # example use of the Servo class to read a register
            s = Servo(sp=sp, servo_id=sid)
            value = s[cli.register]
            log.info("Servo:{0} value:{1}".format(sid, value))
            log.info("Servo:{0} status:{1}".format(sid, s.get_status()))
        # else:
        #     log.info("Servo 'default'")
        #     # example use of the ServoProtocol to read a register
        #     value = sp.read_register(servo=1, register=cli.register)
        # log.info("Servo:{0} value:{1}".format(1, value))


def write_register(cli):
    with ServoProtocol() as sp:
        result = {}
        if cli.sid is None:
            cli.sid = [1]

        for sid in cli.sid:
            s = Servo(sp=sp, servo_id=sid)
            s[cli.register] = cli.value
            log.info("Servo:{0} wrote register:{1} with status:{2}".format(
                sid, cli.register, s.get_status()))
        # else:
        #     log.info("Servo 'default' ID is 1")
        #     result = sp.write_register(
        #         servo=1,
        #         register=cli.register,
        #         value=cli.value
        #     )


def to_goal(cli):
    with ServoProtocol() as sp:
        if cli.sg is not None:
            for servo_goal in cli.sg:
                log.info('Servo goal:{0}'.format(servo_goal))
                s = Servo(sp=sp, servo_id=servo_goal[0])
                s.write('goal_position', servo_goal[1])
        else:
            log.info("Servo: 1 goal: 0")
            s = Servo(sp=sp, servo_id=1)
            s.write('goal_position', 0)


def factory_reset(cli):
    with ServoProtocol() as sp:
        sp.factory_reset(servo=cli.servo_id)


def change_id(cli):
    with ServoProtocol() as sp:
        s = Servo(sp, servo_id=cli.servo_id)
        s.new_id(cli.new_id)


def ping(cli):
    with ServoProtocol() as sp:
        pong = sp.ping(servo=cli.servo_id)
        log.info("Ping result, model_number:{0}".format(pong))


def torque_enable(cli):
    with ServoProtocol() as sp:
        if cli.torque:
            s = Servo(sp=sp, servo_id=cli.servo_id)
            s.write('torque_enable', 1)
        else:
            s = Servo(sp=sp, servo_id=cli.servo_id)
            s.write('torque_enable', 0)

        log.info("Servo:{0} enable torque:{1}".format(
            cli.servo_id, cli.torque))


if __name__ == '__main__':
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s|%(name)-8s|%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(
        description='Servo Protocol implementation and some common functions',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help="Activate debug logging level")

    subparsers = parser.add_subparsers()

    all_registers = subparsers.add_parser(
        'all_registers',
        description='Read all registers from a servo')
    all_registers.add_argument('servo_id', nargs='?', default=1, type=int,
                               help="The servo_id to read registers.")
    all_registers.set_defaults(func=read_all_servo_registers)

    wheel_parser = subparsers.add_parser(
        'wheel_test',
        description='Put the Servo in wheel mode and test comms.')
    wheel_parser.add_argument('servo_id', nargs='?', default=1, type=int,
                              help="The servo_id to use to test wheel mode.")
    wheel_parser.set_defaults(func=wheel_test)

    blink_parser = subparsers.add_parser(
        'blink_led',
        description='Blink the LED of the Servo for 30 seconds.')
    blink_parser.add_argument('servo_id', nargs='?', default=1, type=int,
                              help="The servo_id to use for LED blinking.")
    blink_parser.set_defaults(func=blink_led)

    reset_parser = subparsers.add_parser(
        'factory_reset',
        description='Reset the Servo to factory original settings.')
    reset_parser.add_argument(
        'servo_id', nargs='?', default=1, type=int,
        help="The servo_id to perform a factory reset upon.")
    reset_parser.set_defaults(func=factory_reset)

    change_id_parser = subparsers.add_parser(
        'change_id',
        description='Change the ID of the given Servo to a new ID')
    change_id_parser.add_argument(
        'servo_id', nargs='?', default=1, type=int,
        help="The current servo_id of the Servo to change.")
    change_id_parser.add_argument('new_id', nargs='?', default=1, type=int,
                                  help="The new servo_id.")
    change_id_parser.set_defaults(func=change_id)

    ping_parser = subparsers.add_parser(
        'ping',
        description='Ping the Servo and get model_number.')
    ping_parser.add_argument('servo_id', nargs='?', default=1, type=int,
                             help="The servo_id of the Servo to ping.")
    ping_parser.set_defaults(func=ping)

    torque_enable_parser = subparsers.add_parser(
        'torque_enable',
        description='Set torque enable for the specified servo.'
    )
    torque_enable_parser.add_argument(
        'servo_id', nargs='?', default=1, type=int,
        help='The ID of the Servo to set the torque enable register.')
    torque_enable_parser.add_argument(
        '--enable', dest='torque',
        action='store_true',
        help="Enable toggle_enable")
    torque_enable_parser.add_argument(
        '--disable', dest='torque',
        action='store_false',
        help="Disable torque_enable")
    torque_enable_parser.set_defaults(func=torque_enable, torque=True)

    goal_position_parser = subparsers.add_parser(
        'to_goal', description='Move one or more servos to the goal position.'
    )
    goal_position_parser.add_argument(
        '--sg', nargs=2, type=int, action='append',
        help='Servo ID and goal position. [Ex: --sg <sid> <position>]')
    goal_position_parser.set_defaults(func=to_goal)

    read_register_parser = subparsers.add_parser(
        'read_register',
        description='Read the given register from one or more Servos.')
    read_register_parser.add_argument(
        'register', nargs='?', default='present_position',
        help="The Servo register to read.")
    read_register_parser.add_argument(
        '--sid', action='append', type=int,
        help="A servo_id. [one or more arguments]")
    read_register_parser.set_defaults(func=read_register)

    write_register_parser = subparsers.add_parser(
        'write_register',
        description='Write the value to the register of one or more Servos.')
    write_register_parser.add_argument(
        'register', nargs='?', default='goal_position',
        help="The Servo register to write.")
    write_register_parser.add_argument(
        'value', nargs='?', type=int,
        help="The value to write to the register.")
    write_register_parser.add_argument(
        '--sid', action='append', type=int,
        help="A servo_id. [one or more arguments]")
    write_register_parser.set_defaults(func=write_register)

    args = parser.parse_args()
    if args.debug:
        log.setLevel(logging.DEBUG)

    args.func(args)
