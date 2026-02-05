#!/usr/bin/env python3
"""
AI-Powered Traffic Classifier for SDN
Refactored production-ready implementation with fault tolerance
"""

import sys
import signal
import subprocess
import time
import argparse
from pathlib import Path
from typing import Optional
from prettytable import PrettyTable

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import get_config
from src.utils.logger import get_logger, setup_logging
from src.utils.health import get_health_monitor
from src.ml.feature_extractor import FeatureExtractor
from src.ml.model_manager import ModelManager
from src.controller.flow_manager import FlowManager
from src.controller.qos_manager import QoSManager


class TrafficClassifier:
    """
    Main traffic classifier application.
    
    Integrates all components for real-time traffic classification with QoS.
    """
    
    def __init__(self, algorithm: str = 'Randomforest', auto_install_rules: bool = False):
        """
        Initialize traffic classifier.
        
        Args:
            algorithm: ML algorithm to use
            auto_install_rules: Whether to automatically install flow rules
        """
        # Load configuration
        self.config = get_config()
        
        # Setup logging
        logging_config = self.config.get('logging', {})
        self.logger = setup_logging(logging_config)
        
        self.logger.info("="*80)
        self.logger.info("🚀 AI-POWERED TRAFFIC CLASSIFIER FOR SDN")
        self.logger.info("="*80)
        
        # Initialize components
        self.algorithm = algorithm
        self.auto_install_rules = auto_install_rules
        
        self.flow_manager = FlowManager(self.logger)
        self.model_manager = ModelManager(self.config, self.logger)
        self.qos_manager = QoSManager(self.config, self.logger)
        self.health_monitor = get_health_monitor()
        
        # Ryu controller process
        self.ryu_process: Optional[subprocess.Popen] = None
        
        # Statistics
        self.classification_count = 0
        self.classification_stats = {}
        
        # Load ML model
        self._load_model()
    
    def _load_model(self):
        """Load ML model"""
        self.logger.info(f"Loading model: {self.algorithm}")
        
        success = self.model_manager.load_model(self.algorithm)
        
        if success:
            self.health_monitor.set_component_status('model', True)
            self.logger.info(f"✅ Model loaded successfully: {self.algorithm}")
        else:
            self.health_monitor.set_component_status('model', False)
            self.health_monitor.add_error(f"Failed to load model: {self.algorithm}")
            self.logger.error(f"❌ Failed to load model: {self.algorithm}")
            self.logger.warning("⚠️  System will use fallback classification")
    
    def start_ryu_controller(self):
        """Start Ryu SDN controller"""
        self.logger.info("Starting Ryu SDN controller...")
        
        controller_config = self.config.get_controller_config()
        
        # Build Ryu command
        cmd = [
            controller_config.ryu_executable,
            '--ofp-tcp-listen-port', str(controller_config.listen_port),
            '--log-file', str(self.config.resolve_path('logs/ryu.log')),
            controller_config.monitor_script
        ]
        
        try:
            self.ryu_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=False
            )
            
            self.health_monitor.set_component_status('controller', True)
            self.logger.info(f"✅ Ryu controller started on port {controller_config.listen_port}")
            
            return True
            
        except Exception as e:
            self.health_monitor.set_component_status('controller', False)
            self.health_monitor.add_error(f"Failed to start Ryu: {e}")
            self.logger.error(f"❌ Failed to start Ryu controller: {e}")
            return False
    
    def process_flow_data(self, line: str) -> bool:
        """
        Process flow data line from Ryu controller.
        
        Args:
            line: Flow data line
            
        Returns:
            True if flow was processed
        """
        if 'data\t' not in line:
            return False
        
        try:
            # Parse flow data
            fields = line.split('data\t')[1].strip().split('\t')
            
            if len(fields) < 8:
                return False
            
            # Process flow statistics
            flow = self.flow_manager.process_flow_stats(fields)
            
            if flow is None:
                return False
            
            # Only classify active flows
            if not flow.is_active():
                return False
            
            # Extract features
            features = FeatureExtractor.extract_safe(flow)
            
            if features is None:
                self.logger.warning("Invalid features extracted", flow_id=flow.get_flow_id())
                return False
            
            # Classify traffic
            start_time = time.time()
            prediction = self.model_manager.predict(features.to_array())
            duration_ms = (time.time() - start_time) * 1000
            
            # Update flow with prediction
            flow.predicted_type = prediction.traffic_type
            flow.confidence = prediction.confidence
            
            # Assign QoS
            qos_config = self.config.get('qos', {})
            flow.assign_qos(prediction.traffic_type, qos_config)
            
            # Update statistics
            self.classification_count += 1
            self.classification_stats[prediction.traffic_type] = \
                self.classification_stats.get(prediction.traffic_type, 0) + 1
            
            # Log classification
            self.logger.log_flow_classification(
                flow.get_flow_id(),
                prediction.traffic_type,
                prediction.confidence,
                duration_ms
            )
            
            # Install flow rule if enabled
            if self.auto_install_rules and not prediction.fallback_used:
                rule = self.qos_manager.create_flow_rule(flow, prediction.traffic_type, prediction.confidence)
                
                if rule:
                    self.qos_manager.install_flow_rule(rule)
                    flow.flow_rule_installed = True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing flow data: {e}")
            return False
    
    def display_classification_table(self):
        """Display classification results in table format"""
        table = PrettyTable()
        table.field_names = [
            "Flow ID", "Src MAC", "Dst MAC", "Traffic Type", 
            "Confidence", "QoS Class", "Priority", "Rule Installed"
        ]
        
        active_flows = self.flow_manager.get_active_flows()
        
        for flow_id, flow in active_flows.items():
            if flow.predicted_type:
                table.add_row([
                    str(flow_id)[:8],
                    flow.ethsrc[:17],
                    flow.ethdst[:17],
                    flow.predicted_type,
                    f"{flow.confidence:.2%}",
                    flow.qos_class,
                    flow.priority,
                    "✅" if flow.flow_rule_installed else "❌"
                ])
        
        print("\n" + "="*100)
        print(table)
        print(f"\n📊 Classification Statistics: {self.classification_stats}")
        print(f"📈 Total Classifications: {self.classification_count}")
        print(f"🔄 Active Flows: {len(active_flows)}")
        print(f"📋 Installed Rules: {self.qos_manager.get_rule_count()}")
        print("="*100 + "\n")
    
    def run(self):
        """Main run loop"""
        # Start Ryu controller
        if not self.start_ryu_controller():
            self.logger.critical("Failed to start Ryu controller. Exiting.")
            return 1
        
        self.logger.info("🎯 Traffic classifier running...")
        self.logger.info(f"📊 Algorithm: {self.algorithm}")
        self.logger.info(f"⚙️  Auto-install rules: {self.auto_install_rules}")
        self.logger.info("⏳ Waiting for flow data...\n")
        
        # Classification interval
        classification_interval = self.config.get('classification.classification_interval', 10)
        last_display_time = time.time()
        
        try:
            while True:
                # Read from Ryu controller
                line = self.ryu_process.stdout.readline()
                
                if not line and self.ryu_process.poll() is not None:
                    self.logger.error("⚠️  Ryu controller process terminated")
                    self.health_monitor.set_component_status('controller', False)
                    break
                
                if line:
                    decoded_line = line.decode('utf-8', errors='ignore').strip()
                    
                    # Process flow data
                    self.process_flow_data(decoded_line)
                
                # Display classification table periodically
                current_time = time.time()
                if current_time - last_display_time >= classification_interval:
                    self.display_classification_table()
                    last_display_time = current_time
                    
                    # Clean up old flows
                    self.flow_manager.clear_inactive_flows()
                    
                    # Clean up old rules
                    self.qos_manager.clear_old_rules()
        
        except KeyboardInterrupt:
            self.logger.info("\n⏹️  Received shutdown signal")
        
        except Exception as e:
            self.logger.exception(f"Unexpected error: {e}")
            return 1
        
        finally:
            self.cleanup()
        
        return 0
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("🧹 Cleaning up...")
        
        # Stop Ryu controller
        if self.ryu_process:
            self.logger.info("Stopping Ryu controller...")
            self.ryu_process.terminate()
            try:
                self.ryu_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ryu_process.kill()
        
        # Display final statistics
        self.logger.info("\n" + "="*80)
        self.logger.info("📊 FINAL STATISTICS")
        self.logger.info("="*80)
        self.logger.info(f"Total Classifications: {self.classification_count}")
        self.logger.info(f"Classification Breakdown: {self.classification_stats}")
        self.logger.info(f"Total Flows: {self.flow_manager.get_flow_count()}")
        self.logger.info(f"Installed Rules: {self.qos_manager.get_rule_count()}")
        
        qos_stats = self.qos_manager.get_statistics()
        self.logger.info(f"QoS Statistics: {qos_stats}")
        
        self.logger.info("="*80)
        self.logger.info("✅ Shutdown complete")


