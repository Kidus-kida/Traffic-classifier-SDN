"""
Integration tests for QoS Management
"""

import pytest
from unittest.mock import Mock

from src.controller.flow_manager import Flow
from src.controller.qos_manager import QoSManager, FlowRule


class TestQoSIntegration:
    """Test QoS management integration"""
    
    @pytest.fixture
    def config(self):
        """Mock configuration"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'classification.confidence_threshold': 0.7,
            'flow_rules.auto_install': True,
            'qos.classes.voice.qos_class': 'REAL_TIME',
            'qos.classes.voice.priority': 5,
            'qos.classes.http.qos_class': 'BEST_EFFORT',
            'qos.classes.http.priority': 2,
        }.get(key, default))
        
        # Configure resolve_path to return a valid temp path
        import tempfile
        import os
        tmp_dir = tempfile.mkdtemp()
        config.resolve_path = Mock(return_value=os.path.join(tmp_dir, 'flow_rules/installed_rules.json'))
        config.get_qos_config = Mock(return_value=Mock(
            classes={
                'voice': {'class': 'REAL_TIME', 'priority': 5, 'action': 'PRIORITY_FORWARD'},
                'http': {'class': 'BEST_EFFORT', 'priority': 2, 'action': 'FORWARD'}
            },
            default={'class': 'BEST_EFFORT', 'priority': 0, 'action': 'FORWARD'}
        ))
        
        return config
    
    @pytest.fixture
    def logger(self):
        """Mock logger"""
        return Mock()
    
    @pytest.fixture
    def qos_manager(self, config, logger):
        """Create QoSManager instance"""
        return QoSManager(config, logger)
    
    def test_assign_qos_voice(self, qos_manager):
        """Test QoS assignment for voice traffic"""
        qos_class, priority = qos_manager.assign_qos_class('voice')
        
        assert qos_class == 'REAL_TIME'
        assert priority == 5
    
    def test_assign_qos_http(self, qos_manager):
        """Test QoS assignment for HTTP traffic"""
        qos_class, priority = qos_manager.assign_qos_class('http')
        
        assert qos_class == 'BEST_EFFORT'
        assert priority == 2
    
    def test_create_flow_rule(self, qos_manager):
        """Test flow rule creation"""
        flow = Flow(
            time_start=1000,
            datapath='1',
            inport='1',
            ethsrc='00:00:00:00:00:01',
            ethdst='00:00:00:00:00:02',
            outport='2',
            packets=100,
            bytes_count=5000
        )
        
        rule = qos_manager.create_flow_rule(flow, 'voice', 0.95)
        
        assert isinstance(rule, FlowRule)
        assert rule.traffic_type == 'voice'
        assert rule.qos_class == 'REAL_TIME'
        assert rule.priority == 5
        assert rule.src_mac == '00:00:00:00:00:01'
        assert rule.dst_mac == '00:00:00:00:00:02'
    
    def test_should_install_rule_high_confidence(self, qos_manager):
        """Test rule installation decision with high confidence"""
        flow_id = 12345
        confidence = 0.95
        
        should_install = qos_manager.should_install_rule(flow_id, confidence)
        
        # Should install (auto_install is True)
        assert should_install is True
    
    def test_should_install_rule_low_confidence(self, qos_manager):
        """Test rule installation decision with low confidence"""
        flow_id = 12345
        confidence = 0.5
        
        should_install = qos_manager.should_install_rule(flow_id, confidence)
        
        assert should_install is False
    
    def test_should_install_rule_already_installed(self, qos_manager):
        """Test rule installation when already installed"""
        flow_id = 12345
        
        # Create and "install" a rule
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01',
                   '00:00:00:00:00:02', '2', 100, 5000)
        rule = qos_manager.create_flow_rule(flow, 'voice', 0.95)
        qos_manager.installed_rules[flow_id] = rule
        
        should_install = qos_manager.should_install_rule(flow_id, 0.95)
        
        assert should_install is False
    
    def test_get_statistics(self, qos_manager):
        """Test statistics retrieval"""
        # Add some rules
        for i in range(3):
            flow = Flow(1000, '1', '1', f'00:00:00:00:00:0{i}',
                       '00:00:00:00:00:FF', '2', 100, 5000)
            rule = qos_manager.create_flow_rule(flow, 'http', 0.95)
            qos_manager.installed_rules[i] = rule
        
        stats = qos_manager.get_statistics()
        
        assert stats['total_rules'] == 3
        assert 'by_traffic_type' in stats
        assert 'by_qos_class' in stats


class TestQoSPolicyEnforcement:
    """Test QoS policy enforcement scenarios"""
    
    @pytest.fixture
    def qos_manager(self):
        """Create QoSManager with auto-install enabled"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'classification.confidence_threshold': 0.7,
            'flow_rules.auto_install': True,
            'qos.classes.voice.qos_class': 'REAL_TIME',
            'qos.classes.voice.priority': 5,
            'qos.classes.video.qos_class': 'REAL_TIME',
            'qos.classes.video.priority': 4,
            'qos.classes.http.qos_class': 'BEST_EFFORT',
            'qos.classes.http.priority': 2,
        }.get(key, default))
        
        # Mock resolve_path and get_qos_config
        import tempfile
        import os
        tmp_dir = tempfile.mkdtemp()
        config.resolve_path = Mock(return_value=os.path.join(tmp_dir, 'flow_rules/installed_rules.json'))
        config.get_qos_config = Mock(return_value=Mock(
            classes={
                'voice': {'class': 'REAL_TIME', 'priority': 5},
                'video': {'class': 'REAL_TIME', 'priority': 4},
                'http': {'class': 'BEST_EFFORT', 'priority': 2}
            },
            default={'class': 'BEST_EFFORT', 'priority': 0}
        ))
        
        return QoSManager(config, Mock())
    
    def test_voice_gets_highest_priority(self, qos_manager):
        """Test voice traffic gets highest priority"""
        voice_class, voice_priority = qos_manager.assign_qos_class('voice')
        video_class, video_priority = qos_manager.assign_qos_class('video')
        http_class, http_priority = qos_manager.assign_qos_class('http')
        
        assert voice_priority > video_priority
        assert voice_priority > http_priority
        assert voice_class == 'REAL_TIME'
    
    def test_real_time_traffic_prioritized(self, qos_manager):
        """Test real-time traffic prioritized over best-effort"""
        voice_class, voice_priority = qos_manager.assign_qos_class('voice')
        http_class, http_priority = qos_manager.assign_qos_class('http')
        
        assert voice_class == 'REAL_TIME'
        assert http_class == 'BEST_EFFORT'
        assert voice_priority > http_priority


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
