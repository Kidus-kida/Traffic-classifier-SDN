#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
import warnings
import os
warnings.filterwarnings('ignore')

def train_custom_model():
    print("📊 Training Custom Traffic Classifier Model")
    print("="*50)
    
    # Determine project root
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
    DATASETS_DIR = os.path.join(PROJECT_ROOT, 'data')
    
    # Get user input
    model_name = input("Enter model name (e.g., 'office_traffic'): ").strip()
    # Check current directory and datasets folder
    csv_file = f"{model_name}_training_data.csv"
    if not os.path.exists(csv_file):
        csv_file = os.path.join(DATASETS_DIR, f"{model_name}_training_data.csv")
    
    try:
        # Load training data
        print(f"📁 Loading training data from {csv_file}...")
        data = pd.read_csv(csv_file, sep='\t') # Use tab separator as per collection script
        
        # Assume last column is label
        X = data.iloc[:, :-1]  # Features
        y = data.iloc[:, -1]   # Labels
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        print("🤖 Training Random Forest Classifier...")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Model trained successfully!")
        print(f"📈 Accuracy: {accuracy:.2%}")
        print("\n📋 Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Save model
        os.makedirs(MODELS_DIR, exist_ok=True)
        model_file = os.path.join(MODELS_DIR, f"{model_name}.sav")
        joblib.dump(model, model_file)
        print(f"💾 Model saved to: {model_file}")
        
    except FileNotFoundError:
        print(f"❌ Error: {csv_file} not found!")
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")

if __name__ == "__main__":
    train_custom_model()
