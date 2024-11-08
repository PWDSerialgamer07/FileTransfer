import socket
import threading
import time
import re

# Discovery settings
DISCOVERY_PORT = 5000
DISCOVERY_MESSAGE = b'DISCOVERY'
RESPONSE_MESSAGE = b'RESPONSE'
BLOCKED_IP = "25.34.22.246"  # IP to explicitly block because I have no idea how to auto block it

def get_lan_ip():
    """Attempts to retrieve the local IP on the LAN"""
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    # Option 1: Automatically pick IP based on LAN IP pattern, like 192.168.x.x or 10.x.x.x
    for ip in ips:
        if re.match(r"^(192\.168|10\.)", ip):  # Adjust pattern if needed
            return ip
    # Option 2: Fallback if no match found, just pick the first
    return ips[0] if ips else "127.0.0.1"

LOCAL_IP = get_lan_ip()  # Store the selected local IP to avoid self-discovery

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
                # Ignore responses from self or blocked IP
                if data == RESPONSE_MESSAGE and addr[0] != LOCAL_IP and addr[0] != BLOCKED_IP:
                    print(f"Found device at {addr[0]}")
            except socket.timeout:
                break

def listen_for_discovery():
    """Listens for discovery messages and responds to them."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', DISCOVERY_PORT))
        while True:
            data, addr = s.recvfrom(1024)
            # Ignore discovery requests from self or blocked IP
            if data == DISCOVERY_MESSAGE and addr[0] != LOCAL_IP and addr[0] != BLOCKED_IP:
                print(f"Discovery request received from {addr[0]}")
                s.sendto(RESPONSE_MESSAGE, addr)

# Run both discovery and listening in separate threads
def main():
    print(f"Detected local IP for LAN: {LOCAL_IP}")
    listener_thread = threading.Thread(target=listen_for_discovery, daemon=True)
    listener_thread.start()
    
    # Periodically run discovery
    while True:
        discover_devices()
        time.sleep(10)  # Wait a bit before next discovery

if __name__ == "__main__":
    main()
