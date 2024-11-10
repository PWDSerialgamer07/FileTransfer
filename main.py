import socket
import threading
import time
import subprocess
from tkinter import Tk, filedialog
import tqdm
import os
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.console import Console

DISCOVERY_PORT = 5000
HANDSHAKE_PORT = 5001
DISCOVERY_MESSAGE = b'DISCOVERY'
HANDSHAKE_MESSAGE = b'HANDSHAKE'
BROADCAST_IP = '192.168.1.255'
TIMEOUT = 10  # In seconds, also technically both the timeout and the time between handshakes and discoveries
BLOCKED_IP = "25.34.22.246"
found_devices = []
devices_lock = threading.Lock()
layout = Layout
console = Console()


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


def broadcast_handshake():
    while True:
        # Broadcasts handshake message to the given IPs
        with devices_lock:
            IPs = [device['ip'] for device in found_devices]
        # bh for broadcast handshake
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as bh:
            bh.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            if not IPs:  # If no IPs are provided, log and skip the for loop
                print("No IPs provided, skipping broadcast")
            else:
                for IP in IPs:
                    bh.sendto(HANDSHAKE_MESSAGE, (IP, HANDSHAKE_PORT))
                    # print(f"Sending handshake to {IP}")
            time.sleep(TIMEOUT)


def receive_handshake():
    local_ip = get_local_ip()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as rh:
        rh.bind(('0.0.0.0', HANDSHAKE_PORT))
        while True:
            try:
                data, addr = rh.recvfrom(1024)
                if addr[0] == local_ip or addr[0] == BLOCKED_IP or data != HANDSHAKE_MESSAGE:
                    continue
                # print(f"Received handshake from {addr[0]}")

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
                            # print(f"Responded to {addr[0]}")
                            device['last_handshake'] = current_time

                    # If device is new, add it to found_devices with current time
                    else:
                        found_devices.append(
                            {'ip': addr[0], 'last_handshake': current_time})
            except socket.timeout:
                break


def receive_discovery():
    """
    Listens for discovery messages on the network and responds to them.
    """
    local_ip = get_local_ip()
    while True:
        # ds for discovery receive
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as dr:
            dr.bind(('0.0.0.0', DISCOVERY_PORT))
            try:
                data, addr = dr.recvfrom(1024)
                # This is stupid \/
                if data == DISCOVERY_MESSAGE and addr[0] != local_ip and addr[0] != BLOCKED_IP and addr[0] not in [d['ip'] for d in found_devices]:
                    # print(f"Found device at {addr[0]}, responding")
                    dr.sendto(DISCOVERY_MESSAGE, (addr[0], DISCOVERY_PORT))
                    with devices_lock:
                        if addr[0] not in [d['ip'] for d in found_devices]:
                            found_devices.append(
                                {'index': len(found_devices) + 1, 'ip': addr[0]})

            except socket.timeout:
                break


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

            # print(f"Sending discovery message from {local_ip}...")
            ds.sendto(DISCOVERY_MESSAGE, ('<broadcast>', DISCOVERY_PORT))
            time.sleep(TIMEOUT)  # Changed this one to the TIMEOUT value


def print_found_devices():
    with Live(device_discovery_layout(), console=console, refresh_per_second=4) as live:
        while True:
            with devices_lock:
                live.update(device_discovery_layout())
            # Delay between updates to keep the display responsive
            time.sleep(2)


def get_user_input():
    selected_ip = None
    while selected_ip is None:
        user_input = input("Enter the device index: ").strip()
        with devices_lock:
            try:
                # Try to find the device by index
                index = int(user_input)
                selected_device = next(
                    device for device in found_devices if device['index'] == index)
                selected_ip = selected_device['ip']
            except (ValueError, StopIteration):
                print("Invalid index. Please try again.")

    print(f"Selected device IP: {selected_ip}")
    # After device selection, continue with other logic (e.g., file transfer, etc.)
    # start_file_transfer(selected_ip)


def toggler_layout():
    """
    Toggles between the device discovery layout and the file transfer layout
    once the user selects a device IP.
    """
    selected_ip = None  # Initially, no IP is selected
    # TODO Do this later, I have no idea how to do it


def device_discovery_layout():
    """Creates a layout for displaying found devices."""
    layout.split_column(
        Layout(name="header"),
        Layout(name="body", ratio=3),
        Layout(name="footer")
    )

    # Header
    layout["header"].update(Table(title="Device Discovery"))

    # Body
    table = Table(title="Found Devices")
    table.add_column("Index", justify="center")
    table.add_column("IP Address", justify="center")
    with devices_lock:
        for device in found_devices:
            table.add_row(str(device['index']), device['ip'])
    layout["body"].update(table)

    # Footer
    layout["footer"].update("Press Enter after entering index.")

    return layout


def file_transfer_layout(selected_ip):
    """Creates a layout for file transfer."""
    layout = Layout()
    layout.split_column(
        Layout(name="header"),
        Layout(name="body", ratio=3),
        Layout(name="footer")
    )

    # Header
    layout["header"].update(f"File Transfer with {selected_ip}")

    # Body (for file transfer progress or options)
    layout["body"].update(
        "File transfer details and progress will appear here.")

    # Footer
    layout["footer"].update("Press 'q' to quit file transfer.")

    return layout


def get_user_IP_input():
    """
    Ask the user to select a device index and return the corresponding IP.
    """
    selected_ip = None
    while selected_ip is None:
        user_input = input("Enter the device index: ").strip()
        with devices_lock:
            try:
                # Try to find the device by index
                index = int(user_input)
                selected_device = next(
                    device for device in found_devices if device['index'] == index)
                selected_ip = selected_device['ip']
            except (ValueError, StopIteration):
                print("Invalid index. Please try again.")

    print(f"Selected device IP: {selected_ip}")
    return selected_ip


def main():
    # Start discovery threads (they run in the background)
    send_discover_thread = threading.Thread(target=send_discovery, daemon=True)
    send_discover_thread.start()

    receive_discover_thread = threading.Thread(
        target=receive_discovery, daemon=True)
    receive_discover_thread.start()

    # Allow some time for devices to be discovered
    time.sleep(10)  # Adjust this depending on how long discovery takes

    # Start the display thread (handles device list UI updates)
    display_thread = threading.Thread(target=print_found_devices, daemon=True)
    display_thread.start()

    # Start the user input thread (handles device selection)
    input_thread = threading.Thread(target=get_user_input, daemon=True)
    input_thread.start()

    # Wait for the input thread to finish (this keeps the program running)
    input_thread.join()


if __name__ == "__main__":
    main()
