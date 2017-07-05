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

import socket
import traceback
from AWSIoTPythonSDK.exception import operationTimeoutException


def mqtt_connect(client):
    connected = False
    try:
        client.connect()
        connected = True
    except socket.error as se:
        print("SE:{0}".format(se))
    except operationTimeoutException as te:
        print("operationTimeoutException:{0}".format(te.message))
        traceback.print_tb(te, limit=25)
    except Exception as e:
        print("Exception caught:{0}".format(e.message))

    # TODO add some retry logic
    return connected
