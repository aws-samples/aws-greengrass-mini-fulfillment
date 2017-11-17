#!/usr/bin/env bash

python -m servo.servode ping 20
python -m servo.servode write_register torque_enable 1 --sid 20
python -m servo.servode write_register torque_enable 1 --sid 21
python -m servo.servode write_register torque_enable 1 --sid 22
python -m servo.servode write_register torque_enable 1 --sid 23
python -m servo.servode write_register torque_enable 1 --sid 24
python -m servo.servode write_register torque_limit 1023 --sid 20
python -m servo.servode write_register torque_limit 1023 --sid 21
python -m servo.servode write_register torque_limit 1023 --sid 22
python -m servo.servode write_register torque_limit 1023 --sid 23
python -m servo.servode write_register torque_limit 1023 --sid 24
python -m servo.servode write_register cw_compliance_slope 400 --sid 20
python -m servo.servode write_register cw_compliance_slope 400 --sid 21
python -m servo.servode write_register cw_compliance_slope 400 --sid 22
python -m servo.servode write_register cw_compliance_slope 400 --sid 23
python -m servo.servode write_register cw_compliance_slope 400 --sid 24
python -m servo.servode write_register ccw_compliance_slope 400 --sid 20
python -m servo.servode write_register ccw_compliance_slope 400 --sid 21
python -m servo.servode write_register ccw_compliance_slope 400 --sid 22
python -m servo.servode write_register ccw_compliance_slope 400 --sid 23
python -m servo.servode write_register ccw_compliance_slope 400 --sid 24
python -m servo.servode write_register moving_speed 200 --sid 20
python -m servo.servode write_register moving_speed 200 --sid 21
python -m servo.servode write_register moving_speed 200 --sid 22
python -m servo.servode write_register moving_speed 200 --sid 23
python -m servo.servode write_register moving_speed 200 --sid 24
python -m servo.servode write_register cw_compliance_margin 1 --sid 20
python -m servo.servode write_register cw_compliance_margin 1 --sid 21
python -m servo.servode write_register cw_compliance_margin 1 --sid 22
python -m servo.servode write_register cw_compliance_margin 1 --sid 23
python -m servo.servode write_register cw_compliance_margin 1 --sid 24
python -m servo.servode write_register ccw_compliance_margin 1 --sid 20
python -m servo.servode write_register ccw_compliance_margin 1 --sid 21
python -m servo.servode write_register ccw_compliance_margin 1 --sid 22
python -m servo.servode write_register ccw_compliance_margin 1 --sid 23
python -m servo.servode write_register ccw_compliance_margin 1 --sid 24
