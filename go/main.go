package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"os/exec"
	"os/signal"
	"strings"
	"syscall"
	"time"

	adapter_library "github.com/clearblade/adapter-go-library"
	"github.com/clearblade/mqtt_parsing"
	"golang.org/x/crypto/ssh"
)

type Connection struct {
	*ssh.Client
	//session *
	password string
}

const (
	adapterName                    = "edge-command-adapter"
	JavascriptISOString            = "2006-01-02T15:04:05.000Z07:00"
	tcpTimeout                     = 10 * time.Second
	tcpIdleTimeout                 = 60 * time.Second
	adapterConfigCollectionDefault = "adapter_config"
)

var (
	adapterConfig *adapter_library.AdapterConfig
)

func main() {
	fmt.Println("Starting command-adapter...")

	err := adapter_library.ParseArguments(adapterName)
	if err != nil {
		log.Fatalf("[FATAL] Failed to parse arguments: %s\n", err.Error())
	}

	adapterConfig, err = adapter_library.Initialize()
	if err != nil {
		log.Fatalf("[FATAL] Failed to initialize: %s\n", err.Error())
	}

	//Connect to the MQTT broker and subscribe to the request topic
	err = adapter_library.ConnectMQTT(adapterConfig.TopicRoot+"/request", cbMessageHandler)
	if err != nil {
		log.Fatalf("[FATAL] Failed to connect MQTT: %s\n", err.Error())
	}

	// wait for signal to stop/kill process to allow for graceful shutdown
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGINT, syscall.SIGTERM)
	sig := <-c

	log.Printf("[INFO] OS signal %s received, gracefully shutting down adapter.\n", sig)
	os.Exit(0)
}

func cbMessageHandler(message *mqtt_parsing.Publish) {
	log.Println("[INFO] cbMessageHandler - request received")
	log.Printf("[DEBUG] handleRequest - Json payload received: %s\n", string(message.Payload))

	var jsonResponse = make(map[string]interface{})
	jsonResponse["request"] = []string{}
	jsonResponse["response"] = []map[string]interface{}{}

	var commands []map[string]interface{}

	if err := json.Unmarshal(message.Payload, &commands); err != nil {
		log.Printf("[ERROR] handleRequest - Error encountered unmarshalling json: %s\n", err.Error())
		// TODO - We probably need to end if we can't parse the JSON
		//addErrorToPayload(jsonResponse, "Error encountered unmarshalling json: "+err.Error())
	} else {
		jsonResponse["request"] = commands
		handleRequest(message.Topic, jsonResponse)
	}
}

func handleRequest(topic mqtt_parsing.TopicPath, jsonResponse map[string]interface{}) {
	// The json request should resemble the following:
	// [
	// 	{
	// 	  "command": "ls -al",
	//		"useSsh": true,
	//    "sshHost": "192.168.1.1,
	//    "sshUser": "theUserName",
	//    "sshPassword": "thepassword",
	// 	},
	// 	{
	// 	  "command": "cd .."
	// 	}
	// ]
	cmds := jsonResponse["request"].([]map[string]interface{})
	for _, command := range cmds {
		_, ok := command["command"]
		if ok {
			//See if ssh needs to be used
			if useSsh, ok := command["useSsh"]; ok && useSsh.(bool) {
				jsonResponse["response"] = append(jsonResponse["response"].([]map[string]interface{}), handleSshCommand(command))
			} else {
				jsonResponse["response"] = append(jsonResponse["response"].([]map[string]interface{}), handleNoSshCommand(command))
			}
		} else {
			log.Printf("[DEBUG] Command not found for id %#s\n", command["id"])
			jsonResponse["response"] = append(jsonResponse["response"].([]map[string]interface{}), createErrorResponse(fmt.Sprintf("Command not found for id %#s\n", command["id"])))
		}
	}

	log.Printf("[DEBUG] Publishing response: %#v\n", jsonResponse)

	//Publish the response
	publish(strings.Replace(topic.Whole, "request", "response", 1), jsonResponse)
}

func handleNoSshCommand(commandRequest map[string]interface{}) map[string]interface{} {
	return execCommand(commandRequest["command"].(string))
}

func handleSshCommand(commandRequest map[string]interface{}) map[string]interface{} {
	//Make sure the other ssh keys exist

	// 	  "command": "ls -al",
	//		"useSsh": true,
	//    "sshHost": "192.168.1.1,
	//    "sshUser": "theUserName",
	//    "sshPassword": "thepassword",

	sshHost, hostOk := commandRequest["sshHost"]
	sshUser, userOk := commandRequest["sshUser"]
	sshPassword, passwordOk := commandRequest["sshPassword"]

	if !hostOk {
		return createErrorResponse(fmt.Sprintf("sshHost not found for id %#s\n", commandRequest["id"]))
	}

	if !userOk {
		return createErrorResponse(fmt.Sprintf("sshUser not found for id %#s\n", commandRequest["id"]))
	}

	if !passwordOk {
		return createErrorResponse(fmt.Sprintf("sshPassword not found for id %#s\n", commandRequest["id"]))
	}

	conn, err := connect(sshHost.(string), sshUser.(string), sshPassword.(string))
	if err != nil {
		return createErrorResponse(fmt.Sprintf("Error connecting to remote server: %s\n", err.Error()))
	}

	defer conn.Close()

	output, err := conn.sendSshCommand(commandRequest["command"].(string))
	if err != nil {
		log.Printf("[ERROR] Error executing command over ssh: %s\n", err.Error())
		return createErrorResponse(output)
	}

	return createSuccessResponse(output)
}

