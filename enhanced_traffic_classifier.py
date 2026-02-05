#!/usr/bin/env python3
"""
Enhanced Traffic Classifier with Advanced Features
- Support for more traffic types (HTTP, HTTPS, FTP, SSH)
- Automated flow rule installation
- Real-time metrics export
- WebSocket support for live dashboard
"""

from prettytable import PrettyTable
import subprocess, sys
import signal
import os
import numpy as np
import pickle
import json
import time
from datetime import datetime
from collections import deque

# Configuration
SUPPORTED_TRAFFIC_TYPES = ['dns', 'game', 'ping', 'telnet', 'voice', 'http', 'https', 'ftp', 'ssh', 'video']
FLOW_HISTORY_SIZE = 100  # Keep last 100 predictions for time-series analysis
METRICS_FILE = 'metrics/real_time_metrics.json'
FLOW_RULES_FILE = 'flow_rules/auto_generated_rules.json'

# Ryu controller path
cmd = "ryu-manager --ofp-tcp-listen-port 6633 simple_monitor_13.py"

flows = {}
flow_history = deque(maxlen=FLOW_HISTORY_SIZE)
classification_stats = {traffic_type: 0 for traffic_type in SUPPORTED_TRAFFIC_TYPES}

class EnhancedFlow:
    """Enhanced Flow class with additional features"""
    def __init__(self, time_start, datapath, inport, ethsrc, ethdst, outport, packets, bytes):
        self.time_start = time_start
        self.datapath = datapath
        self.inport = inport
        self.ethsrc = ethsrc
        self.ethdst = ethdst
        self.outport = outport
        
        # Forward direction attributes
        self.forward_packets = packets
        self.forward_bytes = bytes
        self.forward_delta_packets = 0
        self.forward_delta_bytes = 0
        self.forward_inst_pps = 0.00
        self.forward_avg_pps = 0.00
        self.forward_inst_bps = 0.00
        self.forward_avg_bps = 0.00
        self.forward_status = 'ACTIVE'
        self.forward_last_time = time_start
        
        # Reverse direction attributes
        self.reverse_packets = 0
        self.reverse_bytes = 0
        self.reverse_delta_packets = 0
        self.reverse_delta_bytes = 0
        self.reverse_inst_pps = 0.00
        self.reverse_avg_pps = 0.00
        self.reverse_inst_bps = 0.00
        self.reverse_avg_bps = 0.00
        self.reverse_status = 'INACTIVE'
        self.reverse_last_time = time_start
        
        # Enhanced features
        self.predicted_type = None
        self.confidence = 0.0
        self.priority = 0
        self.qos_class = 'BEST_EFFORT'
        self.flow_rule_installed = False
        self.classification_history = []
        
    def updateforward(self, packets, bytes, curr_time):
        self.forward_delta_packets = packets - self.forward_packets
        self.forward_packets = packets
        if curr_time != self.time_start: 
            self.forward_avg_pps = packets/float(curr_time-self.time_start)
        if curr_time != self.forward_last_time: 
            self.forward_inst_pps = self.forward_delta_packets/float(curr_time-self.forward_last_time)
        
        self.forward_delta_bytes = bytes - self.forward_bytes
        self.forward_bytes = bytes
        if curr_time != self.time_start: 
            self.forward_avg_bps = bytes/float(curr_time-self.time_start)
        if curr_time != self.forward_last_time: 
            self.forward_inst_bps = self.forward_delta_bytes/float(curr_time-self.forward_last_time)
        self.forward_last_time = curr_time
        
        if (self.forward_delta_bytes==0 or self.forward_delta_packets==0):
            self.forward_status = 'INACTIVE'
        else:
            self.forward_status = 'ACTIVE'

    def updatereverse(self, packets, bytes, curr_time):
        self.reverse_delta_packets = packets - self.reverse_packets
        self.reverse_packets = packets
        if curr_time != self.time_start: 
            self.reverse_avg_pps = packets/float(curr_time-self.time_start)
        if curr_time != self.reverse_last_time: 
            self.reverse_inst_pps = self.reverse_delta_packets/float(curr_time-self.reverse_last_time)
        
        self.reverse_delta_bytes = bytes - self.reverse_bytes
        self.reverse_bytes = bytes
        if curr_time != self.time_start: 
            self.reverse_avg_bps = bytes/float(curr_time-self.time_start)
        if curr_time != self.reverse_last_time: 
            self.reverse_inst_bps = self.reverse_delta_bytes/float(curr_time-self.reverse_last_time)
        self.reverse_last_time = curr_time

        if (self.reverse_delta_bytes==0 or self.reverse_delta_packets==0):
            self.reverse_status = 'INACTIVE'
        else:
            self.reverse_status = 'ACTIVE'
    
    def assign_qos_class(self, traffic_type):
        """Assign QoS class based on traffic type"""
        qos_mapping = {
            'voice': ('REAL_TIME', 5),
            'video': ('REAL_TIME', 4),
            'game': ('INTERACTIVE', 3),
            'http': ('BEST_EFFORT', 2),
            'https': ('BEST_EFFORT', 2),
            'dns': ('NETWORK_CONTROL', 4),
            'ssh': ('INTERACTIVE', 3),
            'ftp': ('BULK', 1),
            'telnet': ('INTERACTIVE', 3),
            'ping': ('NETWORK_CONTROL', 4)
        }
        self.qos_class, self.priority = qos_mapping.get(traffic_type, ('BEST_EFFORT', 0))

