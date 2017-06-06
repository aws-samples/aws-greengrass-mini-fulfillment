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

from __future__ import print_function
import os
import fire
import json
import zipfile
import boto3
from botocore.exceptions import ClientError
from retrying import retry

dir_path = os.path.dirname(os.path.realpath(__file__))
print("path: {0}".format(dir_path))
temp_deploy_zip = "deploy.zip"


def create(config_file, runtime='python2.7', role_name='NoServiceAccess',
           role_policy='policy.json', assume_role_policy_doc='trust.json'):

    with open(config_file, "r") as f:
        cfg = json.load(f)

    func_name = cfg['func_name']
    func_desc = cfg['func_desc']
    lambda_alias = cfg['lambda_alias']
    lambda_dir = dir_path + '/' + cfg['lambda_dir']
    lambda_handler = cfg['lambda_handler']
    lambda_files = cfg['lambda_files']
    lambda_main = cfg['lambda_main']

    role_arn = _create_lambda_policies(assume_role_policy_doc,
                                       func_name=func_name,
                                       lambda_dir=lambda_dir,
                                       role_name=role_name,
                                       role_policy=role_policy)

    with zipfile.ZipFile(temp_deploy_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in lambda_files:
            zf.write(cfg['lambda_dir'] + '/' + f)

    resp = _create_lambda(
        role_arn, func_name, func_desc, lambda_handler, lambda_main, runtime
    )
    _publish_lambda_version(func_arn=resp['FunctionArn'])
    _create_function_alias(func_alias=lambda_alias,
                           func_name=func_name,
                           func_version=resp['Version'])

    os.remove(temp_deploy_zip)


def _create_lambda_policies(assume_role_policy_doc, func_name, lambda_dir,
                            role_name, role_policy):
    iam = boto3.client('iam')
    role_arn = ''
    try:
        tf = lambda_dir + '/' + assume_role_policy_doc
        with open(tf) as trust_file:
            trust = json.dumps(json.load(trust_file))
            resp = iam.create_role(RoleName=role_name,
                                   # Path=dir_path+'/',
                                   AssumeRolePolicyDocument=trust)
            role_arn = resp['Role']['Arn']

        print('created iam role:{0} with arn:{1}'.format(role_name, role_arn))
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'EntityAlreadyExists':
            print("Role '{0}' already exists. Using existing Role".format(
                role_name))
            role = iam.get_role(RoleName=role_name)
            role_arn = role['Role']['Arn']
        else:
            print("Unexpected Error: {0}".format(ce))
    try:
        pf = lambda_dir + '/' + role_policy
        with open(pf) as policy_file:
            policy = json.dumps(json.load(policy_file))
            resp = iam.put_role_policy(RoleName=role_name,
                                       PolicyName=func_name + '_policy',
                                       PolicyDocument=policy)
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'EntityAlreadyExists':
            print("Policy '{0}' already exists.".format(role_name))
        else:
            print("Unexpected Error: {0}".format(ce))

    return role_arn


@retry(wait_random_min=4000, wait_random_max=6000, stop_max_attempt_number=3)
def _create_lambda(arn, func_name, func_desc, lambda_handler, lambda_main,
                   runtime):
    func = dict()
    lamb = boto3.client('lambda')
    with open(temp_deploy_zip) as deploy:
        func['ZipFile'] = deploy.read()
    try:
        resp = lamb.create_function(
            FunctionName=func_name, Runtime=runtime, Publish=True,
            Description=func_desc,
            Role=arn, Code=func, Handler='{0}.{1}'.format(
                lambda_main, lambda_handler
            ))
        print("Create Lambda Function resp:{0}".format(
            json.dumps(resp, indent=4, sort_keys=True))
        )
        return resp
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ValidationException':
            print("Validation Error {0} creating function '{1}'.".format(
                ce, func_name))
        else:
            print("Unexpected Error: {0}".format(ce))


def _publish_lambda_version(func_arn):
    pass


def _create_function_alias(func_alias, func_name, func_version):
    lamb = boto3.client('lambda')

    try:
        resp = lamb.create_alias(
            Name=func_alias,
            FunctionName=func_name,
            FunctionVersion=func_version
        )
        print("Create Lambda Alias resp:{0}".format(
            json.dumps(resp, indent=4, sort_keys=True))
        )
        return resp
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ValidationException':
            print("Validation Error {0} creating alias '{1}'.".format(
                ce, func_alias))
        else:
            print("Unexpected Error: {0}".format(ce))


def update(func_name, lambda_main=None, lambda_handler='handler',
           lambda_files=None):
    pass

if __name__ == "__main__":

    fire.Fire({
        'create': create
    })

    # create(
    #     func_name='ArmErrorDetector',
    #     lambda_main='error_detector',
    #     lambda_files=['error_detector.py']
    # )
    # update(
    #     func_name='SHSortArmErrorDetector',
    #     lambda_main='error_detector',
    #     lambda_files=['error_detector.py']
    # )
