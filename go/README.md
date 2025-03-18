# command-adapter
A ClearBlade Adapter for running shell commands natively in linux and sending the results to a ClearBlade Edge or the ClearBlade Platform

# Warning
This Adapter will enable the execution of any arbitrary shell command on the underlying OS. Use with caution!

# MQTT Topic Structure
The command-adapter adapter utilizes MQTT messaging to communicate with the ClearBlade Platform or ClearBlade Edge. The command-adapter will subscribe to a specific topic in order to handle requests. The command-adapter will publish messages to MQTT topics in order to communicate the results of requests to client applications. The topic structures utilized by the command-adapter are as follows:

  * command-adapter command request: {__TOPIC ROOT__}/receive/request
  * command-adapter command response: {__TOPIC ROOT__}/receive/response

## ClearBlade Platform Dependencies
The command-adapter was constructed to provide the ability to communicate with a _System_ defined in a ClearBlade Platform instance. Therefore, the adapter requires a _System_ to have been created within a ClearBlade Platform instance.

Once a System has been created, artifacts must be defined within the ClearBlade Platform system to allow the adapter to function properly. At a minimum: 

  * A device needs to be created in the Auth --> Devices collection. The device will represent the adapter, or more importantly, the command-adapter device or gateway on which the adapter is executing. The _name_ and _active key_ values specified in the Auth --> Devices collection will be used by the adapter to authenticate to the ClearBlade Platform or ClearBlade Edge.


  * An adapter configuration data collection named `adapter_config` needs to be created in the ClearBlade Platform _system_ and populated with data appropriate to the modbus client adapter adapter. The schema of the data collection should be as follows:

| Column Name      | Column Datatype |
| ---------------- | --------------- |
| adapter_name     | string          |
| topic_root       | string          |
| adapter_settings | string          |

## Adapter Settings Structure
The `adapter_settings` JSON string provided in the `adapter_config` collection is expected to have the following structure. This JSON is how you provide the Adapter with the specific OPC UA Server connection details.

```json
{}
```

## MQTT Message structure

### Request Payload Format
The payload of a command request should have the following format:

```json
/**
 * @typedef {object} CommandRequest Array of shell commands to execute
 * @property {string} command The shell command to execute
 *
 * @example <caption>Example CommandRequest object</caption>
 * {
 *   "command": "ls -al"  
 *   "useSsh": true,
 *   "sshHost": "192.168.1.1,
 *   "sshUser": "theUserName",
 *   "sshPassword": "thepassword",
 * }
 */

/**
 * @typedef {CommandRequest[]} Request Array of shell commands to execute
 *
 * @example <caption>Example Adapter Request</caption>
 * [ 
 *   {
 *     "command": "ls -al"
 *   },
 *   {
 *     "command": "cd .."
 *   }
 * ]
 */
```

### Response Payload Format

```json

/**
 * @typedef {object} CommandResponse
 * @property {string} stdout The standard out content resulting from the execution of the shell command
 * @property {string} stderr The standard error content resulting from the execution of the shell command
 * @property {boolean} error A flag indicating whether or not the execution of the command resulted in an error
 *
 * @example <caption>Example CommandResponse object</caption>
 * {
 *   "stdout": "This is the standard output contents",
 *   "stderr": "This is the standard error contents",
 *   "error": false  
 * }
 */


/**
 * @typedef {Object} Response
 * @param {CommandRequest} request The original request
 * @param {CommandResponse[]} Response.response - The responses to the original requests
 *
 * @example <caption>Example Adapter response</caption>
 * {
 *   "request": [ 
 *     {
 *       "command": "ls -al"
 *     },
 *     {
 *       "command": "cd .."
 *     }
 *   ],
 *   "response": [
 *     {
 *       "stdout": "This is the standard output from the ls -al command",
 *       "stderr": "This is the standard error from the ls -al command",
 *       "error": false  
 *     },
 *     {
 *       "stdout": "This is the standard output from the cd .. command",
 *       "stderr": "This is the standard error from the cd .. command",
 *       "error": false  
 *     }
 *   ]
 * }
 */
```

## Usage

