import argparse
from servode import Servo, ServoGroup, ServoProtocol


def hello_protocol(cli):
    print("[hello_protocol] _begin_")
    # use a with block and a ServoProtocol to enable simple cleanup of protocol
    with ServoProtocol() as sp:
        # to read a value using the protocol directly
        value = sp.read_register(
            servo=cli.servo_id,
            register='present_position'
        )
        print("[hello_protocol] register:'present_position' value:{0}".format(
            value))


def hello_servo(cli):
    print("[hello_servo] _begin_")
    # use a with block and a ServoProtocol to enable simple cleanup of protocol
    with ServoProtocol() as sp:
        # to read a value using a Servo class first instantiate a Servo
        servo = Servo(sp=sp, servo_id=cli.servo_id)
        # then read a value as if you're reading from a dict
        value = servo['present_position']
        print("[hello_servo] register:'present_position' value:{0}".format(
            value))


def hello_group(cli):
    print("[hello_group] _begin_")
    # use a with block and a ServoProtocol to enable simple cleanup of protocol
    with ServoProtocol() as sp:
        # to use an ordered group of servos instantiate a ServoGroup
        sg = ServoGroup()
        sg['base'] = Servo(sp, 1)   # add a servo with ID 1 named 'base'
        sg['elbow'] = Servo(sp, 2)  # add a servo with ID 2 named 'elbow'
        # servos will remain in the order added and they're available by 'key'

        # now write values to one register across the group of servos
        sg.write("goal_position", [
            100,  # first servo value to write to 'goal_position' register
            200,  # second servo value to write to 'goal_position' register
        ])
        print("[hello_group] wrote register:'goal_position' values")


def hsw(cli):
    print("[hello_sync_write] _begin_")
    # use a with block and a ServoProtocol to enable simple cleanup of protocol
    with ServoProtocol() as sp:
        if cli.sid is not None:
            sp.sync_write('torque_enable', 1, servo_list=cli.sid)
            for sid in cli.sid:
                print("[hello_sync_write] read torque_enable:{0}".format(
                    sp.read_register(sid, 'torque_enable')))

            sp.sync_write('torque_enable', 0, servo_list=cli.sid)
            for sid in cli.sid:
                print("[hello_sync_write] read torque_enable:{0}".format(
                    sp.read_register(sid, 'torque_enable')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Servo Protocol implementation and some helper functions',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers()

    hello_proto_parser = subparsers.add_parser(
        'hello_protocol',
        description='Basic example showing direct use of ServoProtocol.')
    hello_proto_parser.add_argument('servo_id', nargs='?', default=1, type=int,
                                    help="The servo_id to read registers.")
    hello_proto_parser.set_defaults(func=hello_protocol)

    hello_servo_parser = subparsers.add_parser(
        'hello_servo',
        description='Basic example showing use of the Servo class.')
    hello_servo_parser.add_argument('servo_id', nargs='?', default=1, type=int,
                                    help="The servo_id to read registers.")
    hello_servo_parser.set_defaults(func=hello_servo)

    hello_group_parser = subparsers.add_parser(
        'hello_group',
        description='Basic example showing use of the Servo Group class.')
    hello_group_parser.set_defaults(func=hello_group)

    hello_sync_write_parser = subparsers.add_parser(
        'hello_sync_write',
        description='Basic example showing use of sync_write operation.')
    hello_sync_write_parser.add_argument(
        '--sid', action='append', type=int,
        help="A servo_id. [one or more arguments]")
    hello_sync_write_parser.set_defaults(func=hsw)

    args = parser.parse_args()
    args.func(args)
