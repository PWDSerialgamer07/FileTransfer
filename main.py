import socket
import threading
import os
import time
import netifaces as ni
import ipaddress
import subprocess
from scapy.all import ARP, Ether, srp
# import curses

BROADCAST_PORT = 5000
FILE_TRANSFER_PORT = 5001
DISCOVERY_MESSAGE = b'DISCOVERY'
BROADCAST_IP = '192.168.1.255'
TIMEOUT = 30  # In seconds
devices = []


def get_local_ip():  # Is this even useful? TODO delete it if uneeded
    # AF_INET = IPv4 and SOCK_DGRAM = UDP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a remote server (google's)
        s.connect(('8.8.8.8', 80))
        # Get local IP address used for the connection
        local_ip = s.getsockname()[0]
    except Exception as e:
        print(f"Error: {e}")
        local_ip = '127.0.0.1'  # Fallback to loopback address
    finally:
        s.close()
    return local_ip


def broadcast_handshake(IP=BROADCAST_IP):
    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as bs:
        # Allow broadcast permissions on the socket
        bs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Send discovery message
        bs.sendto(DISCOVERY_MESSAGE, (IP, BROADCAST_PORT))


def receive_handshake():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as bs:
        bs.settimeout(TIMEOUT)
        bs.bind(('', BROADCAST_PORT))  # Bind to the port for receiving data
        while True:
            try:
                data, addr = bs.recvfrom(1024)  # Receive data from any device
                print(f"Received handshake from {addr}")
                if addr not in devices:
                    broadcast_handshake(addr)  # Return discovery message
                    devices.append(addr)
            except socket.timeout:
                # Timeout (so you don't keep broadcasting forever)
                break


def main():
    receive_thread = threading.Thread(target=receive_handshake)
    receive_thread.start()
    while True:
        broadcast_handshake()
        print(f"Broadcasted handshake to {BROADCAST_IP}")
        time.sleep(5)


if __name__ == '__main__':
    main()
