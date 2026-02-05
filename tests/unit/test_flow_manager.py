"""
Unit tests for Flow Manager
"""

import pytest
from unittest.mock import Mock

from src.controller.flow_manager import Flow, FlowManager


class TestFlow:
    """Test Flow class"""
    
    def test_flow_initialization(self):
        """Test Flow initialization"""
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
        
        assert flow.time_start == 1000
        assert flow.datapath == '1'
        assert flow.forward_packets == 100
        assert flow.forward_bytes == 5000
        assert flow.reverse_packets == 0
        assert flow.reverse_bytes == 0
    
    def test_update_forward(self):
        """Test updating forward direction"""
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01', 
                   '00:00:00:00:00:02', '2', 100, 5000)
        
        # Update with new values
        flow.update_forward(150, 7500, 1010)
        
        assert flow.forward_packets == 150
        assert flow.forward_bytes == 7500
        assert flow.forward_delta_packets == 50
        assert flow.forward_delta_bytes == 2500
        assert flow.forward_inst_pps > 0
        assert flow.forward_avg_pps > 0
    
    def test_update_reverse(self):
        """Test updating reverse direction"""
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01',
                   '00:00:00:00:00:02', '2', 100, 5000)
        
        # Update reverse
        flow.update_reverse(50, 2500, 1010)
        
        assert flow.reverse_packets == 50
        assert flow.reverse_bytes == 2500
        assert flow.reverse_delta_packets == 50
        assert flow.reverse_delta_bytes == 2500
    
    def test_flow_status_active(self):
        """Test flow status when active"""
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01',
                   '00:00:00:00:00:02', '2', 100, 5000)
        
        flow.update_forward(150, 7500, 1010)
        
        assert flow.forward_status == 'ACTIVE'
    
    def test_flow_status_inactive(self):
        """Test flow status when inactive"""
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01',
                   '00:00:00:00:00:02', '2', 100, 5000)
        
        # Update with same values (no change)
        flow.update_forward(100, 5000, 1010)
        
        assert flow.forward_status == 'INACTIVE'
    
    def test_assign_qos(self):
        """Test QoS assignment"""
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01',
                   '00:00:00:00:00:02', '2', 100, 5000)
        
        qos_config = {
            'classes': {
                'http': {
                    'class': 'BEST_EFFORT',
                    'priority': 2
                }
            },
            'default': {}
        }
        
        flow.assign_qos('http', qos_config)
        
        assert flow.qos_class == 'BEST_EFFORT'
        assert flow.priority == 2

    def test_get_flow_id(self):
        """Test flow ID generation"""
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01',
                   '00:00:00:00:00:02', '2', 100, 5000)
        
        flow_id = flow.get_flow_id()
        
        assert isinstance(flow_id, str)
        assert flow_id != ""
    
    def test_is_active(self):
        """Test is_active method"""
        flow = Flow(1000, '1', '1', '00:00:00:00:00:01',
                   '00:00:00:00:00:02', '2', 100, 5000)
        
        # Initially active
        assert flow.is_active()
        
        # Set inactive
        flow.forward_status = 'INACTIVE'
        flow.reverse_status = 'INACTIVE'
        
        assert not flow.is_active()


