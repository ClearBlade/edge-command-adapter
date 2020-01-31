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
                        connect to. The default is 1883.')

    parser.add_argument('--adapterSettingsCollection', dest="adapterSettingsCollectionName", \
                        default="", \
                        help='The name of the ClearBlade Platform data collection which contains \
                        runtime configuration settings for the adapter. The default is "".')

    parser.add_argument('--adapterSettingsItem', dest="adapterSettingsItemID", default="", \
                        help='The "item_id" of the row, within the ClearBlade Platform data \
                        collection which contains runtime configuration settings, that should \
                        be used to configure the adapter. The default is "".')

    parser.add_argument('--requestTopicRoot', dest="requestTopicRoot", default="edge/command", \
                        help='The root of MQTT topics this adapter will subscribe and publish to. \
                        The default is "edge/command".')

    parser.add_argument('--responseTopicRoot', dest="responseTopicRoot", default="edge/command", \
                        help='The root of MQTT topics this adapter will subscribe and publish to. \
                        The default is "edge/response".')

    parser.add_argument('--deviceProvisionSvc', dest="deviceProvisionSvc", default="", \
                        help='The name of a service that can be invoked to provision IoT devices \
                        within the ClearBlade Platform or Edge. The default is "".')

    parser.add_argument('--deviceHealthSvc', dest="deviceHealthSvc", default="", \
                        help='The name of a service that can be invoked to provide the health of \
                        an IoT device to the ClearBlade Platform or Edge. The default is "".')

    parser.add_argument('--deviceLogsSvc', dest="deviceLogsSvc", default="", \
                        help='The name of a service that can be invoked to provide IoT device \
                        logging information to the ClearBlade Platform or Edge. The default is "".')

    parser.add_argument('--deviceStatusSvc', dest="deviceStatusSvc", default="", \
                        help='The name of a service that can be invoked to provide the status of \
                        an IoT device to the ClearBlade Platform or Edge. The default is "".')

    parser.add_argument('--deviceDecommissionSvc', dest="deviceDecommissionSvc", default="", \
                        help='The name of a service that can be invoked to decommission IoT \
                        devices within the ClearBlade Platform or Edge. The default is "".')

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

CB_SYSTEM = System(CB_CONFIG['systemKey'], CB_CONFIG['systemSecret'], CB_CONFIG['httpURL'] )

# Log in as Sanket
#uid = CB_SYSTEM.User("aidemonitor@clearblade.com", "#bubba#")
uid = CB_SYSTEM.Device(CB_CONFIG['deviceID'], CB_CONFIG['activeKey'])

# Use Sanket to access a messaging client
mqtt = CB_SYSTEM.Messaging(uid, CB_CONFIG["messagingPort"], keepalive=30)

# Set up callback functions
def on_connect(client, userdata, flags, rc):
    # When we connect to the broker, subscribe to the southernplayalisticadillacmuzik channel
    client.subscribe(CB_CONFIG["requestTopicRoot"])
    
def on_message(client, userdata, message):
    # When we receive a message, print it out
    print "Received message '" + message.payload + "' on topic '" + message.topic + "'"
    j=json.loads(message.payload)
    cmd=str(j["command"])
    #args=str(j["args"])
    try:
        result= subprocess.check_output(cmd.split())
    except:
        result='{"Error": "Error Running " + cmd}'
    mqtt.publish(CB_CONFIG["responseTopicRoot"], create_response(message, result))


def create_response(request, resp):
    logging.debug("In create_response")
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