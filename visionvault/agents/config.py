import os
import uuid
import socket


def get_server_url():
    """Auto-detect server URL based on environment"""
    # Priority 1: User-specified environment variable
    if os.environ.get('AGENT_SERVER_URL'):
        return os.environ.get('AGENT_SERVER_URL')

    # Priority 2: Check if running in same environment as server
    # Look for common local development ports
    local_ports = [7890, 5000, 8000, 3000]

    for port in local_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:  # Port is open
                print(f"✓ Detected local server on port {port}")
                return f'http://127.0.0.1:{port}'
        except:
            pass

    # Priority 3: Default to standard port 5000
    print("ℹ No server detected. Using default: http://127.0.0.1:5000")
    print("  Set AGENT_SERVER_URL environment variable to override")
    return 'http://127.0.0.1:5000'


# Global configuration
SERVER_URL = get_server_url()
AGENT_ID = str(uuid.uuid4())