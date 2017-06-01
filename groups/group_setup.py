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

from master.group_config import GroupConfigFile

logging.basicConfig(format='%(asctime)s|%(name)-8s|%(levelname)s: %(message)s',
                    level=logging.INFO)

group_types = ['arm', 'master']
prod_gg_endpoint = "https://greengrass.us-west-2.amazonaws.com"
gg_client = boto3.client("gg", endpoint_url=prod_gg_endpoint)


# TODO revise the thing policy with min privileges required at Greengrass GA.
# TODO revise the thing policy with min resources required at Greengrass GA
def _create_and_attach_thing_policy(config, region):
    if config['core']['thing_name'] is '<device_thing_name>':
        raise ValueError("Config file values seem to be mis-configured.")

    # Create and attach to the principal/certificate the minimal action
    # privileges Thing policy that allows publish and subscribe
    thing_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "iot:*",
                "greengrass:*"
                # "iot:Connect",
                # "iot:Publish",
                # "iot:Receive",
                # "iot:Subscribe"
            ],
            "Resource": [
                # "arn:aws:iot:{0}:*:*".format(region)
                "*"
            ]
        }]
    }

    iot = Session(region_name=region).client('iot')
    policy_name = 'ggmf-{0}'.format(config['core']['thing_name'])
    policy = json.dumps(thing_policy)
    logging.debug('[_create_and_attach_thing_policy] policy:{0}'.format(policy))
    try:
        p = iot.create_policy(
            policyName=policy_name,
            policyDocument=policy
        )
        logging.debug("[_create_and_attach_thing_policy] Created Policy: {0}".format(
            p['policyName']))

        cert_arn = config['core']['cert_arn']
        iot.attach_principal_policy(policyName=policy_name, principal=cert_arn)
        logging.debug("[_create_and_attach_thing_policy] Attached {0} to {1}".format(
            policy_name, cert_arn))
        return p['policyName'], p['policyArn']

    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            logging.warning(
                "[_create_and_attach_thing_policy] {0}".format(
                    ce.response['Error']['Message']))
        # since policy already exists return nothing, assuming previous success


def _create_and_attach_iam_role(config, region):
    logging.info("[begin] [_create_and_attach_iam_role]")
    iam = Session(region_name=region).client('iam')
    iam_res = Session(region_name=region).resource('iam')
    role_name = 'ggmf_service_role'
    aws_lambda_ro_access_arn = "arn:aws:iam::aws:policy/AWSLambdaReadOnlyAccess"
    aws_iot_full_access_arn = "arn:aws:iam::aws:policy/AWSIoTFullAccess"

    assume_role_policy = {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Effect": "Allow",
              "Principal": {
                "Service": "greengrass.amazonaws.com"
              },
              "Action": "sts:AssumeRole"
            }
          ]
        }
    gg_inline_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ggmf20170531",
                "Effect": "Allow",
                "Action": [
                    "greengrass:*"
                ],
                "Resource": [
                    "*"
                ]
            }
        ]
    }
    try:
        resp = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        logging.debug(
            "[_create_and_attach_iam_role] create_role {0}".format(resp))
        resp = iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn=aws_lambda_ro_access_arn
        )
        logging.debug(
            "[_create_and_attach_iam_role] attach_policy 1 {0}".format(resp))
        resp = iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn=aws_iot_full_access_arn
        )
        logging.debug(
            "[_create_and_attach_iam_role] attach_policy 2 {0}".format(resp))
        resp = iam.put_role_policy(
            RoleName=role_name,
            PolicyName='gg_inline_policy',
            PolicyDocument=json.dumps(gg_inline_policy)
        )
        logging.debug(
            "[_create_and_attach_iam_role] put_policy {0}".format(resp))
        role = iam_res.Role(role_name)
        gg_client.attach_service_role_to_account(RoleArn=role.arn)
        logging.info(
            "[end] [_create_and_attach_iam_role] attached service role")

    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            logging.warning(
                "[_create_and_attach_iam_role] {0}".format(
                    ce.response['Error']['Message']))
        else:
            logging.error("[_create_and_attach_iam_role] {0}".format(
                    ce.response['Error']['Message']))
        # since role already exists return nothing, assuming previous success


