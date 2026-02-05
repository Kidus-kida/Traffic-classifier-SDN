# 🚀 Traffic Classifier SDN - Quick Demo Guide

This guide will help you run the AI-powered Traffic Classifier demo on your WSL2 environment.

## ✅ Prerequisites Checked
- **WSL2**: Installed and ready.
- **Dependencies**: Mininet, Oryu, Open vSwitch, Python libraries are all installed.
- **Models**: Retrained successfully using valid data (DNS, Ping).
- **Datasets**: Validated (Corrupted data was filtered out).

---

## 🚨 Critical First Step: Fix Dependencies for Root

Because the classifier runs with `sudo` (to access network interfaces), it needs Python libraries installed for the **root** user.

**Run this command in your WSL terminal:**
```bash
sudo pip3 install prettytable numpy scikit-learn pandas joblib eventlet flask-socketio ryu
```
*(Enter your password if prompted. This fixes the `ModuleNotFoundError`)*

---

## 🏃 Option A: The Easy Way (Launcher)

The easiest way to run the demo is to use the interactive launcher.

1. Open **PowerShell** as Administrator.
2. Navigate to the project folder:
   ```powershell
   cd "d:\Projects\Traffic-classifier-SDN"
   ```
3. Run the launcher:
   ```powershell
   .\launcher.ps1
   ```
4. Choose **Option 2** for a Quick Test or **Option 6** for the Full Dashboard experience.

---

## 👨‍💻 Option B: Manual Quick Test (Command Line)

If you prefer to run commands manually or investigate specific components, follow these steps. You will need **two** open terminals.

### Terminal 1: Start the AI Classifier
This script monitors network traffic and classifies it in real-time.

```bash
# In WSL
cd /mnt/d/Projects/Traffic-classifier-SDN
sudo python3 enhanced_traffic_classifier.py Randomforest
```

### Terminal 2: Start the Network (Mininet)
This simulates a network where we can generate traffic.

```bash
# In WSL (Open a NEW terminal)
cd /mnt/d/Projects/Traffic-classifier-SDN
sudo mn --topo single,3 --mac --switch ovsk --controller remote
```

### generate Traffic
Once Mininet is running in Terminal 2 (you will see the `mininet>` prompt), generate some traffic:

1. **Ping Traffic** (Should be classified as "ping"):
   ```bash
   mininet> h1 ping h2
   ```
   *Watch Terminal 1 to see the classification!*

2. **DNS Traffic** (Should be classified as "dns"):
   ```bash
   mininet> h1 dig @h2 example.com
   ```

---

## 📊 Option C: data Collection (Fixing Empty Datasets)

Since some datasets (Video, Voice, FPS, etc.) are empty, the classifier currently only detects **DNS** and **PING**. To fix this, you need to collect data.

1. **Start Collection Mode**:
   ```bash
   # Terminal 1
   sudo python3 enhanced_traffic_classifier.py train video
   ```
2. **Generate Traffic** (in Mininet):
   ```bash
   # Terminal 2 (Mininet)
   h1 ITGSend D-ITG_scripts/video_script_file -a h2
   ```
3. **Wait**: Let it run for 5-15 minutes.
4. **Retrain**: Run `python3 retrain_all_models.py`.

---

## 🛠️ Troubleshooting

- **"Address already in use"**: If you see this error, run the cleanup command:
  ```bash
  sudo mn -c
  sudo fuser -k 6633/tcp
  ```
- **Permission Denied**: Ensure you use `sudo ` for Mininet and Classifier scripts.
