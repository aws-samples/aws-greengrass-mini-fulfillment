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

import json
import fire
import boto3
import logging
from operator import itemgetter
from boto3.session import Session
from botocore.exceptions import ClientError

from gg_group_setup import GroupCommands
from gg_group_setup import GroupType


logging.basicConfig(format='%(asctime)s|%(name)-8s|%(levelname)s: %(message)s',
                    level=logging.INFO)


class MasterGroupType(GroupType):
    MASTER_TYPE = 'master'

    def __init__(self, config=None, region='us-west-2'):
        super(MasterGroupType, self).__init__(
            type_name=MasterGroupType.MASTER_TYPE, config=config, region=region
        )

    def get_core_definition(self, cfg):
        return [{
            "ThingArn": cfg['core']['thing_arn'],
            "CertificateArn": cfg['core']['cert_arn'],
            "Id": "{0}_00".format(self.type_name),
            "SyncShadow": True
        }]

    def get_device_definition(self, cfg):
        return [
            {
                "Id": "{0}_10".format(self.type_name),
                "ThingArn": cfg['devices']['GGD_belt']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_belt'][
                    'cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_11".format(self.type_name),
                "ThingArn": cfg['devices']['GGD_bridge']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_bridge'][
                    'cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_12".format(self.type_name),
                "ThingArn": cfg['devices']['GGD_button']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_button'][
                    'cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_13".format(self.type_name),
                "ThingArn": cfg['devices']['GGD_inv_arm']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_inv_arm'][
                    'cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_14".format(self.type_name),
                "ThingArn": cfg['devices']['GGD_sort_arm']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_sort_arm'][
                    'cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_15".format(self.type_name),
                "ThingArn": cfg['devices']['GGD_heartbeat'][
                    'thing_arn'],
                "CertificateArn": cfg['devices']['GGD_heartbeat'][
                    'cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_16".format(self.type_name),
                "ThingArn": cfg['devices']['GGD_web']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_web']['cert_arn'],
                "SyncShadow": False
            }
        ]

    def get_subscription_definition(self, cfg):
        d = cfg['devices']
        l = cfg['lambda_functions']
        s = cfg['subscriptions']

        return [
            {
                "Id": "5",
                "Source": d['GGD_belt']['thing_arn'],
                "Subject": s['telemetry'],
                "Target": l['MasterErrorDetector']['arn']
            },
            {
                "Id": "10",
                "Source": d['GGD_belt']['thing_arn'],
                "Subject": s['all'],
                "Target": d['GGD_web']['thing_arn']
            },
            {
                "Id": "11",
                "Source": d['GGD_belt']['thing_arn'],
                "Subject": s['stages'],
                "Target": l['MasterBrain']['arn']
            },
            {
                "Id": "12",
                "Source": l['MasterErrorDetector']['arn'],
                "Subject": s['errors'],
                "Target": l['MasterBrain']['arn']
            },
            {
                "Id": "13",
                "Source": l['MasterErrorDetector']['arn'],
                "Subject": s['errors'],
                "Target": "cloud"
            },
            {
                "Id": "15",
                "Source": d['GGD_belt']['thing_arn'],
                "Subject": s['stages'],
                "Target": "cloud"
            },
            {
                "Id": "16",
                "Source": d['GGD_web']['thing_arn'],
                "Subject": "$aws/things/MasterBrain/shadow/get",
                "Target": "GGShadowService"
            },
            {
                "Id": "17",
                "Source": "GGShadowService",
                "Subject": "$aws/things/MasterBrain/shadow/get/#",
                "Target": d['GGD_web']['thing_arn']
            },
            {
                "Id": "18",
                "Source": d['GGD_bridge']['thing_arn'],
                "Subject": "/sortarm/#",
                "Target": d['GGD_web']['thing_arn']
            },
            {
                "Id": "19",
                "Source": d['GGD_bridge']['thing_arn'],
                "Subject": "/sortarm/stages",
                "Target": l['MasterBrain']['arn']
            },
            {
                "Id": "20",
                "Source": d['GGD_bridge']['thing_arn'],
                "Subject": "/sortarm/errors",
                "Target": l['MasterBrain']['arn']
            },
            {
                "Id": "21",
                "Source": d['GGD_bridge']['thing_arn'],
                "Subject": "/invarm/stages",
                "Target": l['MasterBrain']['arn']
            },
            {
                "Id": "22",
                "Source": d['GGD_bridge']['thing_arn'],
                "Subject": "/invarm/errors",
                "Target": l['MasterBrain']['arn']
            },
            {
                "Id": "23",
                "Source": d['GGD_bridge']['thing_arn'],
                "Subject": "/invarm/#",
                "Target": d['GGD_web']['thing_arn']
            },
            {
                "Id": "31",
                "Source": d['GGD_belt']['thing_arn'],
                "Subject": "$aws/things/MasterBrain/shadow/get",
                "Target": "GGShadowService"
            },
            {
                "Id": "32",
                "Source": "GGShadowService",
                "Subject": "$aws/things/MasterBrain/shadow/get/#",
                "Target": d['GGD_belt']['thing_arn']
            },
            {
                "Id": "34",
                "Source": d['GGD_belt']['thing_arn'],
                "Subject": "$aws/things/MasterBrain/shadow/update",
                "Target": "GGShadowService"
            },
            {
                "Id": "35",
                "Source": "GGShadowService",
                "Subject": "$aws/things/MasterBrain/shadow/update/#",
                "Target": d['GGD_belt']['thing_arn']
            },
            {
                "Id": "84",
                "Source": d['GGD_inv_arm']['thing_arn'],
                "Subject": "$aws/things/MasterBrain/shadow/get",
                "Target": "GGShadowService"
            },
            {
                "Id": "85",
                "Source": "GGShadowService",
                "Subject": "$aws/things/MasterBrain/shadow/get/#",
                "Target": d['GGD_inv_arm']['thing_arn']
            },
            {
                "Id": "86",
                "Source": d['GGD_inv_arm']['thing_arn'],
                "Subject": "$aws/things/MasterBrain/shadow/update",
                "Target": "GGShadowService"
            },
            {
                "Id": "87",
                "Source": "GGShadowService",
                "Subject": "$aws/things/MasterBrain/shadow/update/#",
                "Target": d['GGD_inv_arm']['thing_arn']
            },
            {
                "Id": "92",
                "Source": d['GGD_sort_arm']['thing_arn'],
                "Subject": "$aws/things/MasterBrain/shadow/get",
                "Target": "GGShadowService"
            },
            {
                "Id": "93",
                "Source": "GGShadowService",
                "Subject": "$aws/things/MasterBrain/shadow/get/#",
                "Target": d['GGD_sort_arm']['thing_arn']
            },
            {
                "Id": "94",
                "Source": d['GGD_sort_arm']['thing_arn'],
                "Subject": "$aws/things/MasterBrain/shadow/update",
                "Target": "GGShadowService"
            },
            {
                "Id": "95",
                "Source": "GGShadowService",
                "Subject": "$aws/things/MasterBrain/shadow/update/#",
                "Target": d['GGD_sort_arm']['thing_arn']
            },
            {
                "Id": "97",
                "Source": d['GGD_heartbeat']['thing_arn'],
                "Subject": "/heart/beat",
                "Target": "cloud"
            },
            {
                "Id": "98",
                "Source": d['GGD_button']['thing_arn'],
                "Subject": "/button",
                "Target": l['MasterBrain']['arn']
            }
        ]


class ArmGroupType(GroupType):
    ARM_TYPE = 'arm'

    def __init__(self, config=None, region='us-west-2'):
        super(ArmGroupType, self).__init__(
            type_name=ArmGroupType.ARM_TYPE, config=config, region=region
        )

    def get_core_definition(self, cfg):
        return [{
            "ThingArn": cfg['core']['thing_arn'],
            "CertificateArn": cfg['core']['cert_arn'],
            "Id": "{0}_00".format(self.type_name),
            "SyncShadow": True
        }]

    def get_device_definition(self, cfg):
        return [
            {
                "Id": "{0}_20".format(self.type_name),
                "ThingArn": cfg['devices']['GGD_arm']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_arm']['cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_21".format(self.type_name),
                "ThingArn": cfg['devices']['GGD_bridge']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_bridge']['cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_22".format(self.type_name),
                "ThingArn": cfg['devices']['GGD_heartbeat']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_heartbeat']['cert_arn'],
                "SyncShadow": False
            }
        ]

    def get_subscription_definition(self, cfg):
        d = cfg['devices']
        l = cfg['lambda_functions']
        s = cfg['subscriptions']

        return [
            {
                "Id": "40",
                "Source": d['GGD_arm']['thing_arn'],
                "Subject": s["all"],
                "Target": d['GGD_bridge']['thing_arn']
            },
            {
                "Id": "41",
                "Source": d['GGD_arm']['thing_arn'],
                "Subject": s['stages'],
                "Target": "cloud"
            },
            {
                "Id": "42",
                "Source": d['GGD_arm']['thing_arn'],
                "Subject": s['telemetry'],
                "Target": l['ArmErrorDetector']['arn']
            },
            {
                "Id": "50",
                "Source": l['ArmErrorDetector']['arn'],
                "Subject": s['errors'],
                "Target": d['GGD_bridge']['thing_arn']
            },
            {
                "Id": "51",
                "Source": l['ArmErrorDetector']['arn'],
                "Subject": s['errors'],
                "Target": "cloud"
            },
            {
                "Id": "95",
                "Source": d['GGD_heartbeat']['thing_arn'],
                "Subject": "/heart/beat",
                "Target": d['GGD_bridge']['thing_arn']
            },
            {
                "Id": "97",
                "Source": d['GGD_heartbeat']['thing_arn'],
                "Subject": "/heart/beat",
                "Target": "cloud"
            }
        ]


if __name__ == '__main__':
    gc = GroupCommands(group_types={
            MasterGroupType.MASTER_TYPE: MasterGroupType,
            ArmGroupType.ARM_TYPE: ArmGroupType
        }
    )
    fire.Fire(gc)
