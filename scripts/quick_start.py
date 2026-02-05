#!/usr/bin/env python3
"""
Quick Start Script
Automated setup and launch of the traffic classifier system
"""

import sys
import os
import subprocess
import time
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")


def run_command(cmd, description, check=True):
    """Run command with description"""
    print(f"→ {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  ✅ {description} - SUCCESS")
            return True
        else:
            print(f"  ❌ {description} - FAILED")
            if result.stderr:
                print(f"     Error: {result.stderr[:200]}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"  ❌ {description} - ERROR: {e}")
        return False


def main():
    """Main quick start function"""
    print_header("🚀 TRAFFIC CLASSIFIER - QUICK START")
    
    base_dir = Path(__file__).parent.parent
    os.chdir(base_dir)
    
    # Step 1: Validate system
    print_header("Step 1: System Validation")
    if not run_command(
        f"{sys.executable} scripts/validate_system.py",
        "Validating system requirements"
    ):
        print("\n❌ System validation failed. Please fix errors and try again.")
        return 1
    
    # Step 2: Clean up previous runs
    print_header("Step 2: Cleanup")
    run_command("sudo mn -c", "Cleaning up Mininet", check=False)
    run_command("sudo pkill -f ryu-manager", "Stopping Ryu processes", check=False)
    time.sleep(2)
    
    # Step 3: Create necessary directories
    print_header("Step 3: Directory Setup")
    dirs = ['logs', 'metrics', 'flow_rules']
    for dir_name in dirs:
        dir_path = base_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"  ✅ Created/verified {dir_name}/")
    
    # Step 4: Run tests (optional)
    print_header("Step 4: Running Tests (Optional)")
    response = input("Run tests before starting? (y/N): ").strip().lower()
    if response == 'y':
        if not run_command(
            f"{sys.executable} -m pytest tests/unit/ -v",
            "Running unit tests",
            check=False
        ):
            print("  ⚠️  Some tests failed, but continuing...")
    
    # Step 5: Start the classifier
    print_header("Step 5: Starting Traffic Classifier")
    
    print("\n📋 Available algorithms:")
    print("  1. Randomforest (Recommended - 96.8% accuracy)")
    print("  2. logistic (Fast - 92.3% accuracy)")
    print("  3. kneighbors (Balanced - 94.1% accuracy)")
    print("  4. svc (Good - 93.7% accuracy)")
    print("  5. gaussiannb (Basic - 89.5% accuracy)")
    print("  6. kmeans (Unsupervised - 85.2% accuracy)")
    
    algorithm = input("\nSelect algorithm (1-6) [1]: ").strip() or "1"
    
    algorithm_map = {
        "1": "Randomforest",
        "2": "logistic",
        "3": "kneighbors",
        "4": "svc",
        "5": "gaussiannb",
        "6": "kmeans"
    }
    
    selected_algorithm = algorithm_map.get(algorithm, "Randomforest")
    
    auto_rules = input("Auto-install flow rules? (y/N): ").strip().lower() == 'y'
    
    # Build command
    cmd = f"{sys.executable} src/controller/traffic_classifier.py {selected_algorithm}"
    if auto_rules:
        cmd += " --auto-rules"
    
    print(f"\n🎯 Starting classifier with {selected_algorithm}...")
    print(f"   Command: {cmd}")
    print("\n" + "="*80)
    print("  CLASSIFIER RUNNING")
    print("  Press Ctrl+C to stop")
    print("="*80 + "\n")
    
    try:
        # Run classifier
        subprocess.run(cmd, shell=True)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping classifier...")
    
    # Cleanup
    print_header("Cleanup")
    run_command("sudo mn -c", "Cleaning up Mininet", check=False)
    run_command("sudo pkill -f ryu-manager", "Stopping Ryu", check=False)
    
    print("\n✅ Quick start complete!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