def print_help():
    """Print help message"""
    print("\n" + "="*80)
    print("🚀 AI-POWERED TRAFFIC CLASSIFIER FOR SDN")
    print("="*80)
    print("\n📖 Usage: python3 traffic_classifier.py [algorithm] [options]")
    
    print("\n🤖 Available Algorithms:")
    print("   • Randomforest     - Random Forest (Best accuracy)")
    print("   • logistic         - Logistic Regression (Fastest)")
    print("   • kneighbors       - K-Nearest Neighbors")
    print("   • svc              - Support Vector Machine")
    print("   • gaussiannb       - Gaussian Naive Bayes")
    print("   • kmeans           - K-Means Clustering (Unsupervised)")
    
    print("\n⚙️  Options:")
    print("   --auto-rules       - Automatically install flow rules")
    print("   --help, -h         - Show this help message")
    
    print("\n📝 Examples:")
    print("   python3 traffic_classifier.py Randomforest")
    print("   python3 traffic_classifier.py logistic --auto-rules")
    
    print("\n" + "="*80 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='AI-Powered Traffic Classifier for SDN',
        add_help=False
    )
    
    parser.add_argument(
        'algorithm',
        nargs='?',
        default='Randomforest',
        help='ML algorithm to use'
    )
    
    parser.add_argument(
        '--auto-rules',
        action='store_true',
        help='Automatically install flow rules'
    )
    
    parser.add_argument(
        '--help', '-h',
        action='store_true',
        help='Show help message'
    )
    
    args = parser.parse_args()
    
    if args.help:
        print_help()
        return 0
    
    # Create and run classifier
    classifier = TrafficClassifier(
        algorithm=args.algorithm,
        auto_install_rules=args.auto_rules
    )
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\n⏹️  Received interrupt signal")
        classifier.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run classifier
    return classifier.run()


if __name__ == '__main__':
    sys.exit(main())
