#!/bin/bash

# Traffic Classifier SDN - WSL2 Setup Script
# This script installs all dependencies needed to run the project

set -e  # Exit on error

echo "=========================================="
echo "Traffic Classifier SDN - Setup Script"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running in WSL
if ! grep -qi microsoft /proc/version; then
    print_warning "This doesn't appear to be WSL. Continuing anyway..."
fi

# Update system packages
print_status "Updating system packages..."
sudo apt-get update

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt-get install -y \
    mininet \
    openvswitch-switch \
    openvswitch-testcontroller \
    git \
    python3 \
    python3-pip \
    build-essential \
    net-tools \
    iproute2

# Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install --user ryu numpy scikit-learn prettytable

# Check if D-ITG is already installed
if ! command -v ITGSend &> /dev/null; then
    print_warning "Installing D-ITG (optional - for advanced traffic generation)..."
    echo "    Note: D-ITG is optional. The classifier works with ping, iperf, etc."
    
    # Try to build D-ITG
    cd /tmp
    if git clone https://github.com/traffic-generator/D-ITG-2.8.1-r1023.git ditg 2>/dev/null; then
        cd ditg
        if make 2>&1 | tee /tmp/ditg_build.log; then
            sudo make install PREFIX=/usr/local 2>/dev/null || true
            print_status "D-ITG installed successfully"
        else
            print_warning "D-ITG compilation failed (this is OK - it's optional)"
            echo "    The classifier will work fine with other traffic generators"
        fi
        cd - > /dev/null
    else
        print_warning "Could not download D-ITG (this is OK - it's optional)"
    fi
else
    print_status "D-ITG already installed, skipping..."
fi

# Verify installations
echo ""
echo "=========================================="
echo "Verifying Installations"
echo "=========================================="

# Check Mininet
if command -v mn &> /dev/null; then
    print_status "Mininet: $(mn --version 2>&1 | head -n 1)"
else
    print_error "Mininet not found"
fi

# Check Open vSwitch
if command -v ovs-vsctl &> /dev/null; then
    print_status "Open vSwitch: $(ovs-vsctl --version | head -n 1)"
else
    print_error "Open vSwitch not found"
fi

# Check Python packages
echo ""
print_status "Checking Python packages..."
python3 -c "import ryu; print('  - Ryu: OK')" 2>/dev/null || print_error "  - Ryu: NOT FOUND"
python3 -c "import numpy; print('  - NumPy: OK')" 2>/dev/null || print_error "  - NumPy: NOT FOUND"
python3 -c "import sklearn; print('  - Scikit-learn: OK')" 2>/dev/null || print_error "  - Scikit-learn: NOT FOUND"
python3 -c "import prettytable; print('  - PrettyTable: OK')" 2>/dev/null || print_error "  - PrettyTable: NOT FOUND"

# Check D-ITG
if command -v ITGSend &> /dev/null; then
    print_status "D-ITG: OK"
else
    print_error "D-ITG: NOT FOUND"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start Mininet topology:"
echo "   sudo mn --topo single,3 --mac --switch ovsk --controller remote"
echo ""
echo "2. In another terminal, run the classifier:"
echo "   sudo python3 traffic_classifier.py logistic"
echo ""
echo "Available algorithms: logistic, kmeans, kneighbors, svm, Randomforest, gaussiannb"
echo ""
