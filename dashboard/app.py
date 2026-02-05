from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Simple in-memory storage for the latest metrics
latest_metrics = {
    'flow_count': 0,
    'throughput': {},
    'latency': {},
    'traffic_distribution': {}
}

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    # In a real system, this would read from InfluxDB
    # For this demo, we'll return the in-memory buffer
    return jsonify(latest_metrics)

# Endpoint for the classifier to send data to
@app.route('/update', methods=['POST'])
def update_metrics():
    # Update logic would go here
    return jsonify({"status": "success"})

if __name__ == '__main__':
    print("🌐 Dashboard starting on http://localhost:8085")
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(host='0.0.0.0', port=8085)