### Environment Variables
   __CB_SYSTEM_KEY__
  * OPTIONAL - Not needed if __systemKey__ command line argument is present
  * The system key of the ClearBLade Platform __System__ the adapter will connect to

   __CB_SYSTEM_SECRET__
  * OPTIONAL - Not needed if __systemSecret__ command line argument is present
  * The system secret of the ClearBLade Platform __System__ the adapter will connect to

   __CB_SERVICE_ACCOUNT__
  * OPTIONAL - Not needed if __CB_SERVICE_ACCOUNT__ command line argument is present
  * The id/name of the device service account that will be used for authentication against the ClearBlade Platform or Edge
  * Defined within the devices collection of the ClearBlade platform.
  * Requires the device to have been defined in the _Devices_ collection within the ClearBlade Platform __System__

   __CB_SERVICE_ACCOUNT_TOKEN__
  * OPTIONAL - Not needed if __cb_service_account_token__ command line argument is present
  * The token of the device service account that will be used for device authentication against the ClearBlade Platform or Edge
  * Defined within the devices table of the ClearBlade platform.
  * Requires the device to have been defined in the _Devices_ collection within the ClearBlade Platform __System__

### Command Line Arguments

### Executing the adapter

`command-adapter -systemKey=<SYSTEM_KEY> -systemSecret=<SYSTEM_SECRET> -platformURL=<PLATFORM_URL> -deviceName=<DEVICE_NAME> -password=<DEVICE_ACTIVE_KEY> -fatalOnDisconnect=<true or false> -logLevel=<LOG_LEVEL>`

   __*Where*__ 

   __systemKey__
  * OPTIONAL - Not needed if __CB_SYSTEM_KEY__ environment variable is present
  * The system key of the ClearBLade Platform __System__ the adapter will connect to

   __systemSecret__
  * OPTIONAL - Not needed if __CB_SYSTEM_SECRET__ environment variable is present
  * The system secret of the ClearBLade Platform __System__ the adapter will connect to
   
   __deviceID__
  * OPTIONAL
  * The device name the adapter will use to authenticate to the ClearBlade Platform
  * Requires the device to have been defined in the _Devices_ collection within the ClearBlade Platform __System__

   __activeKey__
  * REQUIRED
  * The active key the adapter will use to authenticate to the platform or edge
  * Requires the device to have been defined in the _Devices_ collection within the ClearBlade Platform __System__

   __cb_service_account__
  * OPTIONAL - Not needed if __CB_SERVICE_ACCOUNT__ environment variable is present
  * The id/name of the device service account that will be used for authentication against the ClearBlade Platform or Edge
  * Defined within the devices collection of the ClearBlade platform.
  * Requires the device to have been defined in the _Devices_ collection within the ClearBlade Platform __System__
   
   __cb_service_account_token__
  * OPTIONAL - Not needed if __CB_SERVICE_ACCOUNT_TOKEN__ environment variable is present
  * The token of the device service account that will be used for device authentication against the ClearBlade Platform or Edge
  * Defined within the devices table of the ClearBlade platform.
  * Requires the device to have been defined in the _Devices_ collection within the ClearBlade Platform __System__

   __platformURL__
  * REQUIRED 
  * The HTTP URL of the ClearBlade Platform or Edge the adapter will connect to.
  * Defaults to __http://localhost:9000__

   __messagingURL__
  * OPTIONAL
  * The MQTT URL of the ClearBlade Platform or Edge the adapter will connect to.
  * Defaults to __localhost:1883__

   __requestTopicRoot__
  * OPTIONAL 
  * The MQTT topic this adapter will subscribe to in order to receive command requests.
  * Defaults to __edge/command/request__

   __responseTopicRoot__
  * OPTIONAL 
  * The MQTT topic this adapter will publish to in order to send command responses.
  * Defaults to __edge/command/response__

   __logLevel__
  * OPTIONAL
  * The level of runtime logging the adapter should provide.
  * Available log levels:
    * CRITICAL
    * ERROR
    * WARNING
    * INFO
    * DEBUG
  * Defaults to __INFO__

### Adapter compilation
In order to compile the adapter for execution, the following steps need to be performed:

 1. Retrieve the adapter source code  
    * ```git clone git@github.com:ClearBlade/edge-command-adapter.git```
 2. Navigate to the _command-adapter_ directory  
    * ```cd edge-command-adapter```
 3. Compile the adapter
    * ```GOARCH=arm GOARM=5 GOOS=linux go build```
    * ```GOARCH=amd64 GOOS=linux go build```
    * ```GOARCH=amd64 GOOS=linux go build -o command-adapter```