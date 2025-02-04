# VirtualBox MQTT Control with Home Assistant Integration

This script allows you to control your VirtualBox VMs via MQTT and integrates with Home Assistant for automatic discovery of virtual machines. You can start, stop, reset, and enable/disable RDP for your VMs directly from Home Assistant, and monitor their status in real-time. More features are to come.

![image](https://github.com/user-attachments/assets/57b78503-30c2-4278-bf4a-027243a187a0)
![image](https://github.com/user-attachments/assets/70b62fc5-a5cf-4a24-80a5-ae406c758f5e)


# Prerequisites
Before using the script, make sure you have the following installed and configured:
- VirtualBox: Ensure that VirtualBox is installed on the server where your VMs are running.
- MQTT Broker: You will need an MQTT broker (e.g., Mosquitto) to facilitate communication between the script, Home Assistant, and your devices.
- Home Assistant: This script integrates with Home Assistant using MQTT Discovery.
- Python 3.x: The script is written in Python. You need Python 3.x installed.

Additionally, ensure that:
- VirtualBox is installed and accessible on your system.
- The VBoxManage command is available (this is the command-line tool for interacting with VirtualBox).
- The script will be run as a user with permissions to control VirtualBox (e.g., vbox).

# Installation
## Step 1: Install Required Packages
Make sure you have the necessary packages installed on your server.
```
sudo apt update
sudo apt install python3-pip
sudo apt install mosquitto-clients
sudo apt install virtualbox
```

## Step 2: Set Up a Python Virtual Environment
It is recommended to run the script within a Python virtual environment (venv) to avoid conflicts with other Python packages.
- Install virtualenv if you don’t have it:
`sudo apt install python3-venv`
- Create a virtual environment:
`python3 -m venv mqttvbox`
- Activate the virtual environment:
`source mqttvbox/bin/activate`

#Step 3: Install Python Dependencies
Install the paho-mqtt Python library within the virtual environment:
`pip install paho-mqtt`

## Step 4: Download the Script
Clone the GitHub repository:
```
git clone https://github.com/giovi321/mqttvbox.git
cd virtualbox-mqtt-control
```

## Step 5: Configure the Script

Open the script (mqttvbox.py) and update the following variables:

- MQTT_BROKER: Set this to the IP address of your MQTT broker.
- MQTT_PORT = 1883
- MQTT_USERNAME = "MQTT-BROKER-USERNAME"
- MQTT_PASSWORD = "MQTT-BROKER-PASSWORD"
- VBOX_USER: Set this to the user that has permissions to control VirtualBox (e.g., vbox).
- TOPIC_COMMAND: This is the topic the script will listens to for incoming commands and use to publish status updates to.

```
MQTT_BROKER = "MQTT-BROKER-ADDRESS"
MQTT_PORT = 1883
MQTT_USERNAME = "MQTT-BROKER-USERNAME"
MQTT_PASSWORD = "MQTT-BROKER-PASSWORD"
MQTT_TOPIC_PREFIX = "homeassistant"
VBOX_USER = "vbox"
```

## Step 6: Make the Script Executable
Ensure the script is executable. If not, run the following command:
`chmod +x virtualbox_mqtt_control.py`

## Step 7: Run the Script
You can run the script manually using the following command:
`python virtualbox_mqtt_control.py`

For production environments, you can set up a systemd service.

### Creating a systemd service

# Home Assistant Integration

Once the script is running, Home Assistant will automatically discover the virtual machines through MQTT. The discovery messages will create switches and sensors in Home Assistant for each VM.

- Ensure MQTT Integration is Configured in Home Assistant:
    - Go to Configuration > Integrations > MQTT in Home Assistant.
    - Set up your MQTT broker details.

- Home Assistant Entities: The script will automatically create the following entities for each virtual machine:
    - Switches: To start, stop, reset, and enable/disable RDP for each VM.
        - button.virtualbox_<vm_name>_start
        - button.virtualbox_<vm_name>_stop
        - button.virtualbox_<vm_name>_reset
        - button.virtualbox_<vm_name>_rdp_enable
        - button.virtualbox_<vm_name>_rdp_disable
    - Sensors: To show the status of each VM.
        - sensor.virtualbox_<vm_name>_status

# Command Usage
Once the script is running and Home Assistant is integrated, you can control your VirtualBox VMs using the following MQTT commands:
## Start a VM
    Command: start <vm_name>
    Example:
```
    mosquitto_pub -h YOUR_MQTT_BROKER_IP -t "virtualbox/command" -m "start YourVMName"
```

## Force Stop a VM
    Command: force_stop <vm_name>
    Example:
```
    mosquitto_pub -h YOUR_MQTT_BROKER_IP -t "virtualbox/command" -m "force_stop YourVMName"
```

## Reset (Reboot) a VM
    Command: reset <vm_name>
    Example:
```
    mosquitto_pub -h YOUR_MQTT_BROKER_IP -t "virtualbox/command" -m "reset YourVMName"
```

## Get the Status of a Specific VM
    Command: get_status <vm_name>
    Example:
```
    mosquitto_pub -h YOUR_MQTT_BROKER_IP -t "virtualbox/command" -m "get_status YourVMName"
```

## Enable Remote Display (RDP)
    Command: enable_rdp <vm_name>
    Example:
```
    mosquitto_pub -h YOUR_MQTT_BROKER_IP -t "virtualbox/command" -m "enable_rdp YourVMName"
```

## Disable Remote Display (RDP)
    Command: disable_rdp <vm_name>
    Example:
```
    mosquitto_pub -h YOUR_MQTT_BROKER_IP -t "virtualbox/command" -m "disable_rdp YourVMName"
```

# License
The content of this repository is licensed under the WTFPL.

```
Copyright © 2023 giovi321
This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See the LICENSE file for more details.
```