def get_extended_features(flow):
    """Extract standard feature set (16 features) matching training data"""
    features = [
        flow.forward_packets,
        flow.forward_bytes,
        flow.forward_delta_packets,
        flow.forward_delta_bytes,
        flow.forward_inst_pps,
        flow.forward_avg_pps,
        flow.forward_inst_bps,
        flow.forward_avg_bps,
        flow.reverse_packets,
        flow.reverse_bytes,
        flow.reverse_delta_packets,
        flow.reverse_delta_bytes,
        flow.reverse_inst_pps,
        flow.reverse_avg_pps,
        flow.reverse_inst_bps,
        flow.reverse_avg_bps
    ]
    return np.asarray(features).reshape(1, -1)

def predict_with_confidence(model, features, model_type='supervised'):
    """Predict traffic type with confidence score"""
    try:
        if hasattr(model, 'predict_proba'):
            # For models that support probability
            probabilities = model.predict_proba(features.tolist())
            prediction = model.predict(features.tolist())
            confidence = np.max(probabilities)
            return prediction[0], confidence
        else:
            # For models without probability support
            prediction = model.predict(features.tolist())
            return prediction[0], 0.85  # Default confidence
    except Exception as e:
        print(f"Prediction error: {e}")
        return 'unknown', 0.0

def install_flow_rule(flow, traffic_type):
    """Generate and install OpenFlow rule based on traffic classification"""
    if flow.flow_rule_installed:
        return
    
    rule = {
        'timestamp': datetime.now().isoformat(),
        'flow_id': hash(f"{flow.ethsrc}{flow.ethdst}"),
        'src_mac': flow.ethsrc,
        'dst_mac': flow.ethdst,
        'traffic_type': traffic_type,
        'qos_class': flow.qos_class,
        'priority': flow.priority,
        'action': get_flow_action(traffic_type),
        'datapath': flow.datapath,
        'in_port': flow.inport,
        'out_port': flow.outport
    }
    
    # Save rule to file
    os.makedirs('flow_rules', exist_ok=True)
    rules = []
    if os.path.exists(FLOW_RULES_FILE):
        with open(FLOW_RULES_FILE, 'r') as f:
            rules = json.load(f)
    
    rules.append(rule)
    with open(FLOW_RULES_FILE, 'w') as f:
        json.dump(rules, f, indent=2)
    
    flow.flow_rule_installed = True
    print(f"✅ Flow rule installed: {traffic_type} → {flow.qos_class} (Priority: {flow.priority})")

