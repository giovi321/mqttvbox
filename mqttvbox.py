import paho.mqtt.client as mqtt
import subprocess
import json
import logging

# Configuration
MQTT_BROKER = "192.168.1.65"
MQTT_PORT = 1883
MQTT_USERNAME = "mqtt"
MQTT_PASSWORD = "mqtt_password"
MQTT_TOPIC_PREFIX = "homeassistant"
VBOX_USER = "vbox"


# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize MQTT client
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.enable_logger(logging.getLogger(__name__))

def run_vboxmanage(command):
    """Runs VBoxManage as the vbox user and returns output"""
    try:
        result = subprocess.run(["sudo", "-u", VBOX_USER, "VBoxManage"] + command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"VBoxManage command failed: {e}")
        return None

def list_vms():
    """Returns a list of all VirtualBox VMs"""
    output = run_vboxmanage(["list", "vms"])
    return [line.split('"')[1] for line in output.splitlines() if '"' in line]

def list_running_vms():
    """Returns a list of running VMs"""
    output = run_vboxmanage(["list", "runningvms"])
    return [line.split('"')[1] for line in output.splitlines() if '"' in line]

def get_vm_status(vm_name):
    """Gets the power state of a VM"""
    output = run_vboxmanage(["showvminfo", vm_name, "--machinereadable"])
    for line in output.splitlines():
        if line.startswith("VMState="):
            return line.split("=")[1].strip().strip('"')
    return "unknown"

def publish_mqtt_discovery(vm_name):
    """Publishes MQTT discovery messages for buttons & sensors"""
    device_info = {
        "identifiers": [f"virtualbox_{vm_name}"],
        "name": vm_name,
        "model": "VirtualBox VM",
        "manufacturer": "VirtualBox"
    }

    # Determine the VM status icon based on whether it's running or not
    status_icon = "mdi:server-network" if get_vm_status(vm_name) == "running" else "mdi:server-network-off"

    # Status sensor with dynamic icon based on VM state
    status_topic = f"{MQTT_TOPIC_PREFIX}/sensor/{vm_name}_status/config"
    status_payload = {
        "name": f"{vm_name} Status",
        "state_topic": f"virtualbox/{vm_name}/status",
        "unique_id": f"virtualbox_{vm_name}_status",
        "device_class": "enum",
        "options": ["running", "paused", "stopped", "error", "unknown"],
        "device": device_info,
        "icon": status_icon  # Use the dynamic icon
    }
    mqtt_client.publish(status_topic, json.dumps(status_payload), retain=True)

    # Define all command buttons with icons
    commands = {
        "start": ("start", "mdi:play"),
        "stop": ("stop", "mdi:stop"),
        "acpi": ("acpi", "mdi:stop"),
        "reset": ("reset", "mdi:restart"),
        "pause": ("pause", "mdi:pause"),
        "resume": ("resume", "mdi:play"),
        "rdp_enable": ("rdp_enable", "mdi:monitor"),
        "rdp_disable": ("rdp_disable", "mdi:monitor-off")
    }

    for cmd, (payload, icon) in commands.items():
        button_topic = f"{MQTT_TOPIC_PREFIX}/button/{vm_name}_{cmd}/config"
        button_payload = {
            "name": f"{vm_name} {cmd.capitalize()}",
            "command_topic": "virtualbox/command",
            "payload_press": f"{payload} {vm_name}",
            "unique_id": f"virtualbox_{vm_name}_{cmd}",
            "device": device_info,
            "icon": icon
        }
        mqtt_client.publish(button_topic, json.dumps(button_payload), retain=True)


STATUS_MAPPING = {
    "poweroff": "stopped",
    "running": "running",
    "paused": "paused",
    "error": "error",
    "unknown": "unknown"
}

def update_vm_status():
    for vm in list_vms():
        raw_status = get_vm_status(vm)
        status = STATUS_MAPPING.get(raw_status, "unknown")  # Default to "unknown" if no match
        mqtt_client.publish(f"virtualbox/{vm}/status", status, retain=True)
        logging.info(f"Updated status for {vm}: {status}")

def handle_command(client, userdata, msg):
    """Processes incoming MQTT commands"""
    command = msg.payload.decode()
    logging.info(f"Received command: {command}")

    parts = command.split(" ", 1)
    if len(parts) < 2:
        logging.error("Invalid command format")
        return

    action, vm_name = parts

    if action == "start":
        run_vboxmanage(["startvm", vm_name, "--type", "headless"])
    elif action == "stop":
        run_vboxmanage(["controlvm", vm_name, "poweroff"])
    elif action == "reset":
        run_vboxmanage(["controlvm", vm_name, "reset"])
    elif action == "pause":
        run_vboxmanage(["controlvm", vm_name, "pause"])
    elif action == "resume":
        run_vboxmanage(["controlvm", vm_name, "resume"])
    elif action == "rdp_enable":
        run_vboxmanage(["modifyvm", vm_name, "--vrde", "on"])
    elif action == "rdp_disable":
        run_vboxmanage(["modifyvm", vm_name, "--vrde", "off"])
    elif action == "acpi":
        run_vboxmanage(["controlvm", vm_name, "acpipowerbutton"])

    # Update status after command execution
    update_vm_status()

def on_connect(client, userdata, flags, reason_code, properties):
    try:
        if reason_code == 0:  # Successful connection
            logging.info("Connected to MQTT Broker")
            client.subscribe("virtualbox/command")
            logging.info("Subscribed to virtualbox/command")

            # Publish discovery messages
            for vm in list_vms():
                publish_mqtt_discovery(vm)

            # Publish initial VM statuses
            update_vm_status()
        else:
            logging.error(f"Failed to connect to MQTT Broker, return code {reason_code}")
    except Exception as e:
        logging.error(f"Caught exception in on_connect: {e}")

# Setup MQTT client
mqtt_client.on_connect = on_connect
mqtt_client.on_message = handle_command
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Start MQTT loop
mqtt_client.loop_start()

# Periodically update VM statuses
import time
while True:
    update_vm_status()
    time.sleep(5)