def _choose_core_definition(group_type, cfg):
    if 'master' is group_type or 'arm' is group_type:
        return [{
            "ThingArn": cfg['core']['thing_arn'],
            "CertificateArn": cfg['core']['cert_arn'],
            "Id": "{0}_00".format(group_type),
            "SyncShadow": True
        }]

    return None


def _choose_device_definition(group_type, cfg):
    if 'master' is group_type:
        return [
            {
                "Id": "{0}_10".format(group_type),
                "ThingArn": cfg['devices']['GGD_belt']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_belt']['cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_11".format(group_type),
                "ThingArn": cfg['devices']['GGD_bridge']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_bridge']['cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_12".format(group_type),
                "ThingArn": cfg['devices']['GGD_button']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_button']['cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_13".format(group_type),
                "ThingArn": cfg['devices']['GGD_inv_arm']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_inv_arm']['cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_14".format(group_type),
                "ThingArn": cfg['devices']['GGD_sort_arm']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_sort_arm']['cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_15".format(group_type),
                "ThingArn": cfg['devices']['GGD_heartbeat']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_heartbeat']['cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_16".format(group_type),
                "ThingArn": cfg['devices']['GGD_web']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_web']['cert_arn'],
                "SyncShadow": False
            }
        ]
    elif 'arm' is group_type:
        return [
            {
                "Id": "{0}_20".format(group_type),
                "ThingArn": cfg['devices']['GGD_arm']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_arm']['cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_21".format(group_type),
                "ThingArn": cfg['devices']['GGD_bridge']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_bridge']['cert_arn'],
                "SyncShadow": False
            },
            {
                "Id": "{0}_22".format(group_type),
                "ThingArn": cfg['devices']['GGD_heartbeat']['thing_arn'],
                "CertificateArn": cfg['devices']['GGD_heartbeat']['cert_arn'],
                "SyncShadow": False
            }
        ]

    return None


def _choose_subscription_definition(group_type, cfg):
    d = cfg['devices']
    l = cfg['lambda_functions']
    s = cfg['subscriptions']

    if 'master' is group_type:
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
    elif 'arm' is group_type:
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

    return None


def create(group_type, config_file, group_name=None, region='us-west-2'):
    """
    Create a Greengrass group in the gg-mini-fulfillment demo.

    group_type: either 'arm' or 'master'
    config_file: config file of the group to create
    group_name: the name of the group. If no name is given then group_type 
                will be used.
    region: the region in which to create the new group.
    """
    if group_type not in group_types:
        raise ValueError("Can only create {0} groups.".format(group_types))
    config = GroupConfigFile(config_file=config_file)
    if config.is_fresh() is False:
        raise ValueError("Config already tracking previously created group")

    # Create a Group
    logging.info("[begin] Creating a Greengrass Group")
    if group_name is None:
        group_name = group_type

    group_info = gg_client.create_group(Name="{0}_group".format(group_name))
    config['group'] = {"id": group_info['Id']}
    _create_and_attach_thing_policy(config, region)
    _create_and_attach_iam_role(config, region)

    cl_arn = create_core_definition(group_type, config, group_name)
    dl_arn = create_device_definition(group_type, config, group_name)
    lv_arn = create_function_definition(group_type, config)
    log_arn = create_logger_definition(group_type, config)
    sub_arn = create_subscription_definition(group_type, config)

    # Add all the constituent parts to the Greengrass Group
    grp = gg_client.create_group_version(
        GroupId=group_info['Id'],
        CoreDefinitionVersionArn=cl_arn,
        DeviceDefinitionVersionArn=dl_arn,
        FunctionDefinitionVersionArn=lv_arn,
        LoggerDefinitionVersionArn=log_arn,
        SubscriptionDefinitionVersionArn=sub_arn
    )
    config['group'] = {
        "id": group_info['Id'],
        "version_arn": grp['Arn'],
        "version": grp['Version']
    }
    logging.info("[end] Created Greengrass Group {0}".format(group_info['Id']))


