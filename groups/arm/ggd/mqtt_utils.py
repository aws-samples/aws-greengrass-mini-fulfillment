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
