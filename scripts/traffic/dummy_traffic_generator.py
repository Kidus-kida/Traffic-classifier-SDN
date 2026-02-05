#!/usr/bin/env python3
"""
Dummy Traffic Generator for Dashboard Testing
Simulates network traffic and updates metrics.json for the dashboard.
Use this if you can't run Mininet/Ryu (e.g., on Windows without WSL).
"""

import json
import time
import random
import os
from datetime import datetime

METRICS_FILE = 'metrics/real_time_metrics.json'
TRAFFIC_TYPES = ['dns', 'game', 'ping', 'telnet', 'voice', 'http', 'https', 'ftp', 'ssh', 'video']
QOS_CLASSES = ['REAL_TIME', 'INTERACTIVE', 'BEST_EFFORT', 'BULK', 'NETWORK_CONTROL']

def generate_metrics():
    # Simulate realistic traffic patterns
    total_flows = random.randint(50, 200)
    active_flows = int(total_flows * random.uniform(0.3, 0.8))
    
    # Generate classification stats
    stats = {}
    remaining = active_flows
    for t in TRAFFIC_TYPES[:-1]:
        count = random.randint(0, remaining // 2)
        stats[t] = count
        remaining -= count
    stats[TRAFFIC_TYPES[-1]] = remaining

    # Generate QoS stats
    qos_stats = {}
    remaining_qos = active_flows
    for q in QOS_CLASSES[:-1]:
        count = random.randint(0, remaining_qos // 2)
        qos_stats[q] = count
        remaining_qos -= count
    qos_stats[QOS_CLASSES[-1]] = remaining_qos

    metrics = {
        'timestamp': datetime.now().isoformat(),
        'total_flows': total_flows,
        'active_flows': active_flows,
        'total_packets': random.randint(100000, 10000000),
        'total_bytes': random.randint(10000000, 1000000000),
        'classification_stats': stats,
        'qos_distribution': qos_stats
    }
    
    return metrics

def main():
    print("🚦 Starting Dummy Traffic Generator...")
    print(f"📂 Writing to: {METRICS_FILE}")
    print("Press Ctrl+C to stop")
    
    if not os.path.exists('metrics'):
        os.makedirs('metrics')

    try:
        while True:
            metrics = generate_metrics()
            
            with open(METRICS_FILE, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Updated metrics: {metrics['active_flows']} active flows")
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Generator stopped")

if __name__ == "__main__":
    main()
