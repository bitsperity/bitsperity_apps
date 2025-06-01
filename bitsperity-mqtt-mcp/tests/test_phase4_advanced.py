"""
Phase 4 Tests für bitsperity-mqtt-mcp
Tests für Advanced Tools - debug_device, monitor_performance, test_connection
"""

import pytest
import pytest_asyncio
import asyncio
import sys
import os
import time

# Import der zu testenden Module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simple_mcp_server import SimpleMCPServer
from mqtt_connection_manager import MQTTConnectionManager
from mqtt_tools import MQTTTools


class TestPhase4AdvancedTools:
    """Test Phase 4 Advanced Tools Functionality"""
    
    @pytest_asyncio.fixture
    async def mcp_server(self):
        """Create MCP server instance for testing"""
        server = SimpleMCPServer()
        yield server
        await server.shutdown()
    
    @pytest_asyncio.fixture
    async def connected_session(self, mcp_server):
        """Create a connected MQTT session for testing"""
        # Establish connection
        establish_request = {
            "jsonrpc": "2.0",
            "method": "establish_connection",
            "params": {"connection_string": "mqtt://192.168.178.57:1883"},
            "id": 1
        }
        
        response = await mcp_server.handle_request(establish_request)
        
        if "result" in response and "session_id" in response["result"]:
            session_id = response["result"]["session_id"]
            yield session_id
            
            # Cleanup: close session
            try:
                close_request = {
                    "jsonrpc": "2.0",
                    "method": "close_connection",
                    "params": {"session_id": session_id},
                    "id": 999
                }
                await mcp_server.handle_request(close_request)
            except Exception:
                pass  # Ignore cleanup errors
        else:
            pytest.skip("Could not establish MQTT connection for testing")
    
    @pytest.mark.asyncio
    async def test_debug_device_tool_basic(self, mcp_server, connected_session):
        """Test debug_device tool basic functionality"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "debug_device",
            "params": {
                "session_id": connected_session,
                "device_id": "test_device_001"
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        
        result = response["result"]
        assert result["tool"] == "debug_device"
        assert result["session_id"] == connected_session
        assert result["device_id"] == "test_device_001"
        assert "device_topics" in result
        assert "recent_messages" in result
        assert "error_messages" in result
        assert "connection_status" in result
        assert "debug_summary" in result
        assert "analysis_duration_seconds" in result
        assert "timestamp" in result
        assert result["status"] == "success"
        
        # Debug summary should contain health assessment
        debug_summary = result["debug_summary"]
        assert "device_health" in debug_summary
        assert "message_activity" in debug_summary
        assert "topic_diversity" in debug_summary
        assert "error_count" in debug_summary
        assert "total_messages" in debug_summary
    
    @pytest.mark.asyncio
    async def test_debug_device_validation(self, mcp_server, connected_session):
        """Test debug_device tool parameter validation"""
        
        # Test missing device_id
        request = {
            "jsonrpc": "2.0",
            "method": "debug_device",
            "params": {
                "session_id": connected_session
                # Missing device_id
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        # Should be JSON-RPC error response for missing parameter
        assert response["jsonrpc"] == "2.0" 
        assert "error" in response
        assert "Invalid params" in response["error"]["message"]
        assert "device_id" in response["error"]["message"]
        
        # Test invalid session
        request = {
            "jsonrpc": "2.0",
            "method": "debug_device",
            "params": {
                "session_id": "invalid-session",
                "device_id": "test_device"
            },
            "id": 2
        }
        
        response = await mcp_server.handle_request(request)
        
        # Should be result with error status for invalid session
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        result = response["result"]
        assert result["status"] == "error"
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_monitor_performance_tool_basic(self, mcp_server, connected_session):
        """Test monitor_performance tool basic functionality"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "monitor_performance",
            "params": {
                "session_id": connected_session
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        
        result = response["result"]
        assert result["tool"] == "monitor_performance"
        assert result["session_id"] == connected_session
        assert "connection_info" in result
        assert "throughput_metrics" in result
        assert "latency_metrics" in result
        assert "memory_metrics" in result
        assert "session_metrics" in result
        assert "performance_summary" in result
        assert "monitoring_duration_seconds" in result
        assert "timestamp" in result
        assert result["status"] == "success"
        
        # Check throughput metrics structure
        throughput_metrics = result["throughput_metrics"]
        assert "messages_per_second_sent" in throughput_metrics
        assert "messages_per_second_received" in throughput_metrics
        assert "message_loss_rate" in throughput_metrics
        assert "test_duration_seconds" in throughput_metrics
        
        # Check latency metrics structure
        latency_metrics = result["latency_metrics"]
        assert "average_latency_ms" in latency_metrics
        assert "min_latency_ms" in latency_metrics
        assert "max_latency_ms" in latency_metrics
        assert "samples" in latency_metrics
        
        # Check memory metrics structure
        memory_metrics = result["memory_metrics"]
        assert "current_memory_mb" in memory_metrics
        assert "memory_change_mb" in memory_metrics
        assert "peak_memory_mb" in memory_metrics
        
        # Check performance summary
        performance_summary = result["performance_summary"]
        assert "overall_health" in performance_summary
        assert "throughput_rating" in performance_summary
        assert "latency_rating" in performance_summary
        assert "memory_efficiency" in performance_summary
    
    @pytest.mark.asyncio
    async def test_test_connection_tool_basic(self, mcp_server, connected_session):
        """Test test_connection tool basic functionality"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "test_connection",
            "params": {
                "session_id": connected_session
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        
        result = response["result"]
        assert result["tool"] == "test_connection"
        assert result["session_id"] == connected_session
        assert "broker_info" in result
        assert "connectivity_test" in result
        assert "authentication_test" in result
        assert "qos_tests" in result
        assert "network_diagnostics" in result
        assert "broker_diagnostics" in result
        assert "overall_health" in result
        assert "test_duration_seconds" in result
        assert "timestamp" in result
        assert result["status"] == "success"
        
        # Check connectivity test
        connectivity_test = result["connectivity_test"]
        assert "status" in connectivity_test
        assert "broker_reachable" in connectivity_test
        
        # Check QoS tests
        qos_tests = result["qos_tests"]
        assert "qos_0" in qos_tests or "qos_1" in qos_tests or "qos_2" in qos_tests
        
        # Check network diagnostics
        network_diagnostics = result["network_diagnostics"]
        assert "average_ping_ms" in network_diagnostics
        assert "network_stable" in network_diagnostics
        
        # Check overall health assessment
        assert result["overall_health"] in ["excellent", "good", "fair", "poor"]
    
    @pytest.mark.asyncio
    async def test_all_10_tools_registered(self, mcp_server):
        """Test that all 10 MVP tools are registered"""
        
        expected_tools = [
            # Phase 1 tools
            "establish_connection",
            "list_active_connections", 
            "close_connection",
            # Phase 2 tools
            "list_topics",
            "subscribe_and_collect",
            "publish_message",
            # Phase 3 tools
            "get_topic_schema",
            # Phase 4 tools
            "debug_device",
            "monitor_performance",
            "test_connection"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in mcp_server.tools, f"Tool {tool_name} not registered"
        
        # Should have exactly 10 tools
        assert len(mcp_server.tools) == 10, f"Expected 10 tools, got {len(mcp_server.tools)}"
    
    @pytest.mark.asyncio
    async def test_phase4_tools_respond_correctly(self, mcp_server):
        """Test that Phase 4 tools respond correctly to method calls"""
        
        # Define test cases with proper parameters for each tool
        phase4_tools = [
            ("debug_device", {"session_id": "invalid", "device_id": "test"}),
            ("monitor_performance", {"session_id": "invalid"}),
            ("test_connection", {"session_id": "invalid"})
        ]
        
        for tool_name, params in phase4_tools:
            request = {
                "jsonrpc": "2.0",
                "method": tool_name,
                "params": params,
                "id": 1
            }
            
            response = await mcp_server.handle_request(request)
            
            # Should get a response (not "method not found")
            assert response["jsonrpc"] == "2.0"
            assert "result" in response
            assert response["result"]["tool"] == tool_name
            # Should be an error due to invalid session, but tool is implemented
            assert response["result"]["status"] == "error"


class TestPhase4Performance:
    """Test Phase 4 Performance Characteristics"""
    
    @pytest.mark.asyncio
    async def test_advanced_tools_performance(self):
        """Test that advanced tools complete within reasonable time"""
        import time
        
        server = SimpleMCPServer()
        
        try:
            # Test tool response time (even with invalid session)
            tools_to_test = [
                ("debug_device", {"session_id": "invalid", "device_id": "test"}),
                ("monitor_performance", {"session_id": "invalid"}),
                ("test_connection", {"session_id": "invalid"})
            ]
            
            for tool_name, params in tools_to_test:
                request = {
                    "jsonrpc": "2.0",
                    "method": tool_name,
                    "params": params,
                    "id": 1
                }
                
                start_time = time.time()
                response = await server.handle_request(request)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # Should respond quickly even for errors
                assert response_time < 5.0, f"Tool {tool_name} took {response_time:.3f}s, expected <5.0s"
                
                # Should have valid response structure
                assert "result" in response
                assert response["result"]["tool"] == tool_name
                
        finally:
            await server.shutdown()
    
    @pytest.mark.asyncio
    async def test_server_memory_usage(self):
        """Test server memory usage is reasonable"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        
        # Create and use server
        server = SimpleMCPServer()
        
        try:
            # Simulate some tool usage
            for i in range(10):
                request = {
                    "jsonrpc": "2.0",
                    "method": "list_active_connections",
                    "params": {},
                    "id": i
                }
                await server.handle_request(request)
            
            memory_after = process.memory_info().rss
            memory_increase_mb = (memory_after - memory_before) / 1024 / 1024
            
            # Memory increase should be reasonable
            assert memory_increase_mb < 50, f"Memory increased by {memory_increase_mb:.2f}MB, expected <50MB"
            
        finally:
            await server.shutdown()


class TestPhase4Integration:
    """Test Phase 4 Integration Scenarios"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """Test complete workflow with all tool phases"""
        server = SimpleMCPServer()
        
        try:
            # Step 1: List connections (should be empty)
            list_request = {
                "jsonrpc": "2.0",
                "method": "list_active_connections",
                "params": {},
                "id": 1
            }
            
            response = await server.handle_request(list_request)
            assert response["result"]["total_count"] == 0
            
            # Step 2: Try to establish connection (may fail, but should respond)
            establish_request = {
                "jsonrpc": "2.0",
                "method": "establish_connection",
                "params": {"connection_string": "mqtt://test.mosquitto.org:1883"},
                "id": 2
            }
            
            response = await server.handle_request(establish_request)
            # Don't assert success since external broker may not be available
            assert "result" in response
            assert response["result"]["tool"] == "establish_connection"
            
            # Step 3: Test all advanced tools (with invalid session)
            advanced_tools = [
                ("debug_device", {"session_id": "invalid", "device_id": "test"}),
                ("monitor_performance", {"session_id": "invalid"}),
                ("test_connection", {"session_id": "invalid"})
            ]
            
            for i, (tool_name, params) in enumerate(advanced_tools):
                request = {
                    "jsonrpc": "2.0",
                    "method": tool_name,
                    "params": params,
                    "id": 10 + i
                }
                
                response = await server.handle_request(request)
                assert "result" in response
                assert response["result"]["tool"] == tool_name
                # Should be error due to invalid session, but tool responds
                assert response["result"]["status"] == "error"
            
        finally:
            await server.shutdown() 