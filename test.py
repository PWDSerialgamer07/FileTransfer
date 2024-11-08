#this is testing for the discovery logic
import socket
import threading
import time

# Discovery settings
DISCOVERY_PORT = 5000
DISCOVERY_MESSAGE = b'DISCOVERY'
RESPONSE_MESSAGE = b'RESPONSE'


def discover_devices():
    """Sends discovery message over UDP broadcast to find devices on LAN."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(2)  # Time to wait for responses

        print("Sending discovery message...")
        s.sendto(DISCOVERY_MESSAGE, ('<broadcast>', DISCOVERY_PORT))

        while True:
            try:
                data, addr = s.recvfrom(1024)
                if data == RESPONSE_MESSAGE:
                    print(f"Found device at {addr[0]}")
            except socket.timeout:
                break


def listen_for_discovery():
    """Listens for discovery messages and responds to them."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', DISCOVERY_PORT))
        while True:
            data, addr = s.recvfrom(1024)
            if data == DISCOVERY_MESSAGE:
                print(f"Discovery request received from {addr[0]}")
                s.sendto(RESPONSE_MESSAGE, addr)

# Run both discovery and listening in separate threads


def main():
    listener_thread = threading.Thread(
        target=listen_for_discovery, daemon=True)
    listener_thread.start()

    # Periodically run discovery
    while True:
        discover_devices()
        time.sleep(10)  # Wait a bit before next discovery


if __name__ == "__main__":
    main()
