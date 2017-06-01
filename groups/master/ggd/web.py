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

import os
import json
import time
# import fire
import random
import socket
import argparse
import datetime as dt
import logging
import cachetools

from datetime import timedelta
from threading import Lock
from flask import Flask, request, render_template, Response, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from ..group_config import GroupConfigFile

import ggd_config
from mqtt_utils import mqtt_connect

dir_path = os.path.dirname(os.path.realpath(__file__))

app = Flask(
    __name__, static_folder="flask/static", template_folder='flask/templates'
)
CORS(app)

UPLOAD_FOLDER = 'flask/uploads'
ALLOWED_EXTENSIONS = set('png')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# log = logging.getLogger('web')
log = app.logger
# logging.basicConfig(datefmt='%(asctime)s - %(name)s:%(levelname)s: %(message)s')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s|%(name)-8s|%(levelname)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

mqttc = None
master_shadow = None
shady_vals = {}
topic_cache = cachetools.LRUCache(maxsize=50)
msg_cache = cachetools.LRUCache(maxsize=100)
second = timedelta(seconds=1)
# hz_cache = cachetools.TTLCache(maxsize=60, ttl=60)
last_hz = 0
incr_lock = Lock()
current_hz = 0
current_hz_time = dt.datetime.utcnow()
rollover_lock = Lock()


# class HertzCounter:
#     def __init__(self, init_val=0, ts=dt.datetime.utcnow()):
#         self._lock = Lock()
#         self.time = ts
#         self.value = init_val
#         self.old_value = init_val
#
#     def incr(self, increment=1):
#         with self._lock:
#             self.value += increment
#             ts = dt.datetime.utcnow()
#             print("INCR: ts:{0} self.value:{1}".format(ts, self.value))
#
#         return self.value
#
#     def increment(self, increment=1):
#         return self.incr(increment)
#

def shadow_mgr(payload, status, token):
    if payload == "REQUEST TIME OUT":
        log.debug(
            "[shadow_mgr] shadow 'REQUEST TIME OUT' tk:{0}".format(
                token))
        return
    global shady_vals
    shady_vals = json.loads(payload)
    log.debug("[shadow_mgr] shadow payload:{0} token:{1}".format(
        json.dumps(shady_vals, sort_keys=True), token))


def count_telemetry(data):
    i = 0
    for d in data:
        if 'ts' in d:
            i += 1

    global current_hz
    with incr_lock:
        current_hz += i

    log.debug('[count_telemetry] incrementing count by:{0}'.format(1))


def history(message):
    if 'ggd_id' in message and 'data' in message:
        key = message['ggd_id'] + '_' + message['data'][0]['ts']
        msg_cache[key] = message


def topic_update(client, userdata, message):
    log.debug('[topic_update] received topic:{0} ts:{1}'.format(
        message.topic, dt.datetime.utcnow()))
    topic_cache[message.topic] = message.payload

    msg = json.loads(message.payload)

    if 'data' in msg:
        global last_hz
        global current_hz
        global current_hz_time
        count_telemetry(msg['data'])
        elapsed = dt.datetime.utcnow() - current_hz_time
        if elapsed > second:  # if a second has passed rollover Hz
            with rollover_lock:
                last_hz = current_hz
                current_hz_time = dt.datetime.utcnow()
                current_hz = 0

    history(msg)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def initialize(config_file):
    cfg = GroupConfigFile(config_file)

    web_name = cfg['devices']['GGD_web']['thing_name']
    # get a shadow client to receive commands
    mqttc_shadow_client = AWSIoTMQTTShadowClient(web_name)
    # mqttc_shadow_client.configureTlsInsecure(True)
    mqttc_shadow_client.configureEndpoint("localhost", 8883)
    mqttc_shadow_client.configureCredentials(
        CAFilePath=dir_path + "/certs/master-server.crt",
        KeyPath=dir_path + "/certs/GGD_web.private.key",
        CertificatePath=dir_path + "/certs/GGD_web.certificate.pem.crt"
    )

    mqtt_c = mqttc_shadow_client.getMQTTConnection()

    if not mqtt_connect(mqttc_shadow_client):
        raise EnvironmentError("connection to Master Shadow failed.")

    # create and register the shadow handler on delta topics for commands
    global master_shadow
    master_shadow = mqttc_shadow_client.createShadowHandlerWithName(
        "MasterBrain", True)  # persistent connection with Master Core shadow

    token = master_shadow.shadowGet(shadow_mgr, 5)
    log.debug("[initialize] shadowGet() tk:{0}".format(token))

    for topic in ggd_config.convey_topics:
        mqtt_c.subscribe(topic, 1, topic_update)
        log.info('[initialize] subscribed to topic:{0}'.format(topic))

    for topic in ggd_config.sort_bridge_topics:
        mqtt_c.subscribe(topic, 1, topic_update)
        log.info('[initialize] subscribed to topic:{0}'.format(topic))

    for topic in ggd_config.inv_bridge_topics:
        mqtt_c.subscribe(topic, 1, topic_update)
        log.info('[initialize] subscribed to topic:{0}'.format(topic))