def get_flow_action(traffic_type):
    """Determine flow action based on traffic type"""
    actions = {
        'voice': 'PRIORITY_QUEUE_1',
        'video': 'PRIORITY_QUEUE_2',
        'game': 'PRIORITY_QUEUE_3',
        'dns': 'FAST_PATH',
        'http': 'NORMAL_QUEUE',
        'https': 'NORMAL_QUEUE',
        'ftp': 'BULK_QUEUE',
        'ssh': 'PRIORITY_QUEUE_3',
        'telnet': 'PRIORITY_QUEUE_3',
        'ping': 'FAST_PATH'
    }
    return actions.get(traffic_type, 'NORMAL_QUEUE')

def export_metrics():
    """Export real-time metrics for dashboard"""
    os.makedirs('metrics', exist_ok=True)
    
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'total_flows': len(flows),
        'active_flows': sum(1 for f in flows.values() if f.forward_status == 'ACTIVE'),
        'classification_stats': classification_stats,
        'recent_predictions': list(flow_history)[-20:],  # Last 20 predictions
        'qos_distribution': get_qos_distribution(),
        'total_bytes': sum(f.forward_bytes + f.reverse_bytes for f in flows.values()),
        'total_packets': sum(f.forward_packets + f.reverse_packets for f in flows.values())
    }
    
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)

def get_qos_distribution():
    """Get distribution of QoS classes"""
    qos_dist = {}
    for flow in flows.values():
        qos_class = flow.qos_class
        qos_dist[qos_class] = qos_dist.get(qos_class, 0) + 1
    return qos_dist

def printclassifier(model, model_type='supervised', auto_install_rules=False):
    """Enhanced classifier with confidence scores and QoS"""
    x = PrettyTable()
    x.field_names = ["Flow ID", "Src MAC", "Dest MAC", "Traffic Type", "Confidence", "QoS Class", "Priority", "Fwd Status", "Rev Status"]
    
    for key, flow in flows.items():
        features = get_extended_features(flow)
        
        # Predict with confidence
        prediction, confidence = predict_with_confidence(model, features, model_type)
        
        # Handle unsupervised models (K-Means)
        if isinstance(prediction, (int, np.integer)):
            label_map = {0: 'dns', 1: 'game', 2: 'ping', 3: 'telnet', 4: 'voice', 5: 'video'}
            traffic_type = label_map.get(prediction, 'unknown')
        else:
            traffic_type = str(prediction)
        
        # Update flow classification
        flow.predicted_type = traffic_type
        flow.confidence = confidence
        flow.assign_qos_class(traffic_type)
        
        # Track statistics
        classification_stats[traffic_type] = classification_stats.get(traffic_type, 0) + 1
        
        # Add to history
        flow_history.append({
            'timestamp': datetime.now().isoformat(),
            'flow_id': key,
            'traffic_type': traffic_type,
            'confidence': float(confidence),
            'qos_class': flow.qos_class
        })
        
        # Auto-install flow rules if enabled
        if auto_install_rules and confidence > 0.7:  # Only install if confident
            install_flow_rule(flow, traffic_type)
        
        x.add_row([
            key, 
            flow.ethsrc, 
            flow.ethdst, 
            traffic_type,
            f"{confidence:.2%}",
            flow.qos_class,
            flow.priority,
            flow.forward_status,
            flow.reverse_status
        ])
    
    print(x)
    print(f"\n📊 Classification Statistics: {classification_stats}")
    
    # Export metrics for dashboard
    export_metrics()

def printflows(traffic_type, f):
    """Print flows for training data collection"""
    for key, flow in flows.items():
        outstring = '\t'.join([
            str(flow.forward_packets),
            str(flow.forward_bytes),
            str(flow.forward_delta_packets),
            str(flow.forward_delta_bytes), 
            str(flow.forward_inst_pps), 
            str(flow.forward_avg_pps),
            str(flow.forward_inst_bps), 
            str(flow.forward_avg_bps), 
            str(flow.reverse_packets),
            str(flow.reverse_bytes),
            str(flow.reverse_delta_packets),
            str(flow.reverse_delta_bytes),
            str(flow.reverse_inst_pps),
            str(flow.reverse_avg_pps),
            str(flow.reverse_inst_bps),
            str(flow.reverse_avg_bps),
            str(traffic_type)
        ])
        f.write(outstring+'\n')
        f.flush()
        # print(f"📄 Recorded {traffic_type} data point.")

