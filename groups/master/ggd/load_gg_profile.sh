#!/usr/bin/env bash

python -m servo.servode ping 10
python -m servo.servode write_register torque_enable 1 --sid 10
python -m servo.servode write_register torque_limit 1023 --sid 10
python -m servo.servode write_register cw_compliance_slope 400 --sid 10
python -m servo.servode write_register ccw_compliance_slope 400 --sid 10
python -m servo.servode write_register moving_speed 200 --sid 10
python -m servo.servode write_register cw_compliance_margin 1 --sid 10
python -m servo.servode write_register ccw_compliance_margin 1 --sid 10
