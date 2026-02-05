"""
Unit tests for Logger
"""

import pytest
import logging
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock

from src.utils.logger import (
    JSONFormatter,
    StructuredLogger,
    get_logger
)


class TestJSONFormatter:
    """Test JSONFormatter class"""
    
    def test_format_basic(self):
        """Test basic log formatting"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data['level'] == 'INFO'
        assert log_data['message'] == 'Test message'
        assert log_data['timestamp'].endswith('Z')
    
    def test_format_with_extra_fields(self):
        """Test formatting with custom fields"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        # Add custom fields directly to record
        record.flow_id = '123'
        record.traffic_type = 'http'
        record.confidence = 0.95
        record.duration_ms = 45.2
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data['flow_id'] == '123'
        assert log_data['traffic_type'] == 'http'
        assert log_data['confidence'] == 0.95
        assert log_data['duration_ms'] == 45.2


class TestStructuredLogger:
    """Test StructuredLogger class"""
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        config = {
            'level': 'INFO',
            'console': {
                'enabled': True
            },
            'file': {
                'enabled': False
            }
        }
        
        logger = StructuredLogger('test', config)
        
        assert logger is not None
        assert logger.logger.level == logging.INFO
    
    def test_logger_with_file(self):
        """Test logger with file handler"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'level': 'DEBUG',
                'console': {
                    'enabled': False
                },
                'file': {
                    'enabled': True,
                    'directory': tmpdir,
                    'filename': 'test.log',
                    'rotation': 'size',
                    'max_size_mb': 10,
                    'backup_count': 5
                }
            }
            
            logger = StructuredLogger('test_file', config)
            
            # Write log
            logger.info("Test message")
            
            # Check file exists
            log_file = Path(tmpdir) / 'test.log'
            assert log_file.exists()
            
            # Close handlers to release file lock on Windows
            for handler in logger.logger.handlers[:]:
                handler.close()
                logger.logger.removeHandler(handler)
    
    def test_get_logger_singleton(self):
        """Test get_logger returns same instance"""
        logger1 = get_logger('test_singleton')
        logger2 = get_logger('test_singleton')
        
        assert logger1 is logger2
    
    def test_log_methods(self):
        """Test different log level methods"""
        logger = StructuredLogger('test_methods', {'console': {'enabled': False}, 'file': {'enabled': False}})
        
        # Should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
