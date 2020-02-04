#!/usr/bin/env python
from clearblade.ClearBladeCore import System
import argparse, sys, time, subprocess, logging, json, os

CB_CONFIG = {}

def parse_env_variables(env):
    """Parse environment variables"""
    possible_vars = ["CB_SYSTEM_KEY", "CB_SYSTEM_SECRET", "CB_EDGE_NAME", "CB_PLATFORM_IP", "CB_EDGE_IP", "CB_ADAPTERS_ROOT_DIR", "CB_SERVICE_ACCOUNT", "CB_SERVICE_ACCOUNT_TOKEN"]
    
    for var in possible_vars:
        if var in env:
            print("Setting config from environment variable: " + var)
            CB_CONFIG[var] = env[var]

    #TODO Add implementation specific environment variables here


def parse_args(argv):
    """Parse the command line arguments"""

    parser = argparse.ArgumentParser(description='ClearBlade Adapter')
    parser.add_argument('-systemKey', dest="CB_SYSTEM_KEY", help='The System Key of the ClearBlade \
                        Plaform "System" the adapter will connect to.')

    parser.add_argument('-systemSecret', dest="CB_SYSTEM_SECRET", help='The System Secret of the \
                        ClearBlade Plaform "System" the adapter will connect to.')

    parser.add_argument('-deviceID', dest="deviceID", help='The id/name of the device that will be used for device \
                        authentication against the ClearBlade Platform or Edge, defined \
                        within the devices table of the ClearBlade platform.')

    parser.add_argument('-activeKey', dest="activeKey", help='The active key of the device that will be used for device \
                        authentication against the ClearBlade Platform or Edge, defined within \
                        the devices table of the ClearBlade platform.')

    parser.add_argument('-cb_service_account', dest="CB_SERVICE_ACCOUNT", help='The id/name of the device service accountthat will be used for \
                        authentication against the ClearBlade Platform or Edge, defined \
                        within the devices table of the ClearBlade platform.')

    parser.add_argument('-cb_service_account_token', dest="CB_SERVICE_ACCOUNT_TOKEN", help='The token of the device service account that will be used for device \
                        authentication against the ClearBlade Platform or Edge, defined within \
                        the devices table of the ClearBlade platform.')

    parser.add_argument('-httpUrl', dest="httpURL", default="http://localhost", \
                        help='The HTTP URL of the ClearBlade Platform or Edge the adapter will \
                        connect to. The default is https://localhost.')

    parser.add_argument('-httpPort', dest="httpPort", default="9000", \
                        help='The HTTP Port of the ClearBlade Platform or Edge the adapter will \
                        connect to. The default is 9000.')

    parser.add_argument('-messagingUrl', dest="messagingURL", default="localhost", \
                        help='The MQTT URL of the ClearBlade Platform or Edge the adapter will \
                        connect to. The default is https://localhost.')

    parser.add_argument('-messagingPort', dest="messagingPort", type=int, default=1883, \
                        help='The MQTT Port of the ClearBlade Platform or Edge the adapter will \
                        connect to. The default is 9000.')

    parser.add_argument('-adapterSettingsCollection', dest="adapterSettingsCollectionName", \
                        default="", \
                        help='The name of the ClearBlade Platform data collection which contains \
                        runtime configuration settings for the adapter. The default is "".')

    parser.add_argument('-adapterSettingsItem', dest="adapterSettingsItemID", default="", \
                        help='The "item_id" of the row, within the ClearBlade Platform data \
                        collection which contains runtime configuration settings, that should \
                        be used to configure the adapter. The default is "".')

    parser.add_argument('-requestTopicRoot', dest="requestTopicRoot", default="edge/command/request", \
                        help='The MQTT topic this adapter will subscribe to in order to receive command requests. \
                        The default is "edge/command/request".')

    parser.add_argument('-responseTopicRoot', dest="responseTopicRoot", default="edge/command/response", \
                        help='The MQTT topic this adapter will publish to in order to send command responses. \
                        The default is "edge/command/response".')

    parser.add_argument('-logLevel', dest="logLevel", default="INFO", choices=['CRITICAL', \
                        'ERROR', 'WARNING', 'INFO', 'DEBUG'], help='The level of logging that \
                        should be utilized by the adapter. The default is "INFO".')

    parser.add_argument('-logCB', dest="logCB", default=False, action='store_true',\
                        help='Flag presence indicates logging information should be printed for \
                        ClearBlade libraries.')

    parser.add_argument('-logMQTT', dest="logMQTT", default=False, action='store_true',\
                        help='Flag presence indicates MQTT logs should be printed.')

    #TODO Add implementation specific command line arguments here

    args = vars(parser.parse_args(args=argv[1:]))
    for var in args:
        if args[var] != "" and args[var] != None:
            print("Setting config from command line argument: " + var)
            CB_CONFIG[var] = args[var]


def check_required_config():
    """Verify all required config options were provided via environment variables or command line arguments"""
    if "CB_SYSTEM_KEY" not in CB_CONFIG:
        logging.error("System Key is required, can be provided with CB_SYSTEM_KEY environment variable or --systemKey command line argument")
        exit(-1)
    if not "CB_SYSTEM_SECRET" in CB_CONFIG:
        logging.error("System Secret is required, can be provided with CB_SYSTEM_SECRET environment variable or --systemSecret command line argument")
        exit(-1)

    if "deviceID" in CB_CONFIG and CB_CONFIG["deviceID"] != "" and CB_CONFIG["deviceID"] != None:
        if "activeKey" not in CB_CONFIG:
            logging.error("Device Active Key is required when a deviceID is specified, can be provided with the --activeKey command line argument")
            exit(-1)
    elif "CB_SERVICE_ACCOUNT" in CB_CONFIG and CB_CONFIG["CB_SERVICE_ACCOUNT"] != "" and CB_CONFIG["CB_SERVICE_ACCOUNT"] != None:
        if "CB_SERVICE_ACCOUNT_TOKEN" not in CB_CONFIG:
            logging.error("Device Service Account Token is required when a Service Account is specified, can be provided with the CB_SERVICE_ACCOUNT_TOKEN enviornment variable or --cb_service_account_token command line argument")
            exit(-1)
    else:
        logging.error("Device ID/Active Key or Service Account Name and Token are required")
        exit(-1)
    logging.debug("Adapter Config Looks Good!")

# Parse and Validate all args
parse_env_variables(os.environ)
parse_args(sys.argv)   
check_required_config()

# System credentials
CB_SYSTEM = System(CB_CONFIG['CB_SYSTEM_KEY'], CB_CONFIG['CB_SYSTEM_SECRET'], CB_CONFIG['httpURL'] + ":" + CB_CONFIG["httpPort"] )

uid = None

if 'deviceID' in CB_CONFIG:
    uid = CB_SYSTEM.Device(CB_CONFIG['deviceID'], CB_CONFIG['activeKey'])
elif 'CB_SERVICE_ACCOUNT' in CB_CONFIG:
    uid = CB_SYSTEM.Device(CB_CONFIG['CB_SERVICE_ACCOUNT'], authToken=CB_CONFIG['CB_SERVICE_ACCOUNT_TOKEN'])
else:
    print("Device Name/Active Key or Device Service Account/Token not provided")
    exit(-1)

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