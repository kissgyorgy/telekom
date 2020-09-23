package main

import (
	"fmt"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"time"
)

const STICK_URL = "http://192.168.1.1"
const PROFILE_ID = "16" // default value?
const WEB_CONNECTION_APP = "/Volumes/Web Connection/Web Connection.app"

var username = os.Getenv("TELEKOM_STICK_USERNAME")
var password = os.Getenv("TELEKOM_STICK_PASSWORD")
var pin = os.Getenv("TELEKOM_STICK_PIN")

func isConnected() bool {
	resp, err := http.Get(STICK_URL)
	if err != nil {
		return false
	}
	return resp.StatusCode == 200
}

func waitForWebConnectionMount() {
	for {
		err := exec.Command("open", "-a", WEB_CONNECTION_APP).Run()
		if err == nil {
			fmt.Println()
			return
		}
		fmt.Print(".")
		time.Sleep(1 * time.Second)
	}
}

func waitForBoot() {
	for !isConnected() {
		fmt.Print(".")
		time.Sleep(1 * time.Second)
	}
	fmt.Println()
}

// Connect to the internet with the Alcatel 4G LTE modem.
func connect() {
	if !isConnected() {
		fmt.Println("Waiting for Web connection app...")
		waitForWebConnectionMount()
		fmt.Println("Waiting for stick to boot...")
		waitForBoot()
	}

	fmt.Println("Logging in...")
	http.PostForm(STICK_URL+"/goform/setLogin", url.Values{"username": {username}, "password": {password}})
	fmt.Println("Setting PIN...")
	http.PostForm(STICK_URL+"/goform/unlockPIN", url.Values{"pin": {pin}})
	fmt.Println("Connecting...")
	http.PostForm(STICK_URL+"/goform/setWanConnect", url.Values{"profile_id": {PROFILE_ID}})
	fmt.Println("Logging out...")
	http.PostForm(STICK_URL+"/goform/setLogout", nil)
	fmt.Println("Done.")
}

func main() {
	connect()
}
