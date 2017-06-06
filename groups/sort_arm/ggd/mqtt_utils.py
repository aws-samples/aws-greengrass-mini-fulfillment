import socket


def mqtt_connect(client):
    connected = False
    try:
        client.connect()
        connected = True
    except socket.error as se:
        print("SE:{0}".format(se))
        # TODO add some retry logic
    return connected
