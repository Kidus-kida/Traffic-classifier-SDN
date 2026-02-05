#!/bin/bash
# setup_dashboard.sh
echo "🚀 Setting up Real-Time Dashboard"
sudo apt-get update
sudo apt-get install -y influxdb grafana
sudo pip3 install flask influxdb requests
echo "✅ Dashboard dependencies installed."