class TestFlowManager:
    """Test FlowManager class"""
    
    @pytest.fixture
    def flow_manager(self):
        """Create FlowManager instance"""
        return FlowManager(logger=Mock())
    
    def test_initialization(self, flow_manager):
        """Test FlowManager initialization"""
        assert isinstance(flow_manager.flows, dict)
        assert len(flow_manager.flows) == 0
    
    def test_process_flow_stats_new_flow(self, flow_manager):
        """Test processing new flow stats"""
        fields = ['1000', '1', '1', '00:00:00:00:00:01',
                 '00:00:00:00:00:02', '2', '100', '5000']
        
        flow = flow_manager.process_flow_stats(fields)
        
        assert flow is not None
        assert flow.forward_packets == 100
        assert flow.forward_bytes == 5000
        assert flow_manager.get_flow_count() == 1
    
    def test_process_flow_stats_existing_flow(self, flow_manager):
        """Test processing existing flow stats"""
        fields1 = ['1000', '1', '1', '00:00:00:00:00:01',
                  '00:00:00:00:00:02', '2', '100', '5000']
        
        fields2 = ['1010', '1', '1', '00:00:00:00:00:01',
                  '00:00:00:00:00:02', '2', '150', '7500']
        
        flow1 = flow_manager.process_flow_stats(fields1)
        flow2 = flow_manager.process_flow_stats(fields2)
        
        assert flow1 is flow2  # Same flow object
        assert flow2.forward_packets == 150
        assert flow2.forward_delta_packets == 50
        assert len(flow_manager.flows) == 1
    
    def test_process_flow_stats_reverse_flow(self, flow_manager):
        """Test processing reverse flow stats"""
        # Forward flow
        fields1 = ['1000', '1', '1', '00:00:00:00:00:01',
                  '00:00:00:00:00:02', '2', '100', '5000']
        
        # Reverse flow (swapped src/dst)
        fields2 = ['1010', '1', '2', '00:00:00:00:00:02',
                  '00:00:00:00:00:01', '1', '50', '2500']
        
        flow1 = flow_manager.process_flow_stats(fields1)
        flow2 = flow_manager.process_flow_stats(fields2)
        
        assert flow1 is flow2  # Same flow object
        assert flow2.reverse_packets == 50
        assert flow2.reverse_bytes == 2500
        assert len(flow_manager.flows) == 1
    
    def test_get_flow(self, flow_manager):
        """Test getting flow by ID"""
        fields = ['1000', '1', '1', '00:00:00:00:00:01',
                 '00:00:00:00:00:02', '2', '100', '5000']
        
        flow_manager.process_flow_stats(fields)
        
        # Calculate expected hash ID used by manager
        datapath, ethsrc, ethdst = fields[1], fields[3], fields[4]
        flow_id = hash(''.join([datapath, ethsrc, ethdst]))
        
        retrieved_flow = flow_manager.get_flow(flow_id)
        
        assert retrieved_flow is not None
        assert retrieved_flow.datapath == '1'
    
    def test_get_all_flows(self, flow_manager):
        """Test getting all flows"""
        # Add multiple flows
        for i in range(3):
            fields = ['1000', '1', '1', f'00:00:00:00:00:0{i}',
                     '00:00:00:00:00:FF', '2', '100', '5000']
            flow_manager.process_flow_stats(fields)
        
        all_flows = flow_manager.get_all_flows()
        
        assert isinstance(all_flows, dict)
        assert len(all_flows) == 3
    
    def test_get_active_flows(self, flow_manager):
        """Test getting only active flows"""
        # Add flows
        fields1 = ['1000', '1', '1', '00:00:00:00:00:01',
                  '00:00:00:00:00:02', '2', '100', '5000']
        fields2 = ['1000', '1', '1', '00:00:00:00:00:03',
                  '00:00:00:00:00:04', '2', '100', '5000']
        
        flow1 = flow_manager.process_flow_stats(fields1)
        flow2 = flow_manager.process_flow_stats(fields2)
        
        # Update flow1 to be active
        flow1.update_forward(150, 7500, 1010)
        
        # Update flow2 to be inactive
        flow2.update_forward(100, 5000, 1010)
        
        active_flows = flow_manager.get_active_flows()
        
        assert isinstance(active_flows, dict)
        assert len(active_flows) == 1
        assert list(active_flows.values())[0] is flow1
    
    def test_clear_inactive_flows(self, flow_manager):
        """Test clearing inactive flows"""
        # Add flow
        fields = ['1000', '1', '1', '00:00:00:00:00:01',
                 '00:00:00:00:00:02', '2', '100', '5000']
        
        flow = flow_manager.process_flow_stats(fields)
        
        # Make it old and inactive
        flow.forward_last_time = 0  # Very old
        flow.forward_status = 'INACTIVE'
        flow.reverse_status = 'INACTIVE'
        
        flow_manager.clear_inactive_flows(max_age=10)
        
        assert len(flow_manager.flows) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
