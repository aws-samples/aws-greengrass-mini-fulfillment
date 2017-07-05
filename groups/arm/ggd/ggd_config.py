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

master_core_ip = "xx.xx.xx.xx"
# master_core_ip = "10.0.1.41"
master_core_port = 8883
sort_arm_ip = "yy.yy.yy.yy"
# sort_arm_ip = "10.0.1.38"
sort_arm_port = 8883
inv_arm_ip = "zz.zz.zz.zz"
# inv_arm_ip = "10.0.1.42"
inv_arm_port = 8883

master_shadow_name = "MasterBrain"

convey_topics = [
    "/convey/telemetry",
    "/convey/errors",
    "/convey/stages"
]

sort_bridge_topics = [
    "/arm/telemetry",
    "/arm/errors",
    "/arm/stages"
]

inv_bridge_topics = [
    "/arm/telemetry",
    "/arm/errors",
    "/arm/stages"
]

convey_servo_ids = [
    10
]

arm_servo_ids = [
    20, 21, 22, 23, 24
]