@app.route('/')
def index():
    freq = 8

    stages = {
        "sort_arm": "home",
        "inv_arm": "home",
        "conveyor": "forward"
    }

    heartbeat = {
        "duration": "0:06:58.589397",
        "sensor_id": "heartbeat",
        "ts": "2017-05-10T07:32:51.631351",
        "age": "0:00:10.000000",
        "version": "2016-11-01",
        "ggd_id": "sh-pi3b-ggc_GGD_heartbeat",
        "hostname": "sh-pi3b"
    }


    logs = [{
        "payload": "some message here 1",
        "ts": "2017-05-02T05:30:51.631351"
    }, {
        "payload": "some message here 2",
        "ts": "2017-05-02T04:30:51.631352"
    }, {
        "payload": "some message here 3",
        "ts": "2017-05-02T03:30:51.631353"
    }, {
        "payload": "some message here 4",
        "ts": "2017-05-02T02:30:51.631354"
    }]

    images = {
        "sort_arm" : {"url": "https://1"},
        "inv_arm": {"url": "https://2"}
    }


    return render_template(
        'index.html',
        freq=freq,
        stages=stages,
        heartbeat=heartbeat,
        logs=logs,
        images=images
    )


@app.route('/ui')
def root():
    return app.send_static_file('index.html')


@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)


@app.route('/shadow/get')
def get_shadow():
    token = master_shadow.shadowGet(shadow_mgr, 5)
    log.debug("[get_shadow] shadowGet() tk:{0}".format(token))
    return 'Sent request to get MasterBrain shadow'


@app.route('/upload', methods=['POST'])
def upload():
    log.info('[upload] request')
    if request.method == 'POST':
        log.info('[upload] POST request')
        if 'file' not in request.files:
            log.error('[upload] Upload attempt with no file')
            return Response('No file uploaded', status=500)

        f = request.files['file']
        if f.filename == '':
            log.error('[upload] Upload attempt with no filename')
            return Response('No filename uploaded', status=500)

        if f and allowed_file(f.filename):
            absolute_file = os.path.abspath(UPLOAD_FOLDER + f.filename)
            log.info('[upload] absolute_filename:{0}'.format(absolute_file))
            filename = secure_filename(absolute_file)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return Response('Uploaded file successfully', status=200)
    return


@app.route('/arm/find/<filename>')
def arm_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/dashboard')
def dashboard():
    topic_dict = dict()
    if '/convey/stages' in topic_cache:
        topic_dict['/convey/stages'] = topic_cache['/convey/stages']
    else:
        topic_dict['/convey/stages'] = "Empty Cache"

    if '/sortarm/stages' in topic_cache:
        topic_dict['/sortarm/stages'] = topic_cache['/sortarm/stages']
    else:
        topic_dict['/sortarm/stages'] = "Empty Cache"

    if '/invarm/stages' in topic_cache:
        topic_dict['/invarm/stages'] = topic_cache['/invarm/stages']
    else:
        topic_dict['/invarm/stages'] = "Empty Cache"

    return render_template('topic.html', topic_dict=topic_dict)

# @app.route('/example/frequency')
# def example_frequency():
#     return render_template('frequency.html')

@app.route('/msg/frequency')
@app.route('/msg/frequency/all')
def frequency():
    # js = json.dumps({"frequency": last_hz.value}, sort_keys=False)
    js = json.dumps({"frequency": last_hz}, sort_keys=False)
    return Response(js, status=200, mimetype='application/json')

# TODO add specific station Hz metrics
# @app.route('/msg/frequency/sort_arm')
# @app.route('/msg/frequency/inv_arm')
# @app.route('/msg/frequency/conveyor')


@app.route('/msg/history')
@app.route('/msg/history/<count>')
def message_history(count=None):
    response = dict()
    keys = msg_cache.keys()
    log.debug('[message_history] history length:{0}'.format(len(keys)))
    for k in keys:
        response[k] = msg_cache[k]

    response['length'] = len(keys)
    js = json.dumps(response, sort_keys=True)
    log.debug('[message_history] response:{0}'.format(js))
    return Response(js, status=200, mimetype='application/json')


@app.route('/msg/topic/<path:topic>')
def latest_message(topic):
    t = '/' + topic
    log.debug('[latest_message] get topic:{0}'.format(t))
    if t in topic_cache:
        msg = topic_cache[t]
        return Response(msg, status=200, mimetype='application/json')
    else:
        return Response("Couldn't find topic:{0}".format(t),
                        status=200,
                        mimetype='application/json')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Web Greengrass Device',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('config_file',
                        help="The config file.")
    parser.add_argument('--debug', default=False, action='store_true',
                        help="Activate debug output.")
    args = parser.parse_args()
    # cfg = GroupConfigFile(args.config_file)

    try:
        initialize(args.config_file)
        if args.debug:
            log.setLevel(logging.DEBUG)

        app.run(
            host="0.0.0.0",
            port=5000, use_reloader=False,
            debug=True
        )
    except KeyboardInterrupt:
        log.info("[__main__] KeyboardInterrupt ... shutting down")

    if mqttc:
        mqttc.disconnect()
    time.sleep(1)
