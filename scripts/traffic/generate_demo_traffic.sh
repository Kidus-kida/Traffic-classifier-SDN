#!/bin/bash
# Generate various traffic types for the SDN dashboard demo in a single session

echo "🚀 Starting Mininet and generating diverse traffic..."
cd /mnt/d/Projects/Traffic-classifier-SDN

# One-liner to run multiple traffic types in parallel then wait
# This allows the dashboard to capture all of them at once.
sudo mn --topo single,3 --mac --switch ovsk --controller remote,ip=127.0.0.1,port=6633 --test "
h2 ITGRec & 
sleep 2;
h1 ITGSend D-IGT_scripts/http_script_file -a h2 & 
h1 ITGSend D-IGT_scripts/dns_script_file -a h2 & 
h1 ITGSend D-IGT_scripts/ssh_script_file -a h2 & 
h1 ITGSend D-IGT_scripts/voice_script_file -a h2 & 
h1 ITGSend D-IGT_scripts/video_script_file -a h2 & 
sleep 60;
pkill ITGRec
"

echo "✅ Traffic generation complete!"
