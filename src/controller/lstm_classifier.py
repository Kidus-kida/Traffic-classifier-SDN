#!/usr/bin/env python3
"""
LSTM Deep Learning Traffic Classifier
Advanced time-series analysis for network traffic classification
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
import joblib
import os
import pickle
from collections import deque

# Check if CUDA is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class TrafficDataset(Dataset):
    """Custom Dataset for traffic data"""
    def __init__(self, sequences, labels):
        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.LongTensor(labels)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]

class TrafficLSTM(nn.Module):
    """LSTM Neural Network for Traffic Classification"""
    def __init__(self, input_size=12, hidden_size=128, num_layers=2, num_classes=10, dropout=0.3):
        super(TrafficLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # Attention mechanism
        self.attention = nn.Linear(hidden_size * 2, 1)
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size * 2, 64)
        self.fc2 = nn.Linear(64, num_classes)
        
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.softmax = nn.Softmax(dim=1)
    
    def attention_net(self, lstm_output):
        """Attention mechanism to focus on important time steps"""
        attention_weights = torch.tanh(self.attention(lstm_output))
        attention_weights = torch.softmax(attention_weights, dim=1)
        weighted_output = torch.sum(attention_weights * lstm_output, dim=1)
        return weighted_output
    
    def forward(self, x):
        # LSTM forward pass
        lstm_out, _ = self.lstm(x)
        
        # Apply attention
        attn_out = self.attention_net(lstm_out)
        
        # Fully connected layers
        out = self.relu(self.fc1(attn_out))
        out = self.dropout(out)
        out = self.fc2(out)
        
        return out

class LSTMTrafficClassifier:
    """Wrapper class for LSTM traffic classification"""
    def __init__(self, sequence_length=10, input_size=12, hidden_size=128, num_layers=2):
        self.sequence_length = sequence_length
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.flow_sequences = {}  # Store sequences for each flow
        
    def create_sequences(self, data, labels):
        """Create sequences for LSTM training"""
        sequences = []
        sequence_labels = []
        
        for i in range(len(data) - self.sequence_length + 1):
            seq = data[i:i + self.sequence_length]
            label = labels[i + self.sequence_length - 1]
            sequences.append(seq)
            sequence_labels.append(label)
        
        return np.array(sequences), np.array(sequence_labels)
    
    def train(self, datasets_dir='datasets', epochs=50, batch_size=32, learning_rate=0.001):
        """Train the LSTM model"""
        print("🧠 Training LSTM Deep Learning Model...")
        print(f"Device: {device}")
        
        # Load all training data
        all_data = []
        all_labels = []
        
        traffic_types = ['dns', 'game', 'ping', 'telnet', 'voice', 'http', 'https', 'ftp', 'ssh', 'video']
        
        for traffic_type in traffic_types:
            file_path = os.path.join(datasets_dir, f'{traffic_type}_training_data.csv')
            if os.path.exists(file_path):
                print(f"Loading {traffic_type} data...")
                df = pd.read_csv(file_path, sep='\t')
                
                # Extract features (first 12 columns)
                features = df.iloc[:, :12].values
                labels = [traffic_type] * len(features)
                
                all_data.append(features)
                all_labels.extend(labels)
        
        if not all_data:
            print("❌ No training data found!")
            return
        
        # Combine all data
        X = np.vstack(all_data)
        y = np.array(all_labels)
        
        print(f"Total samples: {len(X)}")
        print(f"Traffic types: {np.unique(y)}")
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        num_classes = len(self.label_encoder.classes_)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Create sequences
        X_seq, y_seq = self.create_sequences(X_scaled, y_encoded)
        print(f"Sequences created: {len(X_seq)}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_seq, y_seq, test_size=0.2, random_state=42, stratify=y_seq
        )
        
        # Create datasets and dataloaders
        train_dataset = TrafficDataset(X_train, y_train)
        test_dataset = TrafficDataset(X_test, y_test)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
        
        # Initialize model
        self.model = TrafficLSTM(
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            num_classes=num_classes
        ).to(device)
        
        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.5)
        
        # Training loop
        best_accuracy = 0.0
        
        for epoch in range(epochs):
            self.model.train()
            train_loss = 0.0
            
            for sequences, labels in train_loader:
                sequences, labels = sequences.to(device), labels.to(device)
                
                # Forward pass
                outputs = self.model(sequences)
                loss = criterion(outputs, labels)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            # Validation
            self.model.eval()
            correct = 0
            total = 0
            test_loss = 0.0
            
            with torch.no_grad():
                for sequences, labels in test_loader:
                    sequences, labels = sequences.to(device), labels.to(device)
                    outputs = self.model(sequences)
                    loss = criterion(outputs, labels)
                    test_loss += loss.item()
                    
                    _, predicted = torch.max(outputs.data, 1)
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()
            
            accuracy = 100 * correct / total
            avg_train_loss = train_loss / len(train_loader)
            avg_test_loss = test_loss / len(test_loader)
            
            scheduler.step(avg_test_loss)
            
            print(f"Epoch [{epoch+1}/{epochs}] - "
                  f"Train Loss: {avg_train_loss:.4f}, "
                  f"Test Loss: {avg_test_loss:.4f}, "
                  f"Accuracy: {accuracy:.2f}%")
            
            # Save best model
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                self.save_model('models/LSTM_Classifier')
                print(f"✅ Best model saved! Accuracy: {accuracy:.2f}%")
        
        print(f"\n🎉 Training complete! Best accuracy: {best_accuracy:.2f}%")
    
    def predict(self, flow_features, flow_id):
        """Predict traffic type for a flow using sequence"""
        if self.model is None:
            raise ValueError("Model not loaded. Train or load a model first.")
        
        # Initialize sequence for new flow
        if flow_id not in self.flow_sequences:
            self.flow_sequences[flow_id] = deque(maxlen=self.sequence_length)
        
        # Add current features to sequence
        scaled_features = self.scaler.transform([flow_features])[0]
        self.flow_sequences[flow_id].append(scaled_features)
        
        # Need at least sequence_length samples
        if len(self.flow_sequences[flow_id]) < self.sequence_length:
            # Pad with zeros if not enough data
            padded_seq = np.zeros((self.sequence_length, self.input_size))
            current_len = len(self.flow_sequences[flow_id])
            padded_seq[-current_len:] = list(self.flow_sequences[flow_id])
            sequence = padded_seq
        else:
            sequence = np.array(list(self.flow_sequences[flow_id]))
        
        # Predict
        self.model.eval()
        with torch.no_grad():
            sequence_tensor = torch.FloatTensor(sequence).unsqueeze(0).to(device)
            output = self.model(sequence_tensor)
            probabilities = torch.softmax(output, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
            
            traffic_type = self.label_encoder.inverse_transform([predicted.item()])[0]
            return traffic_type, confidence.item()
    
    def save_model(self, path):
        """Save model and preprocessing objects"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'sequence_length': self.sequence_length,
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'num_layers': self.num_layers,
            'num_classes': len(self.label_encoder.classes_)
        }
        
        torch.save(checkpoint, path + '.pth')
        
        # Also save as pickle for compatibility
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        
        print(f"💾 Model saved to {path}")
    
    def load_model(self, path):
        """Load model and preprocessing objects"""
        checkpoint = torch.load(path + '.pth', map_location=device)
        
        self.scaler = checkpoint['scaler']
        self.label_encoder = checkpoint['label_encoder']
        self.sequence_length = checkpoint['sequence_length']
        self.input_size = checkpoint['input_size']
        self.hidden_size = checkpoint['hidden_size']
        self.num_layers = checkpoint['num_layers']
        
        self.model = TrafficLSTM(
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            num_classes=checkpoint['num_classes']
        ).to(device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        print(f"✅ Model loaded from {path}")

def main():
    """Main function for training"""
    print("\n" + "="*80)
    print("🧠 LSTM DEEP LEARNING TRAFFIC CLASSIFIER")
    print("="*80)
    print(f"PyTorch Version: {torch.__version__}")
    print(f"Device: {device}")
    print("="*80 + "\n")
    
    # Create and train classifier
    classifier = LSTMTrafficClassifier(
        sequence_length=10,
        input_size=12,
        hidden_size=128,
        num_layers=2
    )
    
    # Train model
    classifier.train(
        datasets_dir='datasets',
        epochs=50,
        batch_size=32,
        learning_rate=0.001
    )
    
    print("\n✅ LSTM model training complete!")
    print("📝 Model saved to models/LSTM_Classifier")
    print("\n💡 To use in real-time classification:")
    print("   python3 enhanced_traffic_classifier.py lstm --auto-rules")

if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print("\n❌ PyTorch not installed!")
        print("📦 Install with: pip3 install torch torchvision")
        print(f"Error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
