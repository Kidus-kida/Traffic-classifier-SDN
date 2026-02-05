"""
Unit tests for Health Monitor
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.utils.health import HealthMonitor, HealthStatus


class TestHealthMonitor:
    """Test HealthMonitor class"""
    
    @pytest.fixture
    def health_monitor(self):
        """Create HealthMonitor instance"""
        return HealthMonitor()
    
    def test_initialization(self, health_monitor):
        """Test HealthMonitor initialization"""
        assert health_monitor.start_time is not None
        assert isinstance(health_monitor.components, dict)
        assert isinstance(health_monitor.errors, list)
        assert len(health_monitor.errors) == 0
    
    def test_set_component_status(self, health_monitor):
        """Test setting component status"""
        health_monitor.set_component_status('controller', True)
        assert health_monitor.components['controller'] is True
        
        health_monitor.set_component_status('controller', False)
        assert health_monitor.components['controller'] is False
    
    def test_add_error(self, health_monitor):
        """Test adding errors"""
        health_monitor.add_error("Test error 1")
        assert len(health_monitor.errors) == 1
        assert health_monitor.errors[0]['error'] == "Test error 1"
        
        health_monitor.add_error("Test error 2")
        assert len(health_monitor.errors) == 2
    
    def test_error_limit(self, health_monitor):
        """Test error list is limited to 100"""
        # Add 150 errors
        for i in range(150):
            health_monitor.add_error(f"Error {i}")
        
        # Should only keep last 100
        assert len(health_monitor.errors) == 100
        assert health_monitor.errors[-1]['error'] == "Error 149"
    
    def test_check_health_all_healthy(self, health_monitor):
        """Test status when all components healthy"""
        health_monitor.set_component_status('controller', True)
        health_monitor.set_component_status('model', True)
        health_monitor.set_component_status('dashboard', True)
        
        status = health_monitor.check_health()
        
        assert isinstance(status, HealthStatus)
        assert status.status == 'healthy'
        assert all(status.components.values())
    
    def test_check_health_degraded(self, health_monitor):
        """Test status when some components unhealthy"""
        health_monitor.set_component_status('controller', True)
        health_monitor.set_component_status('model', False)
        health_monitor.set_component_status('dashboard', True)
        
        status = health_monitor.check_health()
        
        assert status.status == 'degraded'
        assert status.components['controller'] is True
        assert status.components['model'] is False
    
    def test_check_health_unhealthy(self, health_monitor):
        """Test status when all components unhealthy"""
        health_monitor.set_component_status('controller', False)
        health_monitor.set_component_status('model', False)
        health_monitor.set_component_status('dashboard', False)
        
        status = health_monitor.check_health()
        
        assert status.status == 'unhealthy'
        assert not any(status.components.values())
    
    def test_uptime_calculation(self, health_monitor):
        """Test uptime calculation"""
        time.sleep(0.1)  # Wait a bit
        
        status = health_monitor.check_health()
        
        assert status.uptime_seconds > 0
        assert status.uptime_seconds < 1  # Should be less than 1 second
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_system_metrics(self, mock_disk, mock_memory, mock_cpu, health_monitor):
        """Test system metrics collection"""
        # Mock system metrics
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, used=1024*1024*1024)
        mock_disk.return_value = Mock(percent=70.0)
        
        status = health_monitor.check_health()
        
        assert 'cpu_percent' in status.metrics
        assert 'memory_percent' in status.metrics
        assert status.metrics['cpu_percent'] == 50.0
        assert status.metrics['memory_percent'] == 60.0
    
    def test_recent_errors_in_status(self, health_monitor):
        """Test recent errors included in status"""
        # Add some errors
        for i in range(15):
            health_monitor.add_error(f"Error {i}")
        
        status = health_monitor.check_health()
        
        # Should only include last 10
        assert len(status.errors) == 10
        assert status.errors[-1]['error'] == "Error 14"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
