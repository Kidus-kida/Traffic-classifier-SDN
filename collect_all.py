
import os
import subprocess
import time
import sys

# Configuration
TRAFFIC_TYPES = ['voice', 'video', 'game', 'https', 'http', 'ssh', 'telnet', 'ping', 'dns'] 
TRAFFIC_SCRIPT_MAP = {
    'voice': 'voice_script_file',
    'video': 'video_script_file',
    'http': 'http_script_file',
    'https': 'https_script_file',
    'ssh': 'ssh_script_file',
    'telnet': 'telnet_script_file',
    'game': 'game_script_file'
}

DURATION = 40 # 40 seconds per type

def collect_data():
    print(f"🚀 Starting automated data collection for {len(TRAFFIC_TYPES)} types...")
    
    for traffic_type in TRAFFIC_TYPES:
        print(f"\n" + "="*50)
        print(f"🔄 Processing: {traffic_type}")
        print(f"="*50)
        
        # 0. Clean up
        print("🧹 Cleanup...")
        subprocess.run("sudo mn -c", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("sudo pkill -9 -f ryu-manager", shell=True)
        subprocess.run("sudo pkill -9 -f enhanced_traffic_classifier.py", shell=True)
        time.sleep(2)

        # 1. Start Classifier
        print("1. Starting Classifier...")
        log_f = open(f"metrics/collect_{traffic_type}.log", "w")
        classifier_proc = subprocess.Popen(["python3", "-u", "enhanced_traffic_classifier.py", "train", traffic_type, f"--duration={DURATION + 30}"], 
                                          stdout=log_f, stderr=log_f, bufsize=1, universal_newlines=True)
        
        print("   Waiting 10s for Ryu...")
        time.sleep(10)
        
        # 2. Run Mininet commands
        print(f"2. Running Mininet with {traffic_type} traffic...")
        mn_cmd = f"sudo mn --topo single,3 --mac --switch ovsk --controller remote,ip=127.0.0.1,port=6633"
        mn = subprocess.Popen(mn_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # We need to feed commands to MN
        print("   -> pingall")
        mn.stdin.write("pingall\n")
        mn.stdin.flush()
        time.sleep(5)
        
        if traffic_type in TRAFFIC_SCRIPT_MAP:
            script = TRAFFIC_SCRIPT_MAP[traffic_type]
            print(f"   -> h2 ITGRecv & h1 ITGSend {script}")
            mn.stdin.write("h2 ITGRecv &\n")
            mn.stdin.write(f"h1 ITGSend D-IGT_scripts/{script} &\n")
        elif traffic_type == 'ping':
            print("   -> h1 ping -i 0.2 h2")
            mn.stdin.write("h1 ping -i 0.2 h2 &\n")
        elif traffic_type == 'dns':
            print("   -> h1 DNS loop")
            mn.stdin.write("h1 bash -c 'while true; do dig @10.0.0.2 example.com; sleep 1; done' &\n")
        
        mn.stdin.flush()
        
        print(f"   ⏱️  Collecting for {DURATION}s...")
        time.sleep(DURATION)
        
        print("3. Stopping...")
        mn.stdin.write("exit\n")
        mn.stdin.flush()
        try:
            mn.wait(timeout=5)
        except:
            pass
        
        classifier_proc.terminate()
        log_f.close()
        
        print(f"✅ Completed {traffic_type}")
        time.sleep(2)

    print("\n🎉 All data collected! Running validation and retraining...")
    subprocess.run("python3 validate_datasets.py", shell=True)
    subprocess.run("python3 retrain_all_models.py", shell=True)

if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Root required")
    collect_data()
