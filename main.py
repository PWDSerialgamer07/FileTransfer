import socket
import threading
import time

BROADCAST_PORT = 5000
FILE_TRANSFER_PORT = 5001
DISCOVERY_MESSAGE = b'DISCOVERY'
BROADCAST_IP = '192.168.1.255'
TIMEOUT = 30  # In seconds
BLOCKED_IP = "25.34.22.246"
devices = []


def get_local_ip():
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


def discover_devices():
    """Sends a discovery message and waits for responses."""
    local_ip = get_local_ip()
    found_devices = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(TIMEOUT)

        print("Sending discovery message...")
        s.sendto(DISCOVERY_MESSAGE, ('<broadcast>', BROADCAST_PORT))

        while True:
            try:
                data, addr = s.recvfrom(1024)
                if data == DISCOVERY_MESSAGE and addr[0] != local_ip and addr[0] != BLOCKED_IP:
                    print(f"Found device at {addr[0]}")
                    found_devices.append({'ip': addr[0]})
            except socket.timeout:
                break

    return found_devices


def main():
    clients = discover_devices()
    handshaked_devices = set()  # Keep track of devices that we've already handshaked with
    last_broadcast_time = time.time()

    while True:
        # Only broadcast every 10 seconds
        if time.time() - last_broadcast_time >= 10:
            for client in clients:
                ip = client['ip']

                # Skip devices we've already handshaked with
                if ip in handshaked_devices:
                    continue

                # Send the broadcast to devices we haven't handshaked with
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as bs:
                    bs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    bs.sendto(DISCOVERY_MESSAGE, (ip, BROADCAST_PORT))

                handshaked_devices.add(ip)  # Mark this device as handshaked

            print(f"Broadcasted handshake to new devices.")
            last_broadcast_time = time.time()

        time.sleep(1)  # Sleep for 1 second to avoid busy waiting


if __name__ == "__main__":
    main()
