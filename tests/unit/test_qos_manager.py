"""
Unit tests for QoS Manager
"""

import pytest
import shutil
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.controller.qos_manager import QoSManager, FlowRule
from src.controller.flow_manager import Flow


class TestQoSManager:
    """Test QoSManager class"""
    
    @pytest.fixture
    def config(self):
        """Mock configuration"""
        config = Mock()
        
        # Setup QoS config mock
        qos_config = Mock()
        qos_config.classes = {
            'voice': {'class': 'REAL_TIME', 'priority': 5, 'action': 'PRIORITY_FORWARD'},
            'video': {'class': 'REAL_TIME', 'priority': 4, 'action': 'PRIORITY_FORWARD'},
            'http': {'class': 'BEST_EFFORT', 'priority': 2, 'action': 'FORWARD'}
        }
        qos_config.default = {'class': 'BEST_EFFORT', 'priority': 0, 'action': 'FORWARD'}
        config.get_qos_config.return_value = qos_config
        
        # Setup get method
        config.get.side_effect = lambda key, default=None: {
            'classification.confidence_threshold': 0.7,
            'flow_rules.auto_install': True
        }.get(key, default)
        
        return config
    
    @pytest.fixture
    def logger(self):
        """Mock logger"""
        return Mock()
    
    @pytest.fixture
    def temp_rules_file(self):
        """Create temporary rules file"""
        tmp_dir = tempfile.mkdtemp()
        rules_file = Path(tmp_dir) / 'test_rules.json'
        yield rules_file
        shutil.rmtree(tmp_dir)
        
    @pytest.fixture
    def qos_manager(self, config, logger, temp_rules_file):
        """Create QoSManager instance"""
        config.resolve_path.return_value = temp_rules_file
        return QoSManager(config, logger)
    
    def test_initialization(self, qos_manager):
        """Test QoS Manager initialization"""
        assert qos_manager.qos_config is not None
        assert isinstance(qos_manager.installed_rules, dict)
        assert len(qos_manager.installed_rules) == 0
    
    def test_assign_qos_class(self, qos_manager):
        """Test QoS class assignment"""
        # Test defined class
        qos_class, priority = qos_manager.assign_qos_class('voice')
        assert qos_class == 'REAL_TIME'
        assert priority == 5
        
        # Test another defined class
        qos_class, priority = qos_manager.assign_qos_class('http')
        assert qos_class == 'BEST_EFFORT'
        assert priority == 2
        
        # Test unknown/default class
        qos_class, priority = qos_manager.assign_qos_class('unknown_type')
        assert qos_class == 'BEST_EFFORT'
        assert priority == 0
    
    def test_get_flow_action(self, qos_manager):
        """Test flow action retrieval"""
        action = qos_manager.get_flow_action('voice')
        assert action == 'PRIORITY_FORWARD'
        
        action = qos_manager.get_flow_action('http')
        assert action == 'FORWARD'
        
        action = qos_manager.get_flow_action('unknown')
        assert action == 'FORWARD'
    
    def test_should_install_rule(self, qos_manager):
        """Test rule installation decision logic"""
        flow_id = 12345
        
        # Should install (high confidence, auto-install enabled)
        assert qos_manager.should_install_rule(flow_id, 0.95)
        
        # Should NOT install (low confidence)
        assert not qos_manager.should_install_rule(flow_id, 0.5)
        
        # Disable auto-install
        qos_manager.config.get.side_effect = lambda key, default=None: {
            'classification.confidence_threshold': 0.7,
            'flow_rules.auto_install': False
        }.get(key, default)
        
        # Should NOT install (auto-install disabled)
        assert not qos_manager.should_install_rule(flow_id, 0.95)
    
    def test_create_flow_rule(self, qos_manager):
        """Test flow rule creation"""
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01',
                   '00:00:00:00:00:02', '2', 100, 5000)
        
        rule = qos_manager.create_flow_rule(flow, 'voice', 0.95)
        
        assert isinstance(rule, FlowRule)
        assert rule.traffic_type == 'voice'
        assert rule.qos_class == 'REAL_TIME'
        assert rule.priority == 5
        assert rule.action == 'PRIORITY_FORWARD'
        assert rule.src_mac == '00:00:00:00:00:01'
        assert rule.dst_mac == '00:00:00:00:00:02'
    
    def test_install_flow_rule(self, qos_manager):
        """Test flow rule installation and persistence"""
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01',
                   '00:00:00:00:00:02', '2', 100, 5000)
        
        rule = qos_manager.create_flow_rule(flow, 'voice', 0.95)
        
        success = qos_manager.install_flow_rule(rule)
        
        assert success
        assert rule.flow_id in qos_manager.installed_rules
        
        # Verify file persistence
        assert os.path.exists(qos_manager.flow_rules_file)
        with open(qos_manager.flow_rules_file, 'r') as f:
            saved_rules = json.load(f)
            assert len(saved_rules) == 1
            assert saved_rules[0]['traffic_type'] == 'voice'
    
    def test_load_existing_rules(self, config, logger, temp_rules_file):
        """Test loading existing rules from file"""
        # Create a dummy rule file
        existing_rule = {
            "timestamp": "2023-01-01T00:00:00Z",
            "flow_id": 12345,
            "src_mac": "00:00:00:00:00:01",
            "dst_mac": "00:00:00:00:00:02",
            "traffic_type": "voice",
            "qos_class": "REAL_TIME",
            "priority": 5,
            "action": "PRIORITY_FORWARD",
            "datapath": "1",
            "in_port": "1",
            "out_port": "2"
        }
        
        with open(temp_rules_file, 'w') as f:
            json.dump([existing_rule], f)
        
        # Initialize manager
        config.resolve_path.return_value = temp_rules_file
        manager = QoSManager(config, logger)
        
        assert len(manager.installed_rules) == 1
        assert 12345 in manager.installed_rules
        assert manager.installed_rules[12345].traffic_type == 'voice'
    
    def test_clear_old_rules(self, qos_manager):
        """Test clearing old rules"""
        # Add old rule
        old_rule = FlowRule(
            timestamp="2020-01-01T00:00:00Z", # Very old
            flow_id=1,
            src_mac="00...", dst_mac="00...", traffic_type="voice",
            qos_class="REAL_TIME", priority=5, action="FORWARD",
            datapath="1", in_port="1", out_port="2"
        )
        qos_manager.installed_rules[1] = old_rule
        
        # Add new rule
        from datetime import datetime
        new_rule = FlowRule(
            timestamp=datetime.utcnow().isoformat() + "Z", # Now
            flow_id=2,
            src_mac="00...", dst_mac="00...", traffic_type="voice",
            qos_class="REAL_TIME", priority=5, action="FORWARD",
            datapath="1", in_port="1", out_port="2"
        )
        qos_manager.installed_rules[2] = new_rule
        
        # Clear rules older than 1 hour
        qos_manager.clear_old_rules(max_age_seconds=3600)
        
        assert 1 not in qos_manager.installed_rules
        assert 2 in qos_manager.installed_rules
    
    def test_get_statistics(self, qos_manager):
        """Test statistics generation"""
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01', '00:00:00:00:00:02', '2', 100, 5000)
        
        # Add voice rule
        rule1 = qos_manager.create_flow_rule(flow, 'voice', 0.95)
        qos_manager.install_flow_rule(rule1)
        
        # Add http rule
        flow.ethsrc = '00:00:00:00:00:03' # Different flow
        rule2 = qos_manager.create_flow_rule(flow, 'http', 0.95)
        qos_manager.install_flow_rule(rule2)
        
        stats = qos_manager.get_statistics()
        
        assert stats['total_rules'] == 2
        assert stats['by_traffic_type']['voice'] == 1
        assert stats['by_traffic_type']['http'] == 1
        assert stats['by_qos_class']['REAL_TIME'] == 1
        assert stats['by_qos_class']['BEST_EFFORT'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
