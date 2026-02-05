# Traffic Classifier SDN: Project Documentation

## 1. Project Overview
**Traffic Classifier SDN** is a machine-learning-based network analysis tool designed to identify the application type of network traffic flows (e.g., Video, Voice, Gaming, DNS) within a Software Defined Network (SDN). 

By analyzing statistical properties of traffic (such as packet rate and byte count) rather than inspecting payload contents (Deep Packet Inspection), this system offers a lightweight, privacy-preserving method for network monitoring and Quality of Service (QoS) management.

## 2. System Architecture
The project is built upon three primary pillars:

1.  **Network Simulation (Mininet & OVS)**
    *   Creates a virtual network topology with Open vSwitch (OVS) switches.
    *   Hosts in the network generate traffic using the **D-ITG** (Distributed Internet Traffic Generator) tool.

2.  **Controller & Monitoring (Ryu)**
    *   Uses the **Ryu SDN Framework**.
    *   The `simple_monitor_13.py` script acts as a controller app, querying switches every second to retrieve flow statistics (Packet Counts, Byte Counts).

3.  **Intelligence & Classification (Python ML)**
    *   The `traffic_classifier.py` script aggregates the stats from Ryu.
    *   It calculates complex features (velocity, variance) and feeds them into **Scikit-Learn** models.
    *   It outputs the predicted traffic class in real-time.

## 3. Supported Traffic Classes
The system is trained to recognize the following applications:
*   **0: DNS** (Domain Name System)
*   **1: Game** (Online Gaming traffic)
*   **2: Ping** (ICMP Echo)
*   **3: Quake** (Specific FPS Game Profile)
*   **4: Telnet** (Remote Command Line)
*   **5: Voice** (VoIP calls)

## 4. Technical Deep Dive

### A. Feature Extraction
For every flow (defined by Source IP, Dest IP, and Protocol), the system calculates **12 statistical features** used for classification.

**Forward Direction (Source -> Dest):**
1.  **Forward Delta Packets**: Number of packets sent in the last second.
2.  **Forward Delta Bytes**: Number of bytes sent in the last second.
3.  **Forward Inst PPS**: Instantaneous Packets Per Second.
4.  **Forward Avg PPS**: Average Packets Per Second over flow lifetime.
5.  **Forward Inst BPS**: Instantaneous Bytes Per Second.
6.  **Forward Avg BPS**: Average Bytes Per Second over flow lifetime.

**Reverse Direction (Dest -> Source):**
*   The same 6 metrics are calculated for the return traffic.

### B. Machine Learning Models
The project includes several pre-trained models located in the `models/` directory:
*   **Logistic Regression** (`models/LogisticRegression`)
*   **K-Means Clustering** (`models/KMeans_Clustering`) - Unsupervised learning.
*   **Support Vector Machine** (`models/SVC`)
*   **K-Nearest Neighbors** (`models/KNeighbors`)
*   **Random Forest** (`models/RandomForestClassifier`)
*   **Gaussian Naive Bayes** (`models/GaussianNB`)

## 5. Installation Guide

### Prerequisites
*   **Operating System**: Linux (Ubuntu 20.04 recommended) or WSL2 on Windows.
    *   *Note: Mininet requires Linux kernel features (Network Namespaces). This project will NOT run natively on Windows.*
*   **Python**: Version 3.x.

### Dependencies
Run the following commands to install necessary packages:

```bash
# System updates and tools
sudo apt-get update
sudo apt-get install mininet openvswitch-switch git -y

# Python dependencies for the Controller and ML
pip3 install ryu numpy scikit-learn prettytable
```

### Installing D-ITG
You must install the D-ITG traffic generator to simulate traffic during testing.
```bash
git clone https://github.com/jbucar/ditg
cd ditg/src
make
sudo make install
```

## 6. Usage Instructions

### Step 1: Start the Network Topology
Launch Mininet with a remote controller configuration:
```bash
sudo mn --topo single,3 --mac --switch ovsk --controller remote
```
*   This creates a single switch with 3 hosts.

### Step 2: Run the Classifier
In a separate terminal window, run the classifier script. You must specify the algorithm you wish to use.

**Syntax:**
```bash
sudo python3 traffic_classifier.py [algorithm]
```

**Examples:**
```bash
# Run using Logistic Regression
sudo python3 traffic_classifier.py logistic

# Run using Random Forest
sudo python3 traffic_classifier.py Randomforest
```

### Step 3: Collect Training Data (Optional)
To train your own models, you can run the system in "Training Mode". This will log flow stats to a CSV file for 15 minutes.

```bash
# Syntax: sudo python3 traffic_classifier.py train [label_name]
sudo python3 traffic_classifier.py train voice
```
This will generate a file named `voice_training_data.csv`.

## 7. Directory Structure
```text
/
├── traffic_classifier.py       # Main Application (The "Analyst")
├── simple_monitor_13.py        # Ryu Controller App (The "Watcher")
├── PROJECT_DOCUMENTATION.md    # This detailed documentation
├── models/                     # Folder containing .pkl model files
│   ├── LogisticRegression
│   ├── RandomForestClassifier
│   └── ...
├── datasets/                   # Folder for training CSVs
└── D-IGT_scripts/              # Helper scripts for traffic generation
```

## 8. Troubleshooting

**Issue: "Module not found: ryu"**
*   Ensure you installed Ryu with `pip3 install ryu`.
*   If you are using `sudo`, ensure root uses the same python environment.

**Issue: Mininet errors on Windows**
*   This project **cannot run directly on Windows PowerShell**. You must use a Linux VM or WSL2.

**Issue: "Address already in use"**
*   If the controller fails to start, another controller might be running. Run `sudo mn -c` to clean up Mininet and kill old processes.

**Issue: "ImportError: No module named prettytable"**
*   Run `pip3 install prettytable`.
