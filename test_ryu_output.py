
import subprocess
import time

cmd = "ryu-manager simple_monitor_13.py"
p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

print("Started ryu-manager, waiting for output...")
start_time = time.time()
try:
    while time.time() - start_time < 20:
        line = p.stdout.readline()
        if not line:
            break
        print(f"DEBUG: {line}")
finally:
    p.terminate()
