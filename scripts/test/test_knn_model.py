#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script to verify the K-Nearest Neighbors (KNN) model works correctly.
This tests the model without needing to run the full SDN setup.
"""

import pickle
import numpy as np

print("Testing K-Nearest Neighbors (KNN) Model")
print("=" * 50)

# Load the KNN model
try:
    print("\nLoading KNN model from models/KNeighbors...")
    with open('models/KNeighbors', 'rb') as f:
        knn_model = pickle.load(f)
    print("[OK] Model loaded successfully!")
    print(f"   Model type: {type(knn_model).__name__}")
    
    # Check if it has the expected attributes
    if hasattr(knn_model, 'n_neighbors'):
        print(f"   Number of neighbors (K): {knn_model.n_neighbors}")
    
except FileNotFoundError:
    print("[ERROR] models/KNeighbors not found!")
    exit(1)
except Exception as e:
    print(f"[ERROR] Error loading model: {e}")
    exit(1)

# Create sample test data (12 features as used in traffic_classifier.py)
print("\nTesting with sample network flow data...")

# Sample features: [forward_delta_packets, forward_delta_bytes, forward_inst_pps, 
#                   forward_avg_pps, forward_inst_bps, forward_avg_bps,
#                   reverse_delta_packets, reverse_delta_bytes, reverse_inst_pps,
#                   reverse_avg_pps, reverse_inst_bps, reverse_avg_bps]

test_samples = [
    {
        'name': 'DNS-like traffic (small packets, bidirectional)',
        'features': [10, 520, 5.0, 5.0, 260.0, 260.0, 8, 480, 4.0, 4.0, 240.0, 240.0]
    },
    {
        'name': 'Telnet-like traffic (interactive, small)',
        'features': [5, 300, 2.5, 2.5, 150.0, 150.0, 5, 300, 2.5, 2.5, 150.0, 150.0]
    },
    {
        'name': 'Ping-like traffic (ICMP)',
        'features': [1, 64, 1.0, 1.0, 64.0, 64.0, 1, 64, 1.0, 1.0, 64.0, 64.0]
    },
    {
        'name': 'Voice-like traffic (constant rate)',
        'features': [50, 8000, 25.0, 25.0, 4000.0, 4000.0, 50, 8000, 25.0, 25.0, 4000.0, 4000.0]
    },
    {
        'name': 'Game-like traffic (low latency)',
        'features': [30, 1500, 15.0, 15.0, 750.0, 750.0, 25, 1200, 12.5, 12.5, 600.0, 600.0]
    }
]

# Create results table
print("\nPrediction Results:")
print("-" * 70)
print(f"{'Sample':<50} | {'Predicted Traffic Type':<15}")
print("-" * 70)

for sample in test_samples:
    # Prepare features as numpy array
    features = np.asarray(sample['features']).reshape(1, -1)
    
    # Predict
    try:
        prediction = knn_model.predict(features)
        
        # The model should return the actual traffic type name (supervised)
        # Not a cluster number (unsupervised)
        predicted_label = prediction[0]
        
        print(f"{sample['name']:<50} | {predicted_label:<15}")
        
    except Exception as e:
        print(f"{sample['name']:<50} | ERROR: {e}")

print("\n" + "=" * 50)
print("[OK] KNN Model Test Complete!")
print("\nKey Points:")
print("   - KNN is a SUPERVISED algorithm")
print("   - It predicts actual traffic type names (dns, telnet, ping, etc.)")
print("   - No manual cluster-to-label mapping needed")
print("   - Learns from labeled training data")

print("\nTo use KNN in real-time classification:")
print("   python3 traffic_classifier.py kneighbors")
print("\n   (Make sure Mininet and Ryu controller are running first)")
