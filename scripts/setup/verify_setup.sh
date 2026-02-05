#!/bin/bash

# Verification script to check if the Traffic Classifier SDN project is ready to run

echo "=========================================="
echo "Traffic Classifier SDN - Verification"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $2 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $2 is NOT installed"
        ((ERRORS++))
        return 1
    fi
}

check_python_module() {
    if python3 -c "import $1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Python module '$1' is available"
        return 0
    else
        echo -e "${RED}✗${NC} Python module '$1' is NOT available"
        ((ERRORS++))
        return 1
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} File exists: $2"
        return 0
    else
        echo -e "${RED}✗${NC} File missing: $2"
        ((ERRORS++))
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} Directory exists: $2"
        return 0
    else
        echo -e "${YELLOW}!${NC} Directory missing: $2"
        ((WARNINGS++))
        return 1
    fi
}

echo "Checking system commands..."
check_command "mn" "Mininet"
check_command "ovs-vsctl" "Open vSwitch"
check_command "python3" "Python 3"
check_command "pip3" "pip3"
check_command "git" "Git"

echo ""
echo "Checking D-ITG installation..."
check_command "ITGSend" "D-ITG (ITGSend)"
check_command "ITGRecv" "D-ITG (ITGRecv)"

echo ""
echo "Checking Python modules..."
check_python_module "ryu"
check_python_module "numpy"
check_python_module "sklearn"
check_python_module "prettytable"
check_python_module "pickle"
check_python_module "subprocess"

echo ""
echo "Checking project files..."
check_file "traffic_classifier.py" "Main classifier script"
check_file "simple_monitor_13.py" "Ryu monitor script"
check_file "PROJECT_DOCUMENTATION.md" "Documentation"

echo ""
echo "Checking project directories..."
check_dir "models" "Models directory"
check_dir "datasets" "Datasets directory"
check_dir "D-IGT_scripts" "D-ITG scripts directory"

echo ""
echo "Checking ML model files..."
if [ -d "models" ]; then
    check_file "models/LogisticRegression" "Logistic Regression model"
    check_file "models/RandomForestClassifier" "Random Forest model"
    check_file "models/SVC" "SVM model"
    check_file "models/KNeighbors" "K-Neighbors model"
    check_file "models/KMeans_Clustering" "K-Means model"
    check_file "models/GaussianNB" "Gaussian NB model"
fi

echo ""
echo "Checking Open vSwitch service..."
if sudo service openvswitch-switch status &> /dev/null; then
    echo -e "${GREEN}✓${NC} Open vSwitch service is running"
else
    echo -e "${YELLOW}!${NC} Open vSwitch service is not running"
    echo "  To start: sudo service openvswitch-switch start"
    ((WARNINGS++))
fi

echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "You're ready to run the project!"
    echo ""
    echo "To start:"
    echo "1. Terminal 1: sudo mn --topo single,3 --mac --switch ovsk --controller remote"
    echo "2. Terminal 2: sudo python3 traffic_classifier.py logistic"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo "The project should still work, but some features may be limited."
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    fi
    echo ""
    echo "Please run the setup script to install missing dependencies:"
    echo "  ./setup_wsl.sh"
fi

echo ""
exit $ERRORS
