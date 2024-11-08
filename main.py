import socket
import threading
import os
import netifaces as ni
# import curses

BROADCAST_PORT = 5000
FILE_TRANSFER_PORT = 5001
DISCOVERY_MESSAGE = b'DISCOVERY'


def get_local_ip():
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


def discover_devices():
    # local_ip = get_local_ip()
    devices = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as bs: # BS for broadcast socket
        bs.bind('',BROADCAST_PORT) # Might e possible with broadcast ip



k = get_local_ip()
print(k)


def server():
    # TODO logic to send discovery message if received
    # local_ip = get_local_ip()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ls: # ls for listening socket
        ls.bind('',FILE_TRANSFER_PORT)
        ls.listen()
        conn, addr = ls.accept()
    pass