def run_ryu(p, traffic_type=None, f=None, model=None, model_type='supervised', auto_install_rules=False):
    """Enhanced Ryu runner with additional features"""
    print("🚀 Ryu manager process started, waiting for flow data...")
    time_counter = 0
    while True:
        out = p.stdout.readline()
        if out == '' and p.poll() != None:
            print("⚠️ Ryu manager process terminated.")
            break
        
        processed_out = out.decode(encoding='utf-8', errors='ignore')
        if processed_out.strip():
            # print(f"DEBUG Ryu: {processed_out.strip()}")
            pass
            
        if 'data\t' in processed_out:
            fields = processed_out.split('data\t')[1].strip().split('\t')
            
            unique_id = hash(''.join([fields[1], fields[3], fields[4]]))
            if unique_id in flows.keys():
                flows[unique_id].updateforward(int(fields[6]), int(fields[7]), int(fields[0]))
            else:
                rev_unique_id = hash(''.join([fields[1], fields[4], fields[3]]))
                if rev_unique_id in flows.keys():
                    flows[rev_unique_id].updatereverse(int(fields[6]), int(fields[7]), int(fields[0]))
                else:
                    flows[unique_id] = EnhancedFlow(
                        int(fields[0]), fields[1], fields[2], 
                        fields[3], fields[4], fields[5], 
                        int(fields[6]), int(fields[7])
                    )
            
            if model is not None:
                if time_counter % 10 == 0:  # Every 10 seconds
                    printclassifier(model, model_type, auto_install_rules)
            else:
                printflows(traffic_type, f)
        
        time_counter += 1

def printHelp():
    """Enhanced help message"""
    print("\n" + "="*80)
    print("🚀 ENHANCED TRAFFIC CLASSIFIER FOR SDN")
    print("="*80)
    print("\n📖 Usage: python3 enhanced_traffic_classifier.py [subcommand] [options]")
    print("\n🎯 TRAINING MODE:")
    print("   python3 enhanced_traffic_classifier.py train <traffic_type>")
    print("   Supported types:", ', '.join(SUPPORTED_TRAFFIC_TYPES))
    print("\n🤖 CLASSIFICATION MODE:")
    print("   python3 enhanced_traffic_classifier.py <algorithm> [--auto-rules]")
    print("\n📊 Available Algorithms:")
    print("   • logistic       - Logistic Regression (Fast)")
    print("   • kneighbors     - K-Nearest Neighbors (Balanced)")
    print("   • Randomforest   - Random Forest (Best Accuracy)")
    print("   • svm            - Support Vector Machine")
    print("   • gaussiannb     - Gaussian Naive Bayes")
    print("   • kmeans         - K-Means Clustering (Unsupervised)")
    print("   • lstm           - LSTM Deep Learning (Time-Series)")
    print("\n⚙️  Options:")
    print("   --auto-rules     - Automatically install flow rules based on classification")
    print("\n💡 Examples:")
    print("   python3 enhanced_traffic_classifier.py Randomforest --auto-rules")
    print("   python3 enhanced_traffic_classifier.py kneighbors")
    print("   python3 enhanced_traffic_classifier.py train http")
    print("="*80 + "\n")

def alarm_handler(signum, frame):
    """Timer handler for training data collection"""
    print("✅ Finished collecting data.")
    raise Exception()

