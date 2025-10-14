import subprocess
import sys
import os
import time

# Paths to scripts
main_script = os.path.join(os.path.dirname(__file__), 'main.py')
agent_script = os.path.join(os.path.dirname(__file__), 'local_agent.py')

# Set environment variable for both processes
env = os.environ.copy()
env['AGENT_SERVER_URL'] = 'http://127.0.0.1:7890'

processes = []

try:
    # Start main.py
    p1 = subprocess.Popen([sys.executable, main_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    print(f"Started main.py with PID {p1.pid}")
    processes.append((p1, 'main.py'))

    # Start local_agent.py
    p2 = subprocess.Popen([sys.executable, agent_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    print(f"Started local_agent.py with PID {p2.pid}")
    processes.append((p2, 'local_agent.py'))

    # Print output from both processes
    while True:
        for proc, name in processes:
            # Print all available lines from stdout
            while True:
                out = proc.stdout.readline()
                if not out:
                    break
                print(f"[{name}] {out.decode().rstrip()}")
            # Print all available lines from stderr
            while True:
                err = proc.stderr.readline()
                if not err:
                    break
                print(f"[{name} ERROR] {err.decode().rstrip()}")
        # Check if any process has exited
        for proc, name in processes[:]:
            if proc.poll() is not None:
                print(f"Process {proc.pid} ({name}) exited.")
                # Print any remaining output after exit
                for out in proc.stdout:
                    print(f"[{name}] {out.decode().rstrip()}")
                for err in proc.stderr:
                    print(f"[{name} ERROR] {err.decode().rstrip()}")
                processes.remove((proc, name))
        if not processes:
            print("All processes exited.")
            break
        time.sleep(0.2)
except KeyboardInterrupt:
    print("Stopping processes...")
    for proc, _ in processes:
        proc.terminate()
