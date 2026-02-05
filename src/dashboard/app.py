"""
Simple web dashboard for traffic classifier
Real-time visualization of traffic classification
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'traffic-classifier-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
current_flows: Dict = {}
classification_stats: Dict = {
    'total': 0,
    'by_type': {},
    'recent': []
}
system_health: Dict = {
    'status': 'unknown',
    'components': {},
    'uptime': 0
}


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/flows')
def get_flows():
    """Get current flows"""
    return jsonify({
        'flows': list(current_flows.values()),
        'count': len(current_flows)
    })


@app.route('/api/stats')
def get_stats():
    """Get classification statistics"""
    return jsonify(classification_stats)


@app.route('/api/system')
def get_system():
    """Get system health"""
    return jsonify(system_health)


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')


def update_flow(flow_data: Dict):
    """Update flow information"""
    flow_id = flow_data.get('flow_id')
    if flow_id:
        current_flows[flow_id] = flow_data
        
        # Emit update to connected clients
        socketio.emit('flow_update', flow_data)


def update_classification(classification_data: Dict):
    """Update classification statistics"""
    traffic_type = classification_data.get('traffic_type', 'unknown')
    
    # Update total
    classification_stats['total'] += 1
    
    # Update by type
    if traffic_type not in classification_stats['by_type']:
        classification_stats['by_type'][traffic_type] = 0
    classification_stats['by_type'][traffic_type] += 1
    
    # Add to recent (keep last 100)
    classification_stats['recent'].append({
        'timestamp': datetime.utcnow().isoformat(),
        'traffic_type': traffic_type,
        'confidence': classification_data.get('confidence', 0),
        'flow_id': classification_data.get('flow_id')
    })
    
    if len(classification_stats['recent']) > 100:
        classification_stats['recent'] = classification_stats['recent'][-100:]
    
    # Emit update to connected clients
    socketio.emit('classification_update', classification_data)


def update_system_health(health_data: Dict):
    """Update system health"""
    global system_health
    system_health = health_data
    
    # Emit update to connected clients
    socketio.emit('health_update', health_data)


def load_metrics_periodically():
    """Load metrics from file periodically"""
    # Robust path detection
    base_dir = Path(__file__).parent.parent.parent
    metrics_file = base_dir / 'data' / 'metrics' / 'real_time_metrics.json'
    
    while True:
        try:
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                    
                    # Update stats
                    if 'classifications' in metrics:
                        classification_stats['by_type'] = metrics['classifications']
                    
                    if 'total_flows' in metrics:
                        classification_stats['total'] = metrics['total_flows']
        
        except Exception as e:
            print(f"Error loading metrics: {e}")
        
        time.sleep(5)  # Update every 5 seconds


def run_dashboard(host='0.0.0.0', port=8080, debug=False):
    """Run the dashboard server"""
    # Start metrics loading thread
    metrics_thread = threading.Thread(target=load_metrics_periodically, daemon=True)
    metrics_thread.start()
    
    print(f"Starting dashboard on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_dashboard(debug=True)
