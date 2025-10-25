import psutil
from typing import List

def terminate_ports(ports: List[int]):
    """
    Terminates all processes using the specified ports.
    Args:
        ports (List[int]): List of port numbers to terminate connections for.
    """
    for port in ports:
        found = False
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port:
                found = True
                pid = conn.pid
                if pid:
                    try:
                        p = psutil.Process(pid)
                        print(f"Terminating process {pid} on port {port}...")
                        p.terminate()
                        p.wait(timeout=3)
                        print(f"Process {pid} terminated.")
                    except Exception as e:
                        print(f"Error terminating process {pid} on port {port}: {e}")
                else:
                    print(f"No PID found for connection on port {port}.")
        if not found:
            print(f"No process found using port {port}.")

if __name__ == "__main__":
    # Example usage: terminate ports 8080 and 5000
    terminate_ports([7890, 5000])