func execCommand(command string) map[string]interface{} {
	log.Printf("[DEBUG] Executing command: %s\n", command)

	cmd := exec.Command("sh", "-c", command)
	var stdout, stderr bytes.Buffer

	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()

	if err != nil {
		log.Printf("cmd.Run() failed with %s\n", err)
		log.Printf("stderr: %s\n", stderr.String())
		return createErrorResponse(stderr.String())
	} else {
		return createSuccessResponse(stdout.String())
	}
}

func connect(addr, user, password string) (*Connection, error) {
	sshConfig := &ssh.ClientConfig{
		User: user,
		Auth: []ssh.AuthMethod{
			ssh.Password(password),
		},
		HostKeyCallback: ssh.HostKeyCallback(func(hostname string, remote net.Addr, key ssh.PublicKey) error { return nil }),
	}

	conn, err := ssh.Dial("tcp", addr, sshConfig)
	if err != nil {
		return nil, err
	}

	return &Connection{conn, password}, nil
}

func (conn *Connection) sendSshCommand(cmds ...string) (string, error) {
	session, err := conn.NewSession()
	if err != nil {
		log.Printf("[ERROR] Error creating new session: %s\n", err.Error())
		return "", err
	}
	defer session.Close()

	modes := ssh.TerminalModes{
		ssh.ECHO:          0,
		ssh.TTY_OP_ISPEED: 14400,
		ssh.TTY_OP_OSPEED: 14400,
	}

	err = session.RequestPty("xterm", 80, 40, modes)
	if err != nil {
		log.Printf("[ERROR] Error associating pty: %s\n", err.Error())
		return "", err
	}

	in, err := session.StdinPipe()
	if err != nil {
		log.Printf("[ERROR] Error associating pty: %s\n", err.Error())
		return "", err
	}

	out, err := session.StdoutPipe()
	if err != nil {
		log.Fatal(err)
	}

	// stdErr, err := session.StderrPipe()
	// if err != nil {
	// 	log.Fatal(err)
	// }

	//var errOut []byte
	var output []byte

	//go conn.readStdErr(in, stdErr, &errOut)
	go conn.readStdOut(in, out, &output)

	cmd := strings.Join(cmds, "; ")
	_, err = session.Output(cmd)

	//log.Printf("[DEBUG] stderr: %s\n", string(errOut))
	log.Printf("[DEBUG] stdout: %s\n", string(output))

	if err != nil {
		return string(output), err
	}

	return string(output), nil
}

func (conn *Connection) readStdOut(in io.WriteCloser, out io.Reader, output *[]byte) {
	var (
		line string
		r    = bufio.NewReader(out)
	)
	for {
		b, err := r.ReadByte()
		if err != nil {
			break
		}

		*output = append(*output, b)

		if b == byte('\n') {
			line = ""
			continue
		}

		line += string(b)

		if strings.HasPrefix(line, "[sudo] password for ") && strings.HasSuffix(line, ": ") {
			_, err = in.Write([]byte(conn.password + "\n"))
			if err != nil {
				break
			}
		}
	}
}

// func (conn *Connection) readStdErr(in io.WriteCloser, err io.Reader, output *[]byte) {
// 	var (
// 		line string
// 		r    = bufio.NewReader(err)
// 	)
// 	for {
// 		b, err := r.ReadByte()
// 		if err != nil {
// 			break
// 		}

// 		*output = append(*output, b)

// 		if b == byte('\n') {
// 			line = ""
// 			continue
// 		}

// 		line += string(b)
// 	}
// }

func createErrorResponse(err string) map[string]interface{} {
	return map[string]interface{}{
		"stdout": "",
		"stderr": err,
		"error":  true,
	}
}

func createSuccessResponse(stdout string) map[string]interface{} {
	return map[string]interface{}{
		"stdout": stdout,
		"stderr": "",
		"error":  false,
	}
}

// Publishes data to a topic
func publish(topic string, data interface{}) {
	b, err := json.Marshal(data)
	if err != nil {
		log.Printf("[ERROR] Failed to stringify JSON: %s\n", err.Error())
		return
	}

	log.Printf("[DEBUG] publish - Publishing to topic %s\n", topic)
	err = adapter_library.Publish(topic, b)
	if err != nil {
		log.Printf("[ERROR] Failed to publish MQTT message to topic %s: %s\n", topic, err.Error())
	}
}
