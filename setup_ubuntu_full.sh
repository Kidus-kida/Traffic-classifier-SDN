#!/bin/bash

# ==========================================
# 🐧 Ubuntu / WSL Full Setup Script
# ==========================================

set -e # Exit on error

echo "🚀 Starting Full Installation for Ubuntu..."

# 1. Update System
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get install -y \
    mininet \
    openvswitch-switch \
    git \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    cmake \
    libgtest-dev \
    net-tools \
    iproute2

# 2. Install Python Dependencies
echo "🐍 Installing Python libraries..."

# Add ~/.local/bin to PATH if not there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc
    export PATH=$PATH:$HOME/.local/bin
fi

# Upgrade pip first
pip3 install --user --upgrade pip

# FIX: Ryu requires older setuptools. 
echo "🔧 Downgrading setuptools for Ryu compatibility..."
pip3 install --user "setuptools<58.0.0" "wheel"

echo "📦 Installing Ryu (safely)..."
pip3 install --user --no-build-isolation ryu

echo "📦 Installing other dependencies..."
pip3 install --user eventlet==0.33.3 numpy pandas scikit-learn prettytable flask flask-socketio joblib

# 3. D-ITG Installation (Critical for Traffic Generation)
if ! command -v ITGSend &> /dev/null; then
    echo "⚡ Installing D-ITG (Traffic Generator)..."
    cd /tmp
    rm -rf D-ITG
    git clone https://github.com/jbucar/ditg.git D-ITG
    cd D-ITG/src
    
    # 🩹 FIXES for GCC/Modern C++ Errors
    
    echo "🔧 Patching D-ITG source code..."
    
    # 1. Fix invalid pointer comparisons in traffic.cpp and ITGSend.cpp
    sed -i 's/argv\[h + 2\] <= 0/argv[h + 2] == NULL/g' ITGSend/traffic.cpp
    sed -i 's/argv\[h + 2\] <= 0/argv[h + 2] == NULL/g' ITGSend/ITGSend.cpp
    
    # 2. Fix 'ambiguous reference to size' in ITGDecod.cpp
    # Rename 'int size' to 'int itg_size'
    # Correct path is ITGDec/ITGDecod.cpp
    sed -i 's/int size, flagfilter/int itg_size, flagfilter/g' ITGDec/ITGDecod.cpp
    # Rename assignments and comparisons (carefully to avoid matching struct members like .size)
    sed -i 's/size = fread/itg_size = fread/g' ITGDec/ITGDecod.cpp
    sed -i 's/size = 1;/itg_size = 1;/g' ITGDec/ITGDecod.cpp
    sed -i 's/size = 0;/itg_size = 0;/g' ITGDec/ITGDecod.cpp
    sed -i 's/while (size/while (itg_size/g' ITGDec/ITGDecod.cpp
    sed -i 's/if (size/if (itg_size/g' ITGDec/ITGDecod.cpp
    
    # Compile core binaries.
    # Note: explicit targets might still trigger ITGManager in generic makefiles, causing a linking error.
    # We use '|| true' to ignore that specific error, as long as ITGSend is built.
    echo "🏗️ Compiling core components..."
    make ITGSend ITGRecv ITGLog ITGDec || true
    
    # Verify compilation success of critical tools
    if [[ -f "ITGSend" && -f "ITGRecv" ]]; then
        echo "✅ Core binaries compiled successfully!"
    else
        echo "❌ Critical compilation failure. ITGSend/ITGRecv not found."
        exit 1
    fi
    
    # Manual install (since make install expects ITGManager)
    echo "📦 Installing binaries manually..."
    sudo cp ITGSend /usr/local/bin/
    sudo cp ITGRecv /usr/local/bin/
    sudo cp ITGLog /usr/local/bin/
    sudo cp ITGDec /usr/local/bin/
    
    cd -
    echo "✅ D-ITG Installed successfully!"
else
    echo "✅ D-ITG is already installed."
fi

# 4. Create Directories
mkdir -p models datasets flow_rules metrics dashboard/templates

echo ""
echo "=========================================="
echo "🎉 Installation Complete!"
echo "=========================================="
echo "You are ready to go. Follow the steps below:"
echo ""
echo "1️⃣  Start Mininet (Terminal 1):"
echo "   sudo mn --topo single,3 --mac --switch ovsk --controller remote"
echo ""
echo "2️⃣  Start Classifier/Trainer (Terminal 2):"
echo "   python3 enhanced_traffic_classifier.py train video"
echo ""
echo "3️⃣  Send Traffic (Terminal 1 - Mininet Prompt):"
echo "   h1 ITGSend D-IGT_scripts/video_script_file -a h2"
echo ""
