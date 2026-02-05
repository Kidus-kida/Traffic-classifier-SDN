"""
Tests for Enhanced Classifier
Basic functionality tests for the monolithic classifier script
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the class to test (we need to handle imports carefully since it's a script)
# We'll use a dynamic import or mock approach since the script runs on import
# For this test, we'll verify the Flow class and basic logic if possible

from enhanced_traffic_classifier import EnhancedFlow

class TestEnhancedClassifier:
    """Test functionality defined in enhanced_traffic_classifier.py"""
    
    def test_enhanced_flow_initialization(self):
        """Test EnhancedFlow class initialization"""
        flow = EnhancedFlow(
            time_start=1000,
            datapath='1',
            inport='1',
            ethsrc='00:00:00:00:00:01',
            ethdst='00:00:00:00:00:02',
            outport='2',
            packets=100,
            bytes=5000  # Note: argument name is 'bytes' in this script
        )
        
        assert flow.time_start == 1000
        assert flow.forward_packets == 100
        assert flow.forward_bytes == 5000
        assert flow.forward_status == 'ACTIVE'
        
        # Check enhanced features
        assert flow.qos_class == 'BEST_EFFORT'
        assert flow.priority == 0
        assert flow.confidence == 0.0
    
    def test_enhanced_flow_update_forward(self):
        """Test forward update logic"""
        flow = EnhancedFlow(1000, '1', '1', '00...', '00...', '2', 100, 5000)
        
        # Update
        flow.updateforward(150, 7500, 1010)
        
        assert flow.forward_packets == 150
        assert flow.forward_bytes == 7500
        assert flow.forward_delta_packets == 50
        assert flow.forward_delta_bytes == 2500
        
        # Check rates
        assert flow.forward_avg_pps > 0
        assert flow.forward_inst_pps > 0
    
    def test_enhanced_flow_update_reverse(self):
        """Test reverse update logic"""
        flow = EnhancedFlow(1000, '1', '1', '00...', '00...', '2', 100, 5000)
        
        # Update reverse
        flow.updatereverse(50, 2500, 1010)
        
        assert flow.reverse_packets == 50
        assert flow.reverse_bytes == 2500
        assert flow.reverse_delta_packets == 50
        assert flow.reverse_status == 'ACTIVE'

    def test_flow_history(self):
        """Test flow history tracking"""
        flow = EnhancedFlow(1000, '1', '1', '00...', '00...', '2', 100, 5000)
        
        assert isinstance(flow.classification_history, list)
        assert len(flow.classification_history) == 0
        
        # Simulate classification
        flow.classification_history.append({
            'timestamp': '2023-01-01T00:00:00Z',
            'type': 'http',
            'confidence': 0.95
        })
        
        assert len(flow.classification_history) == 1
        assert flow.classification_history[0]['type'] == 'http'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
