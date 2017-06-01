
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

import os
import json
import logging


logging.basicConfig(format='%(asctime)s|%(name)-8s|%(levelname)s: %(message)s',
                    level=logging.INFO)


class GroupConfigFile(object):
    def __init__(self, config_file='cfg.json'):
        super(GroupConfigFile, self).__init__()
        self.config_file = config_file
        if self.get_config() is None:
            raise ValueError("Error reading config file: {0}".format(
                self.config_file))

    def get_config(self):
        config = None
        if os.path.exists(self.config_file) and os.path.isfile(
                self.config_file):
            try:
                with open(self.config_file, "r") as in_file:
                    config = json.load(in_file)
            except OSError as ose:
                logging.error(
                    'OSError while reading config file. {0}'.format(ose))
        return config

    def update(self, **kwargs):
        if len(kwargs.keys()) == 0:
            logging.warning("No new configuration to update.")
            return
        # config['group'] = {"id": group_info['Id']}
        config = self.get_config()
        if 'core' in kwargs:
            for key, val in kwargs['core']:
                config['core'][key] = val
            kwargs.pop('core')
        if 'lambda_functions' in kwargs:
            for key in kwargs['lambda_functions']:
                config['lambda_functions'][key] = kwargs['lambda_functions'][
                    key]
            kwargs.pop('lambda_functions')
        if 'devices' in kwargs:
            for key in kwargs['devices']:
                config['devices'][key] = kwargs['devices'][key]
            kwargs.pop('devices')
        if 'core_def' in kwargs:
            for key, val in kwargs['core_def']:
                config['core_def'][key] = val
            kwargs.pop('core_def')
        if 'device_def' in kwargs:
            for key, val in kwargs['device_def']:
                config['device_def'][key] = val
            kwargs.pop('device_def')
        if 'group' in kwargs.keys():
            for key, val in kwargs['group']:
                logging.info('Updating group key:{0} and value:{0}'.format(
                    key, val))
                config['group'][key] = val
            kwargs.pop('group')

        if len(kwargs) > 0:
            # treat the rest of the kwargs as simple property value assignments
            for key in kwargs.keys():
                logging.info("Update config key:{0}".format(key))
                config[key] = kwargs[key]
        self.write_config(config)

    def write_config(self, config):
        try:
            with open(self.config_file, "w") as out_file:
                json.dump(config, out_file, indent=2,
                          separators=(',', ': '), sort_keys=True)
                logging.debug(
                    'Config file:{0} updated.'.format(self.config_file))
        except OSError as ose:
            logging.error(
                'OSError while writing config file. {0}'.format(ose))

    def is_fresh(self):
        cfg = self.get_config()
        if cfg is not None:
            if all(x == '' for x in (
                    cfg['group']['id'], cfg['func_def']['id'],
                    cfg['core_def']['id'], cfg['device_def']['id'],
                    cfg['logger_def']['id']
            )):
                return True

        return False

    def make_fresh(self):
        config = self.get_config()
        config['group']['id'] = ''
        config['group']['version'] = ''
        config['group']['version_arn'] = ''
        config['core_def']['id'] = ''
        config['core_def']['version_arn'] = ''
        config['device_def']['id'] = ''
        config['device_def']['version_arn'] = ''
        config['func_def']['id'] = ''
        config['func_def']['version_arn'] = ''
        config['logger_def']['id'] = ''
        config['logger_def']['version_arn'] = ''
        config['subscription_def']['id'] = ''
        config['subscription_def']['version_arn'] = ''
        self.write_config(config=config)

    def read(self, prop):
        return self.get_config()[prop]

    def __getitem__(self, prop):
        return self.read(prop)

    def __setitem__(self, key, val):
        cfg = self.get_config()
        cfg[key] = val
        self.write_config(cfg)
