import socket
import threading
import time
import subprocess
from tkinter import Tk, filedialog
import tqdm
import os
from textual.app import App, ComposeResult
from textual.widgets import Static, Input, Label, Log
from textual.containers import Center, VerticalScroll


DISCOVERY_PORT = 5000
HANDSHAKE_PORT = 5001
DISCOVERY_MESSAGE = b'DISCOVERY'
HANDSHAKE_MESSAGE = b'HANDSHAKE'
BROADCAST_IP = '192.168.1.255'
TIMEOUT = 10  # In seconds, also technically both the timeout and the time between handshakes and discoveries
BLOCKED_IP = "25.34.22.246" # Really don't know what this IP is for so I'm just manually disabling it.
SERVER_DATA_PATH = "server_data" # Where received data is saved
found_devices = []
devices_lock = threading.Lock()


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


def broadcast_handshake(log):
    while True:
        # Broadcasts handshake message to the given IPs
        with devices_lock:
            IPs = [device['ip'] for device in found_devices]
        # bh for broadcast handshake
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as bh:
            bh.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            if not IPs:  # If no IPs are provided, log and skip the for loop
                log.write_line("No IPs provided, skipping handshake")
            else:
                for IP in IPs:
                    bh.sendto(HANDSHAKE_MESSAGE, (IP, HANDSHAKE_PORT))
                    # print(f"Sending handshake to {IP}")
            time.sleep(TIMEOUT)


def receive_handshake(log):
    local_ip = get_local_ip()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as rh:
        rh.bind(('0.0.0.0', HANDSHAKE_PORT))
        while True:
            try:
                data, addr = rh.recvfrom(1024)
                if addr[0] == local_ip or addr[0] == BLOCKED_IP or data != HANDSHAKE_MESSAGE:
                    continue
                log.write_line(f"Received handshake from {addr[0]}")

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
                            log.write_line(f"Responded to {addr[0]}")
                            device['last_handshake'] = current_time

                    # If device is new, add it to found_devices with current time
                    else:
                        found_devices.append(
                            {'ip': addr[0], 'last_handshake': current_time})
            except socket.timeout:
                break


def receive_discovery(log):
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
                    log.write_line(f"Found device at {addr[0]}, responding")
                    dr.sendto(DISCOVERY_MESSAGE, (addr[0], DISCOVERY_PORT))
                    with devices_lock:
                        if addr[0] not in [d['ip'] for d in found_devices]:
                            found_devices.append(
                                {'index': len(found_devices) + 1, 'ip': addr[0]})

            except socket.timeout:
                break


def send_discovery(log):
    """
    Sends discovery messages over UDP broadcast to find devices on the network.
    """
    local_ip = get_local_ip()
    while True:
        # ds for discovery sned
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as ds:
            ds.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            ds.settimeout(TIMEOUT)

            log.write_line(f"Sending discovery message from {local_ip}...")
            ds.sendto(DISCOVERY_MESSAGE, ('<broadcast>', DISCOVERY_PORT))
            time.sleep(TIMEOUT)  # Changed this one to the TIMEOUT value

def TCP_server(log):
    IP = get_local_ip()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Listen for TCP connections
    server.bind(IP)
    server.listen()
    log.write_line("Started listening for TCP connections")
    while True:
        conn, addr = server.accept()
        client_handling_thread = threading.Thread(target=handle_client, args = (conn, addr)) # TODO make handle_client
        client_handling_thread.start()

def handle_client(conn, addr):
    

class Discovery(App):
    CSS_PATH = "Tcss/grid_layout.tcss"

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="ips_returned")
        yield Log(id="console")
        yield Input(placeholder="Enter your choice", id="user_ip_input", type="integer")

    def on_input_submitted(self) -> None:
        self.choose_ip()

    def on_ready(self) -> None:
        log = self.query_one("#console")
        send_discover_thread = threading.Thread(
            target=send_discovery, daemon=True, args=(log,))
        send_discover_thread.start()

        receive_discover_thread = threading.Thread(
            target=receive_discovery, daemon=True, args=(log,))
        receive_discover_thread.start()

        # Can be adjusted, it's just so handshakes don't start without having IPs
        # time.sleep(10)
        # Start the handshake receiving thread
        receive_thread = threading.Thread(
            target=receive_handshake, daemon=True, args=(log,))
        receive_thread.start()
        # Start the handshake sending thread
        send_thread = threading.Thread(
            target=broadcast_handshake, daemon=True, args=(log,))
        send_thread.start()

    def choose_ip(self) -> None:  # I'll do this later
        return
        text_value = self.query_one(Input).value
        try:
            value = int(text_value)
        except ValueError:
            self.query_one("#console").mount(Label("Invalid input"))
            self.query_one("#user_ip_input").value = ""
            return
        self.query_one("#console").mount(Label(f"{value} has been chosen"))
        self.query_one("#user_ip_input").value = ""


def main():  # Remove this later and put it in the Discovery class
    # Start discovery threads (they run in the background)
    send_discover_thread = threading.Thread(target=send_discovery, daemon=True)
    send_discover_thread.start()

    receive_discover_thread = threading.Thread(
        target=receive_discovery, daemon=True)
    receive_discover_thread.start()

    # Allow some time for devices to be discovered
    time.sleep(10)  # Adjust this depending on how long discovery takes

    receive_thread = threading.Thread(target=receive_handshake, daemon=True)
    receive_thread.start()
    # Start the handshake sending thread
    send_thread = threading.Thread(
        target=broadcast_handshake, daemon=True)
    send_thread.start()


if __name__ == "__main__":
    app = Discovery()
    app.run()
