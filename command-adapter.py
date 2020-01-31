#!/usr/bin/env python
from clearblade.ClearBladeCore import System
import argparse, sys, time, subprocess, logging, json

def parse_args(argv):
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser(description='Start ClearBlade Adapter')
    parser.add_argument('--systemKey', required=True, help='The System Key of the ClearBlade \
                        Plaform "System" the adapter will connect to.')

    parser.add_argument('--systemSecret', required=True, help='The System Secret of the \
                        ClearBlade Plaform "System" the adapter will connect to.')

    parser.add_argument('--deviceID', required=True, \
                        help='The id/name of the device that will be used for device \
                        authentication against the ClearBlade Platform or Edge, defined \
                        within the devices table of the ClearBlade platform.')

    parser.add_argument('--activeKey', required=True, \
                        help='The active key of the device that will be used for device \
                        authentication against the ClearBlade Platform or Edge, defined within \
                        the devices table of the ClearBlade platform.')

    parser.add_argument('--httpUrl', dest="httpURL", default="http://localhost", \
                        help='The HTTP URL of the ClearBlade Platform or Edge the adapter will \
                        connect to. The default is https://localhost.')

    parser.add_argument('--httpPort', dest="httpPort", default="9000", \
                        help='The HTTP Port of the ClearBlade Platform or Edge the adapter will \
                        connect to. The default is 9000.')

    parser.add_argument('--messagingUrl', dest="messagingURL", default="localhost", \
                        help='The MQTT URL of the ClearBlade Platform or Edge the adapter will \
                        connect to. The default is https://localhost.')

    parser.add_argument('--messagingPort', dest="messagingPort", default="1883", \
                        help='The MQTT Port of the ClearBlade Platform or Edge the adapter will \
                        connect to. The default is 1883.', type=int)

    parser.add_argument('--requestTopicRoot', dest="requestTopicRoot", default="edge/command/request", \
                        help='The root of MQTT topics this adapter will subscribe and publish to. \
                        The default is "edge/command/request".')

    parser.add_argument('--responseTopicRoot', dest="responseTopicRoot", default="edge/command/response", \
                        help='The root of MQTT topics this adapter will subscribe and publish to. \
                        The default is "edge/command/response".')

    parser.add_argument('--logLevel', dest="logLevel", default="INFO", choices=['CRITICAL', \
                        'ERROR', 'WARNING', 'INFO', 'DEBUG'], help='The level of logging that \
                        should be utilized by the adapter. The default is "INFO".')

    parser.add_argument('--logCB', dest="logCB", default=False, action='store_true',\
                        help='Flag presence indicates logging information should be printed for \
                        ClearBlade libraries.')

    parser.add_argument('--logMQTT', dest="logMQTT", default=False, action='store_true',\
                        help='Flag presence indicates MQTT logs should be printed.')

    return vars(parser.parse_args(args=argv[1:]))

# System credentials
CB_CONFIG = parse_args(sys.argv)
CB_SYSTEM = System(CB_CONFIG['systemKey'], CB_CONFIG['systemSecret'], CB_CONFIG['httpURL'] + ":" + CB_CONFIG["httpPort"] )

uid = CB_SYSTEM.Device(CB_CONFIG['deviceID'], CB_CONFIG['activeKey'])

mqtt = CB_SYSTEM.Messaging(uid, CB_CONFIG["messagingPort"], keepalive=30)

# Set up callback functions
def on_connect(client, userdata, flags, rc):
    client.subscribe(CB_CONFIG["requestTopicRoot"])
    
def on_message(client, userdata, message):
    message.payload = message.payload.decode()
    print("Received message '" + message.payload + "' on topic '" + message.topic + "'")
    j=json.loads(message.payload)
    cmd=str(j["command"])
    result={}
    try:
        process = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        result["stdout"]=process.stdout
        result["stderr"]=process.stderr
        result["error"]=False
    except subprocess.CalledProcessError as e:
        print("failed to run command")
        result["stdout"]=e.stdout
        result["stderr"]=e.stderr
        result["error"]=True
    
    resp={}
    resp["request"]=j
    resp["response"]=result
    mqtt.publish(CB_CONFIG["responseTopicRoot"], json.dumps(resp))

def create_response(request, resp):
    message = {}
    message['request'] = request
    message['response'] = resp
    return resp
    
# Connect callbacks to client
mqtt.on_connect = on_connect
mqtt.on_message = on_message

# Connect and wait for messages
mqtt.connect()
while(True):
    time.sleep(1)  # wait for messages