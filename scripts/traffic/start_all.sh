
#!/bin/bash

echo "🧹 Cleaning up old processes..."
sudo mn -c
sudo fuser -k 6633/tcp 2>/dev/null
sudo fuser -k 9000/tcp 2>/dev/null
sudo pkill -9 -f enhanced
sudo pkill -9 -f ryu-manager

echo "🚀 Starting Traffic Classifier (Ryu) in background..."
python3 -u src/controller/enhanced_traffic_classifier.py Randomforest --auto-rules > logs/classifier.log 2>&1 &

echo "⏳ Waiting for Ryu to listen on port 6633..."
MAX_RETRIES=30
COUNT=0
while ! netstat -tuln | grep -q ":6633 "; do
    sleep 1
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Timeout waiting for Ryu to start!"
        exit 1
    fi
done
echo "✅ Ryu is ready on 6633."

echo "🌐 Starting Dashboard on port 9000..."
python3 -u src/dashboard/app.py > logs/dashboard.log 2>&1 &
sleep 5

echo "🎮 Starting Mininet topology..."
# We'll run Mininet with a script to automate traffic
cat <<EOF > /tmp/mn_cmds
pingall
h2 ITGRecv &
sleep 1
h1 ITGSend D-IGT_scripts/video_script_file &
h3 ITGSend D-IGT_scripts/voice_script_file &
h1 ping -i 0.2 h3 &
EOF

sudo mn --topo single,3 --mac --switch ovsk --controller remote,ip=127.0.0.1,port=6633 < /tmp/mn_cmds > mininet.log 2>&1 &

echo "✨ All systems started!"
echo "📊 Dashboard: http://localhost:9000"
echo "📡 Check classifier.log and dashboard/dashboard.log for details."
echo "Press Ctrl+C to see logs or just wait..."
