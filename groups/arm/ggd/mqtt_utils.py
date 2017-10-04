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
import socket
import traceback

from AWSIoTPythonSDK.core.protocol.connection.cores import \
    ProgressiveBackOffCore
from AWSIoTPythonSDK.exception.AWSIoTExceptions import \
    DiscoveryInvalidRequestException, DiscoveryFailure
from AWSIoTPythonSDK.exception import operationTimeoutException


# def mqtt_connect(mqtt_client):
#     connected = False
#     try:
#         mqtt_client.connect()
#         connected = True
#     except socket.error as se:
#         print("SE:{0}".format(se))
#     except operationTimeoutException as te:
#         print("operationTimeoutException:{0}".format(te.message))
#         traceback.print_tb(te, limit=25)
#     except Exception as e:
#         print("Exception caught:{0}".format(e.message))
#
#     # TODO add some retry logic
#     return connected

def mqtt_connect(mqtt_client, core_info):
    connected = False
    for connectivity_info in core_info.connectivityInfoList:
        core_host = connectivity_info.host
        core_port = connectivity_info.port
        print("Connecting to Core at {0}:{1}".format(core_host, core_port))
        mqtt_client.configureEndpoint(core_host, core_port)
        try:
            mqtt_client.connect()
            connected = True
        except socket.error as se:
            print("SE:{0}".format(se))
        except operationTimeoutException as te:
            print("operationTimeoutException:{0}".format(te.message))
            traceback.print_tb(te, limit=25)
        except Exception as e:
            print("Exception caught:{0}".format(e.message))

    return connected


def ggc_discovery(thing_name, discovery_info_provider, group_ca_path,
                  retry_count=10):
    back_off_core = ProgressiveBackOffCore()
    discovered = False
    group_ca = None
    ca_list = None
    core_list = None
    while retry_count != 0:
        try:
            discovery_info = discovery_info_provider.discover(thing_name)
            ca_list = discovery_info.getAllCas()
            core_list = discovery_info.getAllCores()

            # Only pick the first CA and Core info (currently)
            group_id, ca = ca_list[0]
            core_info = core_list[0]
            print("Discovered Greengrass Core: {0} from Group: {1}".format(
                core_info.coreThingArn, group_id)
            )

            print("Persist the Core connectivity identity information...")
            group_ca = group_ca_path + '/' + group_id + "_CA.crt"
            if not os.path.exists(group_ca_path):
                os.makedirs(group_ca_path)
            group_ca_file = open(group_ca, "w")
            group_ca_file.write(ca)
            group_ca_file.close()

            discovered = True
            break
        except DiscoveryFailure as df:
            print("Discovery request failed!")
            print("Error:{0} type: {1}".format(df, str(type(df))))
            print("       message: {0}".format(df.message))
            back_off = True
        except DiscoveryInvalidRequestException as e:
            print("Invalid discovery request detected!")
            print("Error:{0}".format(e))
            print("Stopping...")
            break
        except BaseException as e:
            print("Error in discovery: {0} type: {1}".format(e, str(type(e))))
            print("           message: {0}".format(e.message))
            print("  thing_name: {0}".format(thing_name))
            print("  dip: {0}".format(discovery_info_provider))
            print("  group_ca_path: {0}".format(group_ca_path))
            back_off = True

        if back_off:
            retry_count -= 1
            print("  {0} retries left\n".format(retry_count))
            print("  Backing off...\n")
            back_off_core.backOff()

    return discovered, group_ca, ca_list, core_list
