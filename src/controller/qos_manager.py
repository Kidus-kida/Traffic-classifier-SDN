#!/usr/bin/env python3
"""
QoS Manager Module
Manages Quality of Service policies and OpenFlow rule installation
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from ..utils.logger import get_logger


@dataclass
class FlowRule:
    """OpenFlow flow rule data structure"""
    timestamp: str
    flow_id: int
    src_mac: str
    dst_mac: str
    traffic_type: str
    qos_class: str
    priority: int
    action: str
    datapath: str
    in_port: str
    out_port: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class QoSManager:
    """
    Manages Quality of Service policies and flow rule installation.
    
    Features:
    - QoS class assignment based on traffic type
    - Flow rule generation
    - Rule persistence
    - Duplicate prevention
    - Action mapping
    """
    
    def __init__(self, config, logger=None):
        """
        Initialize QoS manager.
        
        Args:
            config: Configuration object
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or get_logger('qos_manager')
        
        # Load QoS configuration
        self.qos_config = config.get_qos_config()
        
        # Flow rules storage
        self.flow_rules_file = config.resolve_path('flow_rules/installed_rules.json')
        self.installed_rules: Dict[int, FlowRule] = {}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.flow_rules_file), exist_ok=True)
        
        # Load existing rules
        self._load_existing_rules()
    
    def _load_existing_rules(self):
        """Load previously installed rules from file"""
        if os.path.exists(self.flow_rules_file):
            try:
                with open(self.flow_rules_file, 'r') as f:
                    rules_data = json.load(f)
                    
                for rule_dict in rules_data:
                    rule = FlowRule(**rule_dict)
                    self.installed_rules[rule.flow_id] = rule
                    
                self.logger.info(f"Loaded {len(self.installed_rules)} existing flow rules")
            except Exception as e:
                self.logger.error(f"Failed to load existing rules: {e}")
    
    def assign_qos_class(self, traffic_type: str) -> tuple[str, int]:
        """
        Assign QoS class and priority based on traffic type.
        
        Args:
            traffic_type: Classified traffic type
            
        Returns:
            Tuple of (qos_class, priority)
        """
        qos_classes = self.qos_config.classes
        default_qos = self.qos_config.default
        
        # Get QoS info for traffic type
        qos_info = qos_classes.get(traffic_type, default_qos)
        
        qos_class = qos_info.get('class', 'BEST_EFFORT')
        priority = qos_info.get('priority', 0)
        
        return qos_class, priority
    
    def get_flow_action(self, traffic_type: str) -> str:
        """
        Get flow action based on traffic type.
        
        Args:
            traffic_type: Classified traffic type
            
        Returns:
            Action string (FORWARD, PRIORITY_FORWARD, DROP, etc.)
        """
        qos_classes = self.qos_config.classes
        default_qos = self.qos_config.default
        
        qos_info = qos_classes.get(traffic_type, default_qos)
        action = qos_info.get('action', 'FORWARD')
        
        return action
    
    def should_install_rule(self, flow_id: int, confidence: float) -> bool:
        """
        Determine if flow rule should be installed.
        
        Args:
            flow_id: Flow identifier
            confidence: Classification confidence
            
        Returns:
            True if rule should be installed
        """
        # Check if rule already installed
        if flow_id in self.installed_rules:
            return False
        
        # Check confidence threshold
        confidence_threshold = self.config.get('classification.confidence_threshold', 0.7)
        if confidence < confidence_threshold:
            return False
        
        # Check if auto-installation is enabled
        auto_install = self.config.get('flow_rules.auto_install', False)
        if not auto_install:
            return False
        
        return True
    
    def create_flow_rule(self, flow, traffic_type: str, confidence: float) -> Optional[FlowRule]:
        """
        Create flow rule for classified flow.
        
        Args:
            flow: Flow object
            traffic_type: Classified traffic type
            confidence: Classification confidence
            
        Returns:
            FlowRule object if created, None otherwise
        """
        flow_id = hash(f"{flow.ethsrc}{flow.ethdst}{flow.datapath}")
        
        # Check if should install
        if not self.should_install_rule(flow_id, confidence):
            return None
        
        # Get QoS class and priority
        qos_class, priority = self.assign_qos_class(traffic_type)
        
        # Get action
        action = self.get_flow_action(traffic_type)
        
        # Create rule
        rule = FlowRule(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            flow_id=flow_id,
            src_mac=flow.ethsrc,
            dst_mac=flow.ethdst,
            traffic_type=traffic_type,
            qos_class=qos_class,
            priority=priority,
            action=action,
            datapath=flow.datapath,
            in_port=flow.inport,
            out_port=flow.outport
        )
        
        return rule
    
    def install_flow_rule(self, rule: FlowRule) -> bool:
        """
        Install flow rule and persist to storage.
        
        Args:
            rule: FlowRule object
            
        Returns:
            True if successful
        """
        try:
            # Add to installed rules
            self.installed_rules[rule.flow_id] = rule
            
            # Persist to file
            self._save_rules()
            
            # Log installation
            self.logger.info(
                f"Flow rule installed: {rule.traffic_type} → {rule.qos_class}",
                flow_id=rule.flow_id,
                traffic_type=rule.traffic_type,
                qos_class=rule.qos_class,
                priority=rule.priority,
                action=rule.action
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install flow rule: {e}")
            return False
    
    def _save_rules(self):
        """Save installed rules to file"""
        try:
            rules_list = [rule.to_dict() for rule in self.installed_rules.values()]
            
            with open(self.flow_rules_file, 'w') as f:
                json.dump(rules_list, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save rules: {e}")
    
    def get_installed_rules(self) -> List[FlowRule]:
        """Get list of all installed rules"""
        return list(self.installed_rules.values())
    
    def get_rule_count(self) -> int:
        """Get count of installed rules"""
        return len(self.installed_rules)
    
    def get_rules_by_traffic_type(self, traffic_type: str) -> List[FlowRule]:
        """Get rules for specific traffic type"""
        return [
            rule for rule in self.installed_rules.values()
            if rule.traffic_type == traffic_type
        ]
    
    def get_rules_by_qos_class(self, qos_class: str) -> List[FlowRule]:
        """Get rules for specific QoS class"""
        return [
            rule for rule in self.installed_rules.values()
            if rule.qos_class == qos_class
        ]
    
    def clear_old_rules(self, max_age_seconds: int = 3600):
        """
        Remove rules older than specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds
        """
        current_time = datetime.utcnow()
        to_remove = []
        
        for flow_id, rule in self.installed_rules.items():
            rule_time = datetime.fromisoformat(rule.timestamp.replace('Z', '+00:00'))
            age = (current_time - rule_time.replace(tzinfo=None)).total_seconds()
            
            if age > max_age_seconds:
                to_remove.append(flow_id)
        
        for flow_id in to_remove:
            del self.installed_rules[flow_id]
        
        if to_remove:
            self._save_rules()
            self.logger.info(f"Removed {len(to_remove)} old flow rules")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get QoS statistics"""
        stats = {
            'total_rules': len(self.installed_rules),
            'by_traffic_type': {},
            'by_qos_class': {},
            'by_action': {}
        }
        
        for rule in self.installed_rules.values():
            # Count by traffic type
            stats['by_traffic_type'][rule.traffic_type] = \
                stats['by_traffic_type'].get(rule.traffic_type, 0) + 1
            
            # Count by QoS class
            stats['by_qos_class'][rule.qos_class] = \
                stats['by_qos_class'].get(rule.qos_class, 0) + 1
            
            # Count by action
            stats['by_action'][rule.action] = \
                stats['by_action'].get(rule.action, 0) + 1
        
        return stats
