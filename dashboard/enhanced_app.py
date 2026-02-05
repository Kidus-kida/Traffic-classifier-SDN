#!/usr/bin/env python3
"""
Enhanced Real-Time Traffic Classification Dashboard
Features:
- Live traffic visualization
- WebSocket support for real-time updates
- Interactive charts and graphs
- Flow rule management
- Performance metrics
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdn-traffic-classifier-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

METRICS_FILE = '../metrics/real_time_metrics.json'
FLOW_RULES_FILE = '../flow_rules/auto_generated_rules.json'

def read_metrics():
    """Read current metrics from file"""
    try:
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    return None
                return json.loads(content)
        return None
    except (json.JSONDecodeError, Exception) as e:
        # print(f"Error reading metrics: {e}")
        return None

def read_flow_rules():
    """Read installed flow rules"""
    try:
        if os.path.exists(FLOW_RULES_FILE):
            with open(FLOW_RULES_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        return []
    except (json.JSONDecodeError, Exception) as e:
        # print(f"Error reading flow rules: {e}")
        return []

def background_metrics_updater():
    """Background thread to push updates to connected clients"""
    while True:
        time.sleep(2)  # Update every 2 seconds
        metrics = read_metrics()
        if metrics:
            socketio.emit('metrics_update', metrics, namespace='/live')

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('enhanced_dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """API endpoint for current metrics"""
    metrics = read_metrics()
    return jsonify(metrics if metrics else {'error': 'No metrics available'})

@app.route('/api/flow-rules')
def get_flow_rules():
    """API endpoint for flow rules"""
    rules = read_flow_rules()
    return jsonify({'rules': rules, 'count': len(rules)})

@app.route('/api/stats')
def get_stats():
    """API endpoint for aggregated statistics"""
    metrics = read_metrics()
    if not metrics:
        return jsonify({'error': 'No data available'})
    
    stats = {
        'total_flows': metrics.get('total_flows', 0),
        'active_flows': metrics.get('active_flows', 0),
        'total_bytes': metrics.get('total_bytes', 0),
        'total_packets': metrics.get('total_packets', 0),
        'classification_distribution': metrics.get('classification_stats', {}),
        'qos_distribution': metrics.get('qos_distribution', {}),
        'timestamp': metrics.get('timestamp', datetime.now().isoformat())
    }
    return jsonify(stats)

@socketio.on('connect', namespace='/live')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect', namespace='/live')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_update', namespace='/live')
def handle_update_request():
    """Handle manual update request"""
    metrics = read_metrics()
    emit('metrics_update', metrics if metrics else {'error': 'No data'})

if __name__ == '__main__':
    # Start background updater thread
    updater_thread = threading.Thread(target=background_metrics_updater, daemon=True)
    updater_thread.start()
    
    print("\n" + "="*80)
    print("🌐 ENHANCED SDN TRAFFIC CLASSIFIER DASHBOARD")
    print("="*80)
    print("📊 Dashboard URL: http://localhost:9000")
    print("🔌 WebSocket: Enabled")
    print("📡 Real-time Updates: Every 2 seconds")
    print("="*80 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=9000, debug=False, log_output=True)
