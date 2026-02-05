#!/bin/bash

# Simple test script to verify the Traffic Classifier is working
# This script will start a basic test scenario

echo "=========================================="
echo "Traffic Classifier SDN - Quick Test"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo ./test_classifier.sh"
    exit 1
fi

# Clean up any previous Mininet instances
echo "Cleaning up previous Mininet instances..."
mn -c > /dev/null 2>&1

echo ""
echo "This script will:"
echo "1. Start a simple Mininet topology"
echo "2. Generate some test traffic"
echo "3. Show you how the classifier works"
echo ""
echo "Press Ctrl+C to stop at any time"
echo ""

# Check if classifier script exists
if [ ! -f "traffic_classifier.py" ]; then
    echo "Error: traffic_classifier.py not found"
    echo "Please run this script from the project directory"
    exit 1
fi

# Start the classifier in the background
echo "Starting traffic classifier with Logistic Regression..."
python3 traffic_classifier.py logistic > classifier_output.log 2>&1 &
CLASSIFIER_PID=$!

# Wait for classifier to initialize
sleep 3

# Check if classifier is still running
if ! ps -p $CLASSIFIER_PID > /dev/null; then
    echo "Error: Classifier failed to start"
    echo "Check classifier_output.log for details"
    cat classifier_output.log
    exit 1
fi

echo "Classifier started (PID: $CLASSIFIER_PID)"
echo ""

# Start Mininet and run a simple test
echo "Starting Mininet topology..."
echo "This will create a network with 3 hosts and 1 switch"
echo ""

# Create a Python script to run in Mininet
cat > /tmp/mininet_test.py << 'EOF'
#!/usr/bin/python3

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
import time

def test_network():
    print("Creating network topology...")
    net = Mininet(controller=RemoteController, switch=OVSSwitch)
    
    print("Adding controller...")
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)
    
    print("Adding switch...")
    s1 = net.addSwitch('s1')
    
    print("Adding hosts...")
    h1 = net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2')
    h3 = net.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3')
    
    print("Creating links...")
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    
    print("Starting network...")
    net.start()
    
    print("\nNetwork is ready!")
    print("Generating test traffic...")
    print("-" * 50)
    
    # Generate some ping traffic
    print("\n1. Testing ping traffic (h1 -> h2)...")
    h1.cmd('ping -c 5 10.0.0.2 &')
    time.sleep(6)
    
    print("\n2. Testing ping traffic (h2 -> h3)...")
    h2.cmd('ping -c 5 10.0.0.3 &')
    time.sleep(6)
    
    print("\n3. Testing ping traffic (h1 -> h3)...")
    h1.cmd('ping -c 5 10.0.0.3 &')
    time.sleep(6)
    
    print("\n" + "=" * 50)
    print("Test complete!")
    print("Check the classifier output above to see traffic classification")
    print("=" * 50)
    print("\nYou can now interact with the network using Mininet CLI")
    print("Try commands like:")
    print("  - pingall")
    print("  - h1 ping h2")
    print("  - iperf h1 h2")
    print("\nType 'exit' to stop the network")
    print("")
    
    CLI(net)
    
    print("\nStopping network...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    test_network()
EOF

# Run the Mininet test
python3 /tmp/mininet_test.py

# Cleanup
echo ""
echo "Stopping classifier..."
kill $CLASSIFIER_PID 2>/dev/null

echo "Cleaning up..."
mn -c > /dev/null 2>&1
rm -f /tmp/mininet_test.py

echo ""
echo "Test completed!"
echo "Check classifier_output.log for detailed output"
echo ""