def create_core_definition(group_type, config, group_name):
    core_def = _choose_core_definition(group_type, config.get_config())
    core_def_id = config['core_def']['id']
    if core_def_id is None or len(core_def_id) == 0:
        cd = gg_client.create_core_definition(
            Name="{0}_core_def".format(group_name)
        )
        core_def_id = cd['Id']
        cdv = gg_client.create_core_definition_version(
            CoreDefinitionId=core_def_id,
            Cores=core_def
        )
        cd_arn = cdv['Arn']
        logging.info("Created Core definition ARN:{0}".format(cd_arn))
        config['core_def'] = {'id': core_def_id, 'version_arn': cd_arn}
        logging.info("CoreDefinitionId: {0}".format(core_def_id))
        return cd_arn
    else:
        logging.info("CoreDefinition already exists:{0}".format(core_def_id))
        return


def create_device_definition(group_type, config, group_name):
    device_def = _choose_device_definition(group_type, config.get_config())
    device_def_id = config['device_def']['id']
    if device_def_id is None or len(device_def_id) == 0:
        dl = gg_client.create_device_definition(
            Name="{0}_device_def".format(group_name))
        device_def_id = dl['Id']
        dlv = gg_client.create_device_definition_version(
            DeviceDefinitionId=device_def_id,
            Devices=device_def
        )
        dl_arn = dlv['Arn']
        logging.info("Created Device definition ARN:{0}".format(dl_arn))
        config['device_def'] = {'id': dl['Id'], 'version_arn': dl_arn}
        logging.info("DeviceDefinitionId: {0}".format(device_def_id))
        return dl_arn
    else:
        logging.info("DeviceDefinition already exists:{0}".format(
            device_def_id)
        )
        return


def create_function_definition(group_type, config):
    # Add latest version of Lambda functions to a Function definition
    aws = boto3.client('lambda')
    latest_funcs = dict()
    func_definition = []
    # first determine the latest versions of configured Lambda functions
    for key in config['lambda_functions']:
        lambda_name = key
        version_definition = aws.list_versions_by_function(FunctionName=lambda_name)
        sv = sorted(version_definition['Versions'], key=itemgetter('Version'),
                    reverse=True)
        # use zero'th function version as the most recent by above `sorted`
        fv = sv[0]
        logging.info("Found latest function version: {0}".format(fv))
        latest_funcs[lambda_name] = {"arn": fv['FunctionArn']}  # config file
        func_definition.append({
            "Id": "{0}".format(lambda_name.lower()),
            "FunctionArn": fv['FunctionArn'],
            "FunctionConfiguration": {
                "Executable": fv['Handler'],
                "MemorySize": fv['MemorySize'],
                "Timeout": fv['Timeout']
            }
        })  # function definition

    # if we found one or more configured functions create a func definition
    if len(func_definition) > 0:
        ll = gg_client.create_function_definition(
            Name="{0}_func_def".format(group_type)
        )
        lmbv = gg_client.create_function_definition_version(
            FunctionDefinitionId=ll['Id'],
            Functions=func_definition
        )
        config['lambda_functions'] = latest_funcs  # update config with versions
        ll_arn = lmbv['Arn']
        logging.info("Created Function definition ARN:{0}".format(ll_arn))
        config['func_def'] = {'id': ll['Id'], 'version_arn': ll_arn}
        return ll_arn
    else:
        return '<no_functions>'


def create_logger_definition(group_type, config):
    log_info = gg_client.create_logger_definition(
        Name="{0}_logger_def".format(group_type)
    )
    logv = gg_client.create_logger_definition_version(
        LoggerDefinitionId=log_info['Id'],
        Loggers=[{
            "Id": "gg-logging",
            "Component": "GreengrassSystem", "Level": "INFO",
            "Space": "5000",  # size in KB
            "Type": "FileSystem"
        }, {
            "Id": "func-logging",
            "Component": "Lambda", "Level": "DEBUG",
            "Space": "5000",  # size in KB
            "Type": "FileSystem"
        }]
    )
    log_arn = logv['Arn']
    logging.info("Created Lambda definition ARN:{0}".format(log_arn))
    config['logger_def'] = {
        "id": log_info['Id'],
        "version_arn": log_arn
    }

    return log_arn


