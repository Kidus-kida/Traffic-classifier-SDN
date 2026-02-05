#!/usr/bin/env python3
"""
Health Monitoring System
Provides system health checks and status monitoring
"""

import time
import psutil
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


@dataclass
class HealthStatus:
    """Health status data structure"""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    uptime_seconds: float
    components: Dict[str, bool]
    metrics: Dict[str, Any]
    errors: list


class HealthMonitor:
    """
    System health monitoring.
    
    Tracks:
    - Component status (controller, model, dashboard)
    - System metrics (CPU, memory, flows)
    - Uptime and errors
    """
    
    def __init__(self):
        """Initialize health monitor"""
        self.start_time = time.time()
        self.components = {
            'controller': False,
            'model': False,
            'dashboard': False
        }
        self.errors = []
        self.max_errors = 100
        
    def set_component_status(self, component: str, status: bool):
        """
        Update component status.
        
        Args:
            component: Component name
            status: True if healthy, False if unhealthy
        """
        if component in self.components:
            self.components[component] = status
    
    def add_error(self, error: str):
        """
        Add error to error log.
        
        Args:
            error: Error message
        """
        self.errors.append({
            'timestamp': datetime.utcnow().isoformat(),
            'error': error
        })
        
        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_mb': psutil.virtual_memory().used / (1024 * 1024),
            'disk_percent': psutil.disk_usage('/').percent
        }
    
    def check_health(self, flow_count: int = 0, 
                    active_flows: int = 0) -> HealthStatus:
        """
        Perform health check.
        
        Args:
            flow_count: Total number of flows
            active_flows: Number of active flows
            
        Returns:
            HealthStatus object
        """
        # Determine overall status
        all_healthy = all(self.components.values())
        any_healthy = any(self.components.values())
        
        if all_healthy:
            status = 'healthy'
        elif any_healthy:
            status = 'degraded'
        else:
            status = 'unhealthy'
        
        # Get metrics
        metrics = self.get_system_metrics()
        metrics.update({
            'total_flows': flow_count,
            'active_flows': active_flows
        })
        
        return HealthStatus(
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=self.get_uptime(),
            components=self.components.copy(),
            metrics=metrics,
            errors=self.errors[-10:]  # Last 10 errors
        )
    
    def to_dict(self, flow_count: int = 0, active_flows: int = 0) -> Dict[str, Any]:
        """Get health status as dictionary"""
        health = self.check_health(flow_count, active_flows)
        return asdict(health)


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance"""
    global _health_monitor
    
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    
    return _health_monitor
