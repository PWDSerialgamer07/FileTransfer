import socket
import threading
import time
import subprocess
from tkinter import Tk, filedialog
import tqdm
import os
import json
from lib import *

global DISCOVERY_PORT, HANDSHAKE_PORT, TRANSFER_PORT, DISCOVERY_MESSAGE, HANDSHAKE_MESSAGE, BROADCAST_IP, TIMEOUT
devices_lock = threading.Lock()
logger = Logger()
log_printer = logger.LogPrint(logger)
found_devices = []

with open("config.json", mode="r", encoding='utf-8') as f:
    config = json.load(f)
DISCOVERY_PORT = int(config["Discovery_port"])
HANDSHAKE_PORT = int(config["Handshake_port"])
TRANSFER_PORT = int(config["Transfer_port"])
DISCOVERY_MESSAGE = config["Discovery_msg"].encode("utf-8")
HANDSHAKE_MESSAGE = config["Hanshake_msg"].encode("utf-8")
BROADCAST_IP = config["Broadcast_Ip"]
TIMEOUT = int(config["Timeout"])


def get_local_ip():
    # Same as before, returns the local IP of the machine
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except Exception as e:
        print(f"Error: {e}")
        local_ip = '127.0.0.1'  # Fallback to loopback address
    finally:
        s.close()
    return local_ip


def send_discovery():
    """
    Sends discovery messages over UDP broadcast to find devices on the network.
    """
    local_ip = get_local_ip()
    while True:
        # ds for discovery sned
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as ds:
            ds.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            ds.settimeout(TIMEOUT)

            log_printer.info(f"Sending discovery message from {local_ip}...")
            ds.sendto(DISCOVERY_MESSAGE, ('<broadcast>', DISCOVERY_PORT))
            time.sleep(TIMEOUT)  # Changed this one to the TIMEOUT value


def broadcast_handshake():
    while True:
        # Broadcasts handshake message to the given IPs
        with devices_lock:
            IPs = [device['ip'] for device in found_devices]
        # bh for broadcast handshake
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as bh:
            bh.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            if not IPs:  # If no IPs are provided, log and skip the for loop
                log_printer.info("No IPs provided, skipping handshake")
            else:
                for IP in IPs:
                    bh.sendto(HANDSHAKE_MESSAGE, (IP, HANDSHAKE_PORT))
                    # print(f"Sending handshake to {IP}")
            time.sleep(TIMEOUT)


def main() -> None:

    send_discover_thread = threading.Thread(target=send_discovery, daemon=True)
    send_discover_thread.start()

    send_thread = threading.Thread(
        target=broadcast_handshake, daemon=True)
    send_thread.start()
    time.sleep(5000)


if __name__ == "__main__":
    main()