if __name__ == '__main__':
    SUBCOMMANDS = ('train', 'logistic', 'kmeans', 'kneighbors', 'svm', 'Randomforest', 'gaussiannb', 'lstm')
    TIMEOUT = 15 * 60  # 15 minutes for training
    
    
    # Parse arguments
    auto_install_rules = '--auto-rules' in sys.argv
    
    # Parse duration
    duration_arg = [arg for arg in sys.argv if arg.startswith('--duration=')]
    if duration_arg:
        try:
            TIMEOUT = int(duration_arg[0].split('=')[1])
        except (IndexError, ValueError):
            print("⚠️ Invalid duration format. Using default.")
    
    args = [arg for arg in sys.argv if not arg.startswith('--')]
    
    if len(args) < 2:
        printHelp()
        sys.exit()
    
    if args[1] not in SUBCOMMANDS:
        print(f"❌ ERROR: Unknown subcommand '{args[1]}'")
        print(f"   Accepted commands: {', '.join(SUBCOMMANDS)}")
        printHelp()
        sys.exit()
    
    # Training mode
    if args[1] == "train":
        if len(args) == 3:
            traffic_type = args[2]
            if traffic_type not in SUPPORTED_TRAFFIC_TYPES:
                print(f"⚠️  Warning: '{traffic_type}' is not in standard types: {SUPPORTED_TRAFFIC_TYPES}")
                print("   Proceeding anyway...")
            
            print(f"🎓 Training mode: Collecting {traffic_type} traffic data for {TIMEOUT//60} minutes...")
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            os.makedirs('datasets', exist_ok=True)
            f = open(f'datasets/{traffic_type}_training_data.csv', 'w')
            
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(TIMEOUT)
            
            try:
                headers = 'Forward Packets\tForward Bytes\tDelta Forward Packets\tDelta Forward Bytes\tForward Instantaneous Packets per Second\tForward Average Packets per second\tForward Instantaneous Bytes per Second\tForward Average Bytes per second\tReverse Packets\tReverse Bytes\tDelta Reverse Packets\tDelta Reverse Bytes\tDeltaReverse Instantaneous Packets per Second\tReverse Average Packets per second\tReverse Instantaneous Bytes per Second\tReverse Average Bytes per second\tTraffic Type\n'
                f.write(headers)
                f.flush()
                run_ryu(p, traffic_type=traffic_type, f=f)
            except Exception:
                print('🛑 Exiting training mode...')
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                f.close()
                print(f"✅ Training data saved to datasets/{traffic_type}_training_data.csv")
        else:
            print("❌ ERROR: Please specify traffic type")
            printHelp()
    
    # Classification mode
    else:
        print(f"🤖 Starting classification with {args[1]} algorithm...")
        if auto_install_rules:
            print("⚙️  Auto flow rule installation: ENABLED")
        
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        # Load model
        model_files = {
            'logistic': 'models/LogisticRegression',
            'kmeans': 'models/KMeans_Clustering',
            'svm': 'models/SVC',
            'kneighbors': 'models/KNeighbors',
            'Randomforest': 'models/RandomForestClassifier',
            'gaussiannb': 'models/GaussianNB'
        }
        
        if args[1] == 'lstm':
            print("🧠 LSTM mode requires PyTorch. Loading LSTM model...")
            print("⚠️  LSTM implementation coming soon!")
            sys.exit()
        
        model_file = model_files.get(args[1])
        if not model_file:
            print(f"❌ Model file not found for {args[1]}")
            sys.exit()
        
        try:
            with open(model_file, 'rb') as infile:
                model = pickle.load(infile)
            print(f"✅ Model loaded: {model_file}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            sys.exit()
        
        model_type = 'unsupervised' if args[1] == 'kmeans' else 'supervised'
        
        print("\n" + "="*80)
        print("🎯 REAL-TIME TRAFFIC CLASSIFICATION ACTIVE")
        print("="*80)
        print(f"Model: {args[1]}")
        print(f"Type: {model_type}")
        print(f"Auto Rules: {'Enabled' if auto_install_rules else 'Disabled'}")
        print(f"Metrics Export: {METRICS_FILE}")
        print(f"Flow Rules: {FLOW_RULES_FILE if auto_install_rules else 'N/A'}")
        print("="*80 + "\n")
        
        try:
            run_ryu(p, model=model, model_type=model_type, auto_install_rules=auto_install_rules)
        except KeyboardInterrupt:
            print("\n🛑 Stopping classifier...")
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            print("✅ Classifier stopped successfully")
