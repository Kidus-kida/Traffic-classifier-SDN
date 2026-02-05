#!/bin/bash

echo "=========================================="
echo "🚀 Enhanced SDN Traffic Classifier Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root for some commands
check_sudo() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${YELLOW}⚠️  Some commands require sudo privileges${NC}"
    fi
}

# Install system dependencies
install_system_deps() {
    echo -e "${BLUE}📦 Installing system dependencies...${NC}"
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-dev build-essential
        echo -e "${GREEN}✅ System dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠️  apt-get not found. Please install Python 3 manually${NC}"
    fi
}

# Install Python packages
install_python_deps() {
    echo -e "${BLUE}📦 Installing Python packages...${NC}"
    
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
    
    echo -e "${GREEN}✅ Python packages installed${NC}"
}

# Install PyTorch for LSTM
install_pytorch() {
    echo ""
    read -p "Install PyTorch for LSTM deep learning? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🧠 Installing PyTorch...${NC}"
        pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu
        echo -e "${GREEN}✅ PyTorch installed${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping PyTorch. LSTM features will not be available${NC}"
    fi
}

# Create necessary directories
create_directories() {
    echo -e "${BLUE}📁 Creating directories...${NC}"
    
    mkdir -p models
    mkdir -p datasets
    mkdir -p metrics
    mkdir -p flow_rules
    mkdir -p dashboard/templates
    
    echo -e "${GREEN}✅ Directories created${NC}"
}

# Check if models exist
check_models() {
    echo -e "${BLUE}🔍 Checking for pre-trained models...${NC}"
    
    models=("LogisticRegression" "KNeighbors" "RandomForestClassifier" "SVC" "GaussianNB" "KMeans_Clustering")
    missing_models=()
    
    for model in "${models[@]}"; do
        if [ ! -f "models/$model" ]; then
            missing_models+=("$model")
        fi
    done
    
    if [ ${#missing_models[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All models found${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing models: ${missing_models[*]}${NC}"
        echo -e "${YELLOW}   You can train them using: python3 retrain_all_models.py${NC}"
    fi
}

# Check if datasets exist
check_datasets() {
    echo -e "${BLUE}🔍 Checking for training datasets...${NC}"
    
    datasets=("dns" "game" "ping" "telnet" "voice")
    missing_datasets=()
    
    for dataset in "${datasets[@]}"; do
        if [ ! -f "datasets/${dataset}_training_data.csv" ]; then
            missing_datasets+=("$dataset")
        fi
    done
    
    if [ ${#missing_datasets[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All datasets found${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing datasets: ${missing_datasets[*]}${NC}"
        echo -e "${YELLOW}   You can collect them using: python3 enhanced_traffic_classifier.py train <type>${NC}"
    fi
}

# Test imports
test_imports() {
    echo -e "${BLUE}🧪 Testing Python imports...${NC}"
    
    python3 << END
import sys
errors = []

try:
    import numpy
    print("✅ NumPy")
except ImportError:
    errors.append("numpy")
    print("❌ NumPy")

try:
    import pandas
    print("✅ Pandas")
except ImportError:
    errors.append("pandas")
    print("❌ Pandas")

try:
    import sklearn
    print("✅ Scikit-learn")
except ImportError:
    errors.append("scikit-learn")
    print("❌ Scikit-learn")

try:
    import flask
    print("✅ Flask")
except ImportError:
    errors.append("flask")
    print("❌ Flask")

try:
    import flask_socketio
    print("✅ Flask-SocketIO")
except ImportError:
    errors.append("flask-socketio")
    print("❌ Flask-SocketIO")

try:
    import prettytable
    print("✅ PrettyTable")
except ImportError:
    errors.append("prettytable")
    print("❌ PrettyTable")

try:
    import torch
    print("✅ PyTorch (LSTM support)")
except ImportError:
    print("⚠️  PyTorch (optional - for LSTM)")

if errors:
    print(f"\n❌ Missing packages: {', '.join(errors)}")
    sys.exit(1)
else:
    print("\n✅ All required packages installed!")
END

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Import test passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Some packages are missing. Run: pip3 install -r requirements.txt${NC}"
    fi
}

# Display usage instructions
show_usage() {
    echo ""
    echo "=========================================="
    echo "🎉 Setup Complete!"
    echo "=========================================="
    echo ""
    echo -e "${GREEN}Quick Start Guide:${NC}"
    echo ""
    echo "1️⃣  Start Mininet network:"
    echo "   sudo mn --topo single,3 --mac --switch ovsk --controller remote"
    echo ""
    echo "2️⃣  Run traffic classifier:"
    echo "   python3 enhanced_traffic_classifier.py Randomforest --auto-rules"
    echo ""
    echo "3️⃣  Launch web dashboard:"
    echo "   cd dashboard && python3 enhanced_app.py"
    echo "   Then visit: http://localhost:5000"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo "   - ENHANCED_FEATURES_GUIDE.md - Complete feature guide"
    echo "   - SUPERVISED_LEARNING_GUIDE.md - ML algorithms guide"
    echo "   - HOW_TO_USE_KNN.md - KNN usage guide"
    echo ""
    echo -e "${BLUE}🧠 Train LSTM model:${NC}"
    echo "   python3 lstm_classifier.py"
    echo ""
    echo "=========================================="
}

# Main installation flow
main() {
    check_sudo
    echo ""
    
    install_system_deps
    echo ""
    
    create_directories
    echo ""
    
    install_python_deps
    echo ""
    
    install_pytorch
    echo ""
    
    test_imports
    echo ""
    
    check_models
    echo ""
    
    check_datasets
    echo ""
    
    show_usage
}

# Run main installation
main
