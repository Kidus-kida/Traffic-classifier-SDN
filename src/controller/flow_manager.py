#!/usr/bin/env python3
"""
Flow Manager Module
Manages bidirectional network flows with statistics tracking
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass


class Flow:
    """
    Represents a bidirectional network flow with statistics.
    
    Tracks both forward (source -> destination) and reverse (destination -> source)
    directions with packet/byte counts and rates.
    """
    
    def __init__(self, time_start: int, datapath: str, inport: str,
                 ethsrc: str, ethdst: str, outport: str, packets: int, bytes_count: int):
        """
        Initialize flow.
        
        Args:
            time_start: Flow start timestamp
            datapath: Switch datapath ID
            inport: Input port
            ethsrc: Source MAC address
            ethdst: Destination MAC address
            outport: Output port
            packets: Initial packet count
            bytes_count: Initial byte count
        """
        self.time_start = time_start
        self.datapath = datapath
        self.inport = inport
        self.ethsrc = ethsrc
        self.ethdst = ethdst
        self.outport = outport
        
        # Forward direction attributes
        self.forward_packets = packets
        self.forward_bytes = bytes_count
        self.forward_delta_packets = 0
        self.forward_delta_bytes = 0
        self.forward_inst_pps = 0.0
        self.forward_avg_pps = 0.0
        self.forward_inst_bps = 0.0
        self.forward_avg_bps = 0.0
        self.forward_status = 'ACTIVE'
        self.forward_last_time = time_start
        
        # Reverse direction attributes
        self.reverse_packets = 0
        self.reverse_bytes = 0
        self.reverse_delta_packets = 0
        self.reverse_delta_bytes = 0
        self.reverse_inst_pps = 0.0
        self.reverse_avg_pps = 0.0
        self.reverse_inst_bps = 0.0
        self.reverse_avg_bps = 0.0
        self.reverse_status = 'INACTIVE'
        self.reverse_last_time = time_start
        
        # Classification attributes
        self.predicted_type: Optional[str] = None
        self.confidence: float = 0.0
        self.qos_class: str = 'BEST_EFFORT'
        self.priority: int = 0
        self.flow_rule_installed: bool = False
        self.classification_history: list = []
    
    def update_forward(self, packets: int, bytes_count: int, curr_time: int):
        """
        Update forward direction statistics.
        
        Args:
            packets: Current packet count
            bytes_count: Current byte count
            curr_time: Current timestamp
        """
        # Calculate deltas
        self.forward_delta_packets = packets - self.forward_packets
        self.forward_delta_bytes = bytes_count - self.forward_bytes
        
        # Update counters
        self.forward_packets = packets
        self.forward_bytes = bytes_count
        
        # Calculate rates
        if curr_time != self.time_start:
            self.forward_avg_pps = packets / float(curr_time - self.time_start)
            self.forward_avg_bps = bytes_count / float(curr_time - self.time_start)
        
        if curr_time != self.forward_last_time:
            time_diff = float(curr_time - self.forward_last_time)
            self.forward_inst_pps = self.forward_delta_packets / time_diff
            self.forward_inst_bps = self.forward_delta_bytes / time_diff
        
        self.forward_last_time = curr_time
        
        # Update status
        if self.forward_delta_bytes == 0 or self.forward_delta_packets == 0:
            self.forward_status = 'INACTIVE'
        else:
            self.forward_status = 'ACTIVE'
    
    def update_reverse(self, packets: int, bytes_count: int, curr_time: int):
        """
        Update reverse direction statistics.
        
        Args:
            packets: Current packet count
            bytes_count: Current byte count
            curr_time: Current timestamp
        """
        # Calculate deltas
        self.reverse_delta_packets = packets - self.reverse_packets
        self.reverse_delta_bytes = bytes_count - self.reverse_bytes
        
        # Update counters
        self.reverse_packets = packets
        self.reverse_bytes = bytes_count
        
        # Calculate rates
        if curr_time != self.time_start:
            self.reverse_avg_pps = packets / float(curr_time - self.time_start)
            self.reverse_avg_bps = bytes_count / float(curr_time - self.time_start)
        
        if curr_time != self.reverse_last_time:
            time_diff = float(curr_time - self.reverse_last_time)
            self.reverse_inst_pps = self.reverse_delta_packets / time_diff
            self.reverse_inst_bps = self.reverse_delta_bytes / time_diff
        
        self.reverse_last_time = curr_time
        
        # Update status
        if self.reverse_delta_bytes == 0 or self.reverse_delta_packets == 0:
            self.reverse_status = 'INACTIVE'
        else:
            self.reverse_status = 'ACTIVE'
    
    def assign_qos(self, traffic_type: str, qos_config: dict):
        """
        Assign QoS class based on traffic type.
        
        Args:
            traffic_type: Classified traffic type
            qos_config: QoS configuration dict
        """
        qos_classes = qos_config.get('classes', {})
        default_qos = qos_config.get('default', {})
        
        qos_info = qos_classes.get(traffic_type, default_qos)
        
        self.qos_class = qos_info.get('class', 'BEST_EFFORT')
        self.priority = qos_info.get('priority', 0)
    
    def get_flow_id(self) -> str:
        """Get unique flow identifier"""
        return f"{self.ethsrc}_{self.ethdst}_{self.datapath}"
    
    def is_active(self) -> bool:
        """Check if flow is active"""
        return self.forward_status == 'ACTIVE' or self.reverse_status == 'ACTIVE'


class FlowManager:
    """
    Manages collection of network flows.
    
    Handles flow creation, updates, and lifecycle management.
    """
    
    def __init__(self, logger=None):
        """
        Initialize flow manager.
        
        Args:
            logger: Optional logger instance
        """
        self.flows: Dict[int, Flow] = {}
        self.logger = logger
    
    def process_flow_stats(self, fields: list) -> Optional[Flow]:
        """
        Process flow statistics from Ryu controller.
        
        Args:
            fields: List of flow stat fields [time, datapath, inport, ethsrc, ethdst, outport, packets, bytes]
            
        Returns:
            Flow object if processed, None otherwise
        """
        try:
            # Parse fields
            timestamp = int(fields[0])
            datapath = fields[1]
            inport = fields[2]
            ethsrc = fields[3]
            ethdst = fields[4]
            outport = fields[5]
            packets = int(fields[6])
            bytes_count = int(fields[7])
            
            # Generate unique flow ID
            unique_id = hash(''.join([datapath, ethsrc, ethdst]))
            
            if unique_id in self.flows:
                # Update existing flow (forward direction)
                self.flows[unique_id].update_forward(packets, bytes_count, timestamp)
                return self.flows[unique_id]
            else:
                # Check for reverse flow
                rev_unique_id = hash(''.join([datapath, ethdst, ethsrc]))
                
                if rev_unique_id in self.flows:
                    # Update reverse direction
                    self.flows[rev_unique_id].update_reverse(packets, bytes_count, timestamp)
                    return self.flows[rev_unique_id]
                else:
                    # Create new flow
                    flow = Flow(timestamp, datapath, inport, ethsrc, ethdst, 
                              outport, packets, bytes_count)
                    self.flows[unique_id] = flow
                    return flow
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error processing flow stats: {e}")
            return None
    
    def get_flow(self, flow_id: int) -> Optional[Flow]:
        """Get flow by ID"""
        return self.flows.get(flow_id)
    
    def get_all_flows(self) -> Dict[int, Flow]:
        """Get all flows"""
        return self.flows
    
    def get_active_flows(self) -> Dict[int, Flow]:
        """Get only active flows"""
        return {fid: flow for fid, flow in self.flows.items() if flow.is_active()}
    
    def get_flow_count(self) -> int:
        """Get total flow count"""
        return len(self.flows)
    
    def get_active_flow_count(self) -> int:
        """Get active flow count"""
        return len(self.get_active_flows())
    
    def clear_inactive_flows(self, max_age: int = 300):
        """
        Remove inactive flows older than max_age.
        
        Args:
            max_age: Maximum age in seconds
        """
        current_time = int(time.time())
        to_remove = []
        
        for fid, flow in self.flows.items():
            if not flow.is_active():
                age = current_time - flow.forward_last_time
                if age > max_age:
                    to_remove.append(fid)
        
        for fid in to_remove:
            del self.flows[fid]
        
        if self.logger and to_remove:
            self.logger.info(f"Removed {len(to_remove)} inactive flows")
