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
import json
import zipfile
import boto3
from botocore.exceptions import ClientError
from retrying import retry

dir_path = os.path.dirname(os.path.realpath(__file__))
print("path: {0}".format(dir_path))


def create(func_name, runtime='python2.7', role_name='NoServiceAccess',
           assume_role_policy_doc='trust.json', lambda_main=None,
           lambda_handler='handler', lambda_files=None):
    iam = boto3.client('iam')
    role_arn = ''
    try:
        with open(name=assume_role_policy_doc) as trust_file:
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
        with open(name='policy.json') as policy_file:
            policy = json.dumps(json.load(policy_file))
            resp = iam.put_role_policy(RoleName=role_name,
                                       PolicyName=func_name+'_policy',
                                       PolicyDocument=policy)
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'EntityAlreadyExists':
            print("Policy '{0}' already exists.".format(role_name))
        else:
            print("Unexpected Error: {0}".format(ce))

    with zipfile.ZipFile("deploy.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for f in lambda_files:
            zf.write(f)

    _create_lambda(role_arn, func_name, lambda_handler, lambda_main, runtime)


@retry(wait_random_min=4000, wait_random_max=6000, stop_max_attempt_number=3)
def _create_lambda(arn, func_name, lambda_handler, lambda_main,
                   runtime):
    func = dict()
    lamb = boto3.client('lambda')
    with open('deploy.zip') as deploy:
        func['ZipFile'] = deploy.read()
    try:
        resp = lamb.create_function(
            FunctionName=func_name, Runtime=runtime, Publish=True,
            Description="gg-mini-fulfillment function for overall error detection",
            Role=arn, Code=func, Handler='{0}.{1}'.format(
                lambda_main, lambda_handler
            ))
        print("Create Lambda Function resp:{0}".format(resp))
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ValidationException':
            print("Validation Error {0} creating function '{1}'.".format(
                ce, func_name))
        else:
            print("Unexpected Error: {0}".format(ce))


def update(func_name, lambda_main=None, lambda_handler='handler',
           lambda_files=None):
    pass

if __name__ == "__main__":
    create(
        func_name='MasterErrorDetector',
        lambda_main='error_detector',
        lambda_files=['error_detector.py']
    )
    # update(
    #     func_name='SHSortArmErrorDetector',
    #     lambda_main='error_detector',
    #     lambda_files=['error_detector.py']
    # )
