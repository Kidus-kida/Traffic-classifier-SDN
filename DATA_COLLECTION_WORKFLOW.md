# 🧪 Data Collection Workflow (Option 1)

This guide shows you how to generate your own high-quality training datasets using Mininet and D-ITG.

**You will need 2 Terminal Windows.**

---

## 🟢 Terminal 1: The Network (Mininet)

1.  **Start Mininet** (Run as root):
    ```bash
    sudo mn --topo single,3 --mac --switch ovsk --controller remote
    ```
    *You should see the `mininet>` prompt.*

2.  **Start the D-ITG Receiver on Host 2**:
    *Run this ONCE in the mininet prompt:*
    ```bash
    mininet> h2 ITGRecv &
    ```
    *(Wait 5 seconds for it to initialize)*

---

## 🔵 Terminal 2: The Collector (AI)

1.  **Navigate to the project folder:**
    ```bash
    cd /path/to/Traffic-classifier-SDN-main
    ```

2.  **Start Collecting Data for a specific Traffic Type:**
    *Example: Collecting VIDEO traffic*
    ```bash
    python3 enhanced_traffic_classifier.py train video
    ```
    *It will say "Collecting video traffic data..."*

---

## ⚡ Generating the Traffic (Back to Terminal 1)

**While Terminal 2 is running**, go back to the `mininet>` prompt in Terminal 1 and fire the traffic generator!

### 1. For Video Traffic 🎬
```bash
mininet> h1 ITGSend D-IGT_scripts/video_script_file -a h2
```

### 2. For HTTP Traffic 🌐
```bash
mininet> h1 ITGSend D-IGT_scripts/http_script_file -a h2
```

### 3. For SSH Traffic 🔐
```bash
mininet> h1 ITGSend D-IGT_scripts/ssh_script_file -a h2
```

### 4. For FTP Traffic 📁
```bash
mininet> h1 ITGSend D-IGT_scripts/ftp_script_file -a h2
```

### 5. For Voice (VoIP) Traffic 🎤
```bash
mininet> h1 ITGSend D-IGT_scripts/voice_script_file -a h2
```

---

## 🔄 Repeat Process

1.  **Wait** for the collector in Terminal 2 to finish (15 minutes by default).
    *   *Tip: You can change `TIMEOUT` in `enhanced_traffic_classifier.py` if 15 mins is too long for testing (e.g., set to 300 for 5 mins).*
2.  **Check** your new file: `ls -l datasets/video_training_data.csv`
3.  **Run** the collector again for the next type (e.g., `train http`).
4.  **Send** the corresponding traffic in Mininet.

---

## 🎓 Final Step: Retrain the AI

Once you have collected all the datasets you want:

```bash
# In Terminal 2
python3 retrain_all_models.py
```

Now your AI is trained on YOUR network's data! 🚀
