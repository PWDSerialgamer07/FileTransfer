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


def receive_discovery() -> None:
    """
    Send discovery message over UDP to find devices on the network
    """
    local_ip = get_local_ip()
    while True:
        # ds for discovery receive
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as dr:
            dr.bind(('0.0.0.0', DISCOVERY_PORT))
            try:
                data, addr = dr.recvfrom(1024)
                # This is stupid \/
                if data == DISCOVERY_MESSAGE and addr[0] != local_ip and addr[0] not in [d['ip'] for d in found_devices]:
                    log_printer.info(
                        f"Found device at {addr[0]}, responding")
                    dr.sendto(DISCOVERY_MESSAGE, (addr[0], DISCOVERY_PORT))
                    with devices_lock:
                        if addr[0] not in [d['ip'] for d in found_devices]:
                            found_devices.append(
                                {'index': len(found_devices) + 1, 'ip': addr[0]})

            except socket.timeout:
                break


def receive_handshake():
    local_ip = get_local_ip()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as rh:
        rh.bind(('0.0.0.0', HANDSHAKE_PORT))
        while True:
            try:
                data, addr = rh.recvfrom(1024)
                if addr[0] == local_ip or data != HANDSHAKE_MESSAGE:
                    continue
                log_printer.info(f"Received handshake from {addr[0]}")

                with devices_lock:
                    current_time = time.time()
                    device = next(
                        (d for d in found_devices if d['ip'] == addr[0]), None)

                    # If device exists and enough time has passed since the last handshake, respond
                    if device:
                        last_handshake = device.get('last_handshake', 0)
                        if current_time - last_handshake > TIMEOUT:
                            rh.sendto(HANDSHAKE_MESSAGE,
                                      (addr[0], HANDSHAKE_PORT))
                            log_printer.info(f"Responded to {addr[0]}")
                            device['last_handshake'] = current_time

                    # If device is new, add it to found_devices with current time
                    else:
                        found_devices.append(
                            {'ip': addr[0], 'last_handshake': current_time})
            except socket.timeout:
                break


def main() -> None:

    receive_discover_thread = threading.Thread(
        target=receive_discovery, daemon=True)
    receive_discover_thread.start()

    receive_thread = threading.Thread(target=receive_handshake, daemon=True)
    receive_thread.start()
    time.sleep(10000)


if __name__ == "__main__":
    main()
