#!/usr/bin/env python3
"""
Configuration Management System
Loads and validates YAML configuration with environment overrides
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class ControllerConfig:
    """SDN Controller configuration"""
    ryu_executable: str
    listen_port: int
    monitor_script: str
    log_level: str
    retry_attempts: int
    retry_delay: int
    timeout: int
    health_check_interval: int


@dataclass
class ClassificationConfig:
    """Traffic classification configuration"""
    traffic_types: list
    confidence_threshold: float
    classification_interval: int
    flow_history_size: int
    models_directory: str
    default_algorithm: str
    available_algorithms: list
    model_files: Dict[str, str]
    fallback_enabled: bool
    fallback_method: str
    default_class: str


@dataclass
class QoSConfig:
    """Quality of Service configuration"""
    classes: Dict[str, Dict[str, Any]]
    default: Dict[str, Any]


class ConfigurationManager:
    """
    Centralized configuration management system.
    
    Loads configuration from YAML files with environment-specific overrides.
    Validates configuration and provides type-safe access to settings.
    """
    
    def __init__(self, config_file: Optional[str] = None, environment: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (default: config/default.yaml)
            environment: Environment name (development, production, testing)
        """
        self.base_dir = Path(__file__).parent.parent.parent
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        
        self.config_dir = self.base_dir / 'src' / 'utils' / 'config'
        
        # Load configuration
        if config_file is None:
            config_file = self.config_dir / 'default.yaml'
        else:
            config_file = Path(config_file)
            
        self.config = self._load_config(config_file)
        self._apply_environment_overrides()
        self._validate_config()
        self._ensure_directories()
        
    def _load_config(self, config_file: Path) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
        if config is None:
            raise ValueError(f"Empty configuration file: {config_file}")
            
        return config
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides"""
        env_config_file = self.config_dir / f'{self.environment}.yaml'
        
        if env_config_file.exists():
            with open(env_config_file, 'r') as f:
                env_config = yaml.safe_load(f)
                if env_config:
                    self._deep_merge(self.config, env_config)
        
        # Apply environment variable overrides
        self._apply_env_vars()
    
    def _apply_env_vars(self):
        """Apply environment variable overrides"""
        # Controller settings
        if os.getenv('RYU_PORT'):
            self.config['controller']['ryu']['listen_port'] = int(os.getenv('RYU_PORT'))
        
        # Dashboard settings
        if os.getenv('DASHBOARD_PORT'):
            self.config['dashboard']['port'] = int(os.getenv('DASHBOARD_PORT'))
        
        # Logging level
        if os.getenv('LOG_LEVEL'):
            self.config['logging']['level'] = os.getenv('LOG_LEVEL')
    
    def _deep_merge(self, base: Dict, override: Dict):
        """Deep merge override dict into base dict"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _validate_config(self):
        """Validate configuration structure and values"""
        required_sections = ['system', 'controller', 'classification', 'qos', 'logging']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate controller settings
        controller = self.config['controller']['ryu']
        if controller['listen_port'] < 1024 or controller['listen_port'] > 65535:
            raise ValueError(f"Invalid controller port: {controller['listen_port']}")
        
        # Validate classification settings
        classification = self.config['classification']
        if not 0 <= classification['confidence_threshold'] <= 1:
            raise ValueError(f"Invalid confidence threshold: {classification['confidence_threshold']}")
        
        # Validate traffic types
        if not classification['traffic_types']:
            raise ValueError("No traffic types configured")
    
    def _ensure_directories(self):
        """Create required directories if they don't exist"""
        paths = self.config.get('paths', {})
        create_dirs = paths.get('create_if_missing', [])
        
        for dir_name in create_dirs:
            dir_path = self.base_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'controller.ryu.listen_port')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_controller_config(self) -> ControllerConfig:
        """Get typed controller configuration"""
        ryu = self.config['controller']['ryu']
        conn = self.config['controller']['connection']
        
        return ControllerConfig(
            ryu_executable=ryu['executable'],
            listen_port=ryu['listen_port'],
            monitor_script=ryu['monitor_script'],
            log_level=ryu['log_level'],
            retry_attempts=conn['retry_attempts'],
            retry_delay=conn['retry_delay'],
            timeout=conn['timeout'],
            health_check_interval=conn['health_check_interval']
        )
    
    def get_classification_config(self) -> ClassificationConfig:
        """Get typed classification configuration"""
        cls = self.config['classification']
        
        return ClassificationConfig(
            traffic_types=cls['traffic_types'],
            confidence_threshold=cls['confidence_threshold'],
            classification_interval=cls['classification_interval'],
            flow_history_size=cls['flow_history_size'],
            models_directory=cls['models']['directory'],
            default_algorithm=cls['models']['default_algorithm'],
            available_algorithms=cls['models']['available_algorithms'],
            model_files=cls['models']['files'],
            fallback_enabled=cls['fallback']['enabled'],
            fallback_method=cls['fallback']['method'],
            default_class=cls['fallback']['default_class']
        )
    
    def get_qos_config(self) -> QoSConfig:
        """Get typed QoS configuration"""
        qos = self.config['qos']
        
        return QoSConfig(
            classes=qos['classes'],
            default=qos['default']
        )
    
    def get_model_path(self, algorithm: str) -> Path:
        """Get full path to model file"""
        models_dir = self.base_dir / self.config['classification']['models']['directory']
        model_file = self.config['classification']['models']['files'].get(algorithm)
        
        if not model_file:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        return models_dir / model_file
    
    def get_dataset_path(self, traffic_type: str) -> Path:
        """Get full path to dataset file"""
        datasets_dir = self.base_dir / self.config['training']['data_directory']
        return datasets_dir / f"{traffic_type}_training_data.csv"
    
    def resolve_path(self, relative_path: str) -> Path:
        """Resolve relative path to absolute path"""
        return self.base_dir / relative_path


# Global configuration instance
_config_instance: Optional[ConfigurationManager] = None


def get_config(config_file: Optional[str] = None, 
               environment: Optional[str] = None) -> ConfigurationManager:
    """
    Get global configuration instance (singleton pattern).
    
    Args:
        config_file: Path to configuration file
        environment: Environment name
        
    Returns:
        ConfigurationManager instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ConfigurationManager(config_file, environment)
    
    return _config_instance


def reload_config(config_file: Optional[str] = None, 
                  environment: Optional[str] = None):
    """Reload configuration (useful for testing)"""
    global _config_instance
    _config_instance = ConfigurationManager(config_file, environment)
    return _config_instance
