#!/usr/bin/env python3
"""
Structured Logging System
Provides JSON-formatted logging with context and multiple outputs
"""

import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'flow_id'):
            log_data['flow_id'] = record.flow_id
        if hasattr(record, 'traffic_type'):
            log_data['traffic_type'] = record.traffic_type
        if hasattr(record, 'confidence'):
            log_data['confidence'] = record.confidence
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class StructuredLogger:
    """
    Structured logging system with JSON output and context support.
    
    Features:
    - JSON and text output formats
    - Multiple destinations (console, file)
    - Log rotation
    - Context-aware logging
    - Performance tracking
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            config: Logging configuration dict
        """
        self.logger = logging.getLogger(name)
        self.config = config or {}
        
        # Set log level
        level_str = self.config.get('level', 'INFO')
        self.logger.setLevel(getattr(logging, level_str))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_console_handler()
        self._setup_file_handler()
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _setup_console_handler(self):
        """Setup console output handler"""
        console_config = self.config.get('console', {})
        
        if not console_config.get('enabled', True):
            return
        
        handler = logging.StreamHandler(sys.stdout)
        
        # Set level
        level_str = console_config.get('level', 'INFO')
        handler.setLevel(getattr(logging, level_str))
        
        # Set formatter based on format type
        format_type = self.config.get('format', 'text')
        if format_type == 'json':
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(TextFormatter())
        
        self.logger.addHandler(handler)
    
    def _setup_file_handler(self):
        """Setup file output handler with rotation"""
        file_config = self.config.get('file', {})
        
        if not file_config.get('enabled', True):
            return
        
        # Create log directory
        log_dir = Path(file_config.get('directory', 'logs'))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file path
        log_file = log_dir / file_config.get('filename', 'classifier.log')
        
        # Choose rotation type
        rotation = file_config.get('rotation', 'size')
        
        if rotation == 'time':
            handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=file_config.get('backup_count', 5)
            )
        else:  # size-based rotation
            max_bytes = file_config.get('max_size_mb', 10) * 1024 * 1024
            handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=file_config.get('backup_count', 5)
            )
        
        # Set level
        level_str = file_config.get('level', 'DEBUG')
        handler.setLevel(getattr(logging, level_str))
        
        # Always use JSON for file output
        handler.setFormatter(JSONFormatter())
        
        self.logger.addHandler(handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional context"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional context"""
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)
    
    def log_flow_classification(self, flow_id: str, traffic_type: str, 
                               confidence: float, duration_ms: float):
        """Log flow classification with structured data"""
        self.info(
            f"Flow classified as {traffic_type}",
            flow_id=flow_id,
            traffic_type=traffic_type,
            confidence=confidence,
            duration_ms=duration_ms
        )
    
    def log_model_load(self, algorithm: str, model_path: str, success: bool):
        """Log model loading event"""
        if success:
            self.info(f"Model loaded successfully: {algorithm}", 
                     algorithm=algorithm, model_path=model_path)
        else:
            self.error(f"Failed to load model: {algorithm}",
                      algorithm=algorithm, model_path=model_path)
    
    def log_controller_event(self, event_type: str, details: Dict[str, Any]):
        """Log controller event"""
        self.info(f"Controller event: {event_type}", 
                 event_type=event_type, **details)
    
    def log_performance(self, operation: str, duration_ms: float, 
                       success: bool = True):
        """Log performance metric"""
        level = self.info if success else self.warning
        level(f"Operation {operation} completed in {duration_ms:.2f}ms",
              operation=operation, duration_ms=duration_ms, success=success)


# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, config: Optional[Dict[str, Any]] = None) -> StructuredLogger:
    """
    Get or create logger instance.
    
    Args:
        name: Logger name
        config: Optional logging configuration
        
    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, config)
    
    return _loggers[name]


def setup_logging(config: Dict[str, Any]):
    """
    Setup global logging configuration.
    
    Args:
        config: Logging configuration dict
    """
    # Clear existing loggers
    _loggers.clear()
    
    # Create root logger
    root_logger = get_logger('traffic_classifier', config)
    
    return root_logger
