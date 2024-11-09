import socket
import threading
import time

DISCOVERY_PORT = 5000
HANDSHAKE_PORT = 5001
DISCOVERY_MESSAGE = b'DISCOVERY'
HANDSHAKE_MESSAGE = b'HANDSHAKE'
BROADCAST_IP = '192.168.1.255'
TIMEOUT = 10  # In seconds, also technically both the timeout and the time between handshakes and discoveries
BLOCKED_IP = "25.34.22.246"
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


def broadcast_handshake(IPs):
    # Broadcasts handshake message to the given IPs
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as bs:
        bs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if not IPs:  # If no IPs are provided, log and skip the for loop
            print("No IPs provided, skipping broadcast")
        else:
            for IP in IPs:
                bs.sendto(HANDSHAKE_MESSAGE, (IP, HANDSHAKE_PORT))
                print(f"Sending handshake to {IP}")
        time.sleep(TIMEOUT)


def receive_handshake():
    # Handles receiving handshakes
    local_ip = get_local_ip()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as bs:
        bs.bind(('0.0.0.0', HANDSHAKE_PORT))
        while True:
            try:
                data, addr = bs.recvfrom(1024)
                if addr[0] == local_ip or addr[0] == BLOCKED_IP or data != HANDSHAKE_MESSAGE:
                    continue
                print(f"Received handshake from {addr[0]}")
                broadcast_handshake(addr[0])  # Respond back to the device
                print(f"Responded to {addr[0]}")
            except socket.timeout:
                break


def discover_devices():
    """ Continuously sends a discovery message and waits for responses. """
    local_ip = get_local_ip()
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.bind(('0.0.0.0', DISCOVERY_PORT))
            s.settimeout(TIMEOUT)

            print(f"Sending discovery message from {local_ip}...")
            s.sendto(DISCOVERY_MESSAGE, ('<broadcast>', DISCOVERY_PORT))

            try:
                data, addr = s.recvfrom(1024)
                print("Receiving discoveries...")
                if data == DISCOVERY_MESSAGE and addr[0] != local_ip and addr[0] != BLOCKED_IP:
                    print(f"Found device at {addr[0]}, responding")
                    s.sendto(DISCOVERY_MESSAGE, (addr[0], DISCOVERY_PORT))
                    found_devices.append({'ip': addr[0]})
            except socket.timeout:
                break
            time.sleep(TIMEOUT)  # Changed this one to the TIMEOUT value


def main():
    Ips = []
    # Start the discovery thread to continuously send messages
    discover_thread = threading.Thread(target=discover_devices, daemon=True)
    discover_thread.start()

    # Start the handshake receiving thread
    receive_thread = threading.Thread(target=receive_handshake, daemon=True)
    receive_thread.start()
    with devices_lock:
        if found_devices:
            Ips = found_devices[:]
    # Start the handshake sending thread
    send_thread = threading.Thread(
        target=broadcast_handshake, daemon=True, args=(Ips,))
    send_thread.start()

    while True:
        # Main loop logic can go here
        time.sleep(1)


if __name__ == "__main__":
    main()
