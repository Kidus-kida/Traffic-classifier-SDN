#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.cluster import KMeans
from sklearn.naive_bayes import GaussianNB
import pickle
import os
import glob

def retrain_models():
    print("🔄 Re-training all models using all available datasets...")
    
    # Create models directory if it doesn't exist
    if not os.path.exists('models'):
        os.makedirs('models')

    # dynamically find all dataset files
    dataset_files = glob.glob('datasets/*_training_data.csv')
    
    if not dataset_files:
        print("❌ Error: No training data found in datasets folder!")
        return

    print(f"Found {len(dataset_files)} datasets: {[os.path.basename(f) for f in dataset_files]}")

    all_data = []
    for file in dataset_files:
            # Read CSV
            try:
                if os.path.getsize(file) < 100:  # Check if file is too small (empty or just headers)
                    print(f"⚠️ Warning: Skipping {file} (File too small/empty)")
                    continue
                    
                df = pd.read_csv(file, sep='\t')
                
                # Verify columns match expected count (approx 17 columns)
                if len(df.columns) < 10:
                    print(f"⚠️ Warning: Skipping {file} (Structure invalid)")
                    continue

                # Drop rows where target is NaN
                df.dropna(subset=[df.columns[-1]], inplace=True)
                    
                all_data.append(df)
            except pd.errors.EmptyDataError:
                print(f"⚠️ Warning: Skipping {file} (Empty)")
            except Exception as e:
                print(f"⚠️ Warning: Could not read {file}: {e}")

    if not all_data:
        print("❌ Error: Could not load any data!")
        return

    df = pd.concat(all_data, ignore_index=True)
    
    # Check if we have enough data
    if len(df) < 10:
        print("❌ Error: Not enough data samples to train models.")
        return

    # Separate features and target
    # The last column is 'Traffic Type'
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values

    print(f"📊 Total samples: {len(df)}")
    print(f"🏷️  Classes: {np.unique(y)}")

    # Model Dictionary
    models_to_train = {
        'models/LogisticRegression': LogisticRegression(max_iter=5000),
        'models/RandomForestClassifier': RandomForestClassifier(n_estimators=100),
        'models/KNeighbors': KNeighborsClassifier(n_neighbors=5),
        'models/SVC': SVC(probability=True), # Enable probability for confidence scores
        'models/GaussianNB': GaussianNB(),
        'models/KMeans_Clustering': KMeans(n_clusters=len(np.unique(y)), n_init='auto')
    }

    for path, model in models_to_train.items():
        print(f"🛠️ Training {os.path.basename(path)}...")
        try:
            if 'KMeans' in path:
                model.fit(X) # Unsupervised
            else:
                model.fit(X, y) # Supervised
                
            with open(path, 'wb') as f:
                pickle.dump(model, f)
            print(f"✅ Saved {path}")
        except Exception as e:
            print(f"❌ Failed to train {path}: {e}")

    print("\n🎉 All models retrained and saved successfully!")

if __name__ == "__main__":
    retrain_models()