def create_subscription_definition(group_type, config):
    """
    Configure routing subscriptions for a Greengrass group in the
    gg-mini-fulfillment demo.

    group_type: either 'arm' or 'master'
    config: config file of the group to create routing subscriptions
    """
    logging.info('[begin] Configuring routing subscriptions')
    if group_type not in group_types:
        raise ValueError(
            "Can only configure {0} for routing.".format(group_types))
    if config.is_fresh():
        raise ValueError("Config not yet tracking a created Group.")

    sub_info = gg_client.create_subscription_definition(
        Name="{0}_routing".format(group_type)
    )
    logging.info('Created subscription definition: {0}'.format(sub_info))

    subs = _choose_subscription_definition(group_type, config.get_config())
    subv = gg_client.create_subscription_definition_version(
        SubscriptionDefinitionId=sub_info['Id'],
        Subscriptions=subs
    )
    sub_arn = subv['Arn']
    config['subscription_def'] = {
        "id": sub_info['Id'],
        "version_arn": sub_arn
    }
    logging.info('[end] Configured routing subscriptions')
    return sub_arn


def delete(config_file, region='us-west-2'):
    logging.info('[begin] Deleting Group')
    config = GroupConfigFile(config_file=config_file)

    logger_def_id = config['logger_def']['id']
    logging.info('Deleting logger_def_id:{0}'.format(logger_def_id))
    try:
        gg_client.delete_logger_definition(LoggerDefinitionId=logger_def_id)
    except ClientError as ce:
        logging.error(ce.message)

    func_def_id = config['func_def']['id']
    logging.info('Deleting func_def_id:{0}'.format(func_def_id))
    try:
        gg_client.delete_function_definition(FunctionDefinitionId=func_def_id)
    except ClientError as ce:
        logging.error(ce.message)

    device_def_id = config['device_def']['id']
    logging.info('Deleting device_def_id:{0}'.format(device_def_id))
    try:
        gg_client.delete_device_definition(DeviceDefinitionId=device_def_id)
    except ClientError as ce:
        logging.error(ce.message)

    core_def_id = config['core_def']['id']
    logging.info('Deleting core_def_id:{0}'.format(core_def_id))
    try:
        gg_client.delete_core_definition(CoreDefinitionId=core_def_id)
    except ClientError as ce:
        logging.error(ce.message)

    group_id = config['group']['id']
    logging.info('Deleting group_id:{0}'.format(group_id))
    try:
        gg_client.delete_group(GroupId=group_id)
    except ClientError as ce:
        logging.error(ce.message)
        return

    logging.info('[end] Deleted group')


def clean_file(config_file):
    logging.info('[begin] Cleaning config file')
    config = GroupConfigFile(config_file=config_file)

    if config.is_fresh() is True:
        raise ValueError("Config is already clean.")
    config.make_fresh()
    logging.info('[end] Cleaned config file:{0}'.format(config_file))


def clean_all(config_file):
    logging.info('[begin] Cleaning all provisioned artifacts')
    config = GroupConfigFile(config_file=config_file)
    if config.is_fresh() is True:
        raise ValueError("Config is already clean.")

    delete(config_file)
    clean_file(config_file)

    logging.info('[end] Cleaned all provisioned artifacts')


def deploy(group_type, config_file):
    if group_type not in group_types:
        raise ValueError("Can only deploy {0} groups.".format(group_types))

    config = GroupConfigFile(config_file=config_file)
    if config.is_fresh():
        raise ValueError("Config not yet tracking a group. Cannot deploy.")

    dep_req = gg_client.create_deployment(
        GroupId=config['group']['id'],
        GroupVersionId=config['group']['version'],
        DeploymentType="NewDeployment"
    )
    print("Group deploy requested for deployment_id:{0}".format(
        dep_req['DeploymentId'],
    ))


if __name__ == '__main__':
    fire.Fire({
        'create': create,
        'deploy': deploy,
        'clean_all': clean_all
    })
