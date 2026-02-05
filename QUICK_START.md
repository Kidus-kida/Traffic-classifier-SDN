# Quick Start Guide - WSL2

## Prerequisites
- WSL2 installed on Windows
- Ubuntu distribution in WSL2

## Installation Steps

### 1. Access WSL2
Open PowerShell or Windows Terminal and run:
```bash
wsl
```

### 2. Navigate to Project Directory
```bash
cd /mnt/d/Downloads/Traffic-classifier-SDN-main
```

### 3. Run Setup Script
```bash
chmod +x setup_wsl.sh
./setup_wsl.sh
```

This will install:
- Mininet (network emulator)
- Open vSwitch (virtual switch)
- Ryu SDN Framework (controller)
- Python dependencies (numpy, scikit-learn, prettytable)
- D-ITG (traffic generator)

**Note**: The installation may take 10-20 minutes depending on your internet connection.

## Running the Project

### Method 1: Real-time Traffic Classification

#### Terminal 1: Start Mininet Network
```bash
cd /mnt/d/Downloads/Traffic-classifier-SDN-main
sudo mn --topo single,3 --mac --switch ovsk --controller remote
```

This creates a network with:
- 1 OpenFlow switch
- 3 hosts (h1, h2, h3)
- Remote controller connection

#### Terminal 2: Start Traffic Classifier
Open a new WSL terminal and run:
```bash
cd /mnt/d/Downloads/Traffic-classifier-SDN-main
sudo python3 traffic_classifier.py logistic
```

Available algorithms:
- `logistic` - Logistic Regression (recommended for beginners)
- `Randomforest` - Random Forest Classifier
- `svm` - Support Vector Machine
- `kneighbors` - K-Nearest Neighbors
- `kmeans` - K-Means Clustering (unsupervised)
- `gaussiannb` - Gaussian Naive Bayes

#### Terminal 3: Generate Traffic (Optional)
In the Mininet CLI, you can generate traffic:
```bash
# In Mininet prompt:
h1 ping h2
```

### Method 2: Collect Training Data

If you want to collect your own training data:

```bash
sudo python3 traffic_classifier.py train <traffic_type>
```

Example:
```bash
sudo python3 traffic_classifier.py train voice
```

This will:
- Run for 15 minutes
- Collect flow statistics
- Save to `voice_training_data.csv`

## Troubleshooting

### Issue: "Cannot connect to controller"
**Solution**: Make sure the classifier is running before starting traffic in Mininet.

### Issue: "Address already in use"
**Solution**: Clean up Mininet:
```bash
sudo mn -c
```

### Issue: "Module not found: ryu"
**Solution**: Install with pip3:
```bash
pip3 install --user ryu
```
Then add to PATH:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Issue: "Permission denied"
**Solution**: Run with sudo:
```bash
sudo python3 traffic_classifier.py logistic
```

### Issue: Open vSwitch not starting
**Solution**: Start the service manually:
```bash
sudo service openvswitch-switch start
```

## Understanding the Output

The classifier will display a table with:
- **Flow ID**: Unique identifier for the network flow
- **Src MAC**: Source MAC address
- **Dest MAC**: Destination MAC address
- **Traffic Type**: Predicted application (dns, game, ping, quake, telnet, voice)
- **Forward Status**: ACTIVE/INACTIVE
- **Reverse Status**: ACTIVE/INACTIVE

## Stopping the Project

1. In Mininet terminal: Type `exit` or press `Ctrl+D`
2. In Classifier terminal: Press `Ctrl+C`
3. Clean up: `sudo mn -c`

## Next Steps

- Experiment with different ML algorithms
- Generate different types of traffic using D-ITG scripts in `D-IGT_scripts/`
- Collect your own training data
- Explore the pre-trained models in `models/` directory
- Review the Jupyter notebooks (if available) for model training details

## File Structure

```
Traffic-classifier-SDN-main/
├── traffic_classifier.py       # Main application
├── simple_monitor_13.py        # Ryu controller
├── models/                     # Pre-trained ML models
│   ├── LogisticRegression
│   ├── RandomForestClassifier
│   ├── SVC
│   ├── KNeighbors
│   ├── KMeans_Clustering
│   └── GaussianNB
├── datasets/                   # Training datasets
├── D-IGT_scripts/              # Traffic generation scripts
└── PROJECT_DOCUMENTATION.md    # Detailed documentation
```

## Support

For detailed information, see:
- `PROJECT_DOCUMENTATION.md` - Complete technical documentation
- `README.md` - Original project README
