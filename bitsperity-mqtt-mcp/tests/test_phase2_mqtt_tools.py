"""
Phase 2 Integration Tests für bitsperity-mqtt-mcp
Tests für die 3 neuen MQTT Core Tools
"""

import pytest
import pytest_asyncio
import asyncio
import sys
import os

# Import der zu testenden Module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simple_mcp_server import SimpleMCPServer
from mqtt_connection_manager import MQTTConnectionManager
from mqtt_tools import MQTTTools


class TestPhase2MQTTTools:
    """Test Phase 2 MQTT Tools Functionality"""
    
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
    async def test_list_topics_tool_basic(self, mcp_server, connected_session):
        """Test list_topics tool basic functionality"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "list_topics",
            "params": {
                "session_id": connected_session,
                "pattern": "#"  # Discover all topics
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        
        result = response["result"]
        assert result["tool"] == "list_topics"
        assert result["session_id"] == connected_session
        assert result["pattern"] == "#"
        assert "topics" in result
        assert "topic_count" in result
        assert "discovery_duration_seconds" in result
        assert "timestamp" in result
        assert result["status"] == "success"
        
        # Topics should be a list
        assert isinstance(result["topics"], list)
        assert result["topic_count"] == len(result["topics"])
    
    @pytest.mark.asyncio
    async def test_list_topics_with_pattern(self, mcp_server, connected_session):
        """Test list_topics tool with specific pattern"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "list_topics",
            "params": {
                "session_id": connected_session,
                "pattern": "$SYS/#"  # System topics
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        
        result = response["result"]
        assert result["pattern"] == "$SYS/#"
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_list_topics_invalid_session(self, mcp_server):
        """Test list_topics tool with invalid session"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "list_topics",
            "params": {
                "session_id": "invalid-session-id",
                "pattern": "#"
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        
        result = response["result"]
        assert result["status"] == "error"
        assert "Session" in result["error"] and "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_subscribe_and_collect_tool_basic(self, mcp_server, connected_session):
        """Test subscribe_and_collect tool basic functionality"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "subscribe_and_collect",
            "params": {
                "session_id": connected_session,
                "topic_pattern": "#",  # Collect all messages
                "duration_seconds": 10  # Short duration for testing
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        
        result = response["result"]
        assert result["tool"] == "subscribe_and_collect"
        assert result["session_id"] == connected_session
        assert result["topic_pattern"] == "#"
        assert result["duration_requested"] == 10
        assert "messages" in result
        assert "message_count" in result
        assert "collection_duration_seconds" in result
        assert "timestamp" in result
        assert result["status"] == "success"
        
        # Messages should be a list
        assert isinstance(result["messages"], list)
        assert result["message_count"] == len(result["messages"])
        
        # Duration should be approximately 10 seconds
        assert 9 <= result["collection_duration_seconds"] <= 12
    
    @pytest.mark.asyncio
    async def test_subscribe_and_collect_duration_validation(self, mcp_server, connected_session):
        """Test subscribe_and_collect tool duration validation"""
        
        # Test too short duration
        request = {
            "jsonrpc": "2.0",
            "method": "subscribe_and_collect",
            "params": {
                "session_id": connected_session,
                "topic_pattern": "#",
                "duration_seconds": 5  # Too short (min is 10)
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        result = response["result"]
        assert result["status"] == "error"
        assert "between 10 and 300" in result["error"]
        
        # Test too long duration
        request = {
            "jsonrpc": "2.0",
            "method": "subscribe_and_collect",
            "params": {
                "session_id": connected_session,
                "topic_pattern": "#",
                "duration_seconds": 400  # Too long (max is 300)
            },
            "id": 2
        }
        
        response = await mcp_server.handle_request(request)
        result = response["result"]
        assert result["status"] == "error"
        assert "between 10 and 300" in result["error"]
    
    @pytest.mark.asyncio
    async def test_publish_message_tool_basic(self, mcp_server, connected_session):
        """Test publish_message tool basic functionality"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "publish_message",
            "params": {
                "session_id": connected_session,
                "topic": "test/bitsperity/mqtt/mcp",
                "payload": "Hello from Phase 2 MCP!",
                "qos": 0,
                "retain": False
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        
        result = response["result"]
        assert result["tool"] == "publish_message"
        assert result["session_id"] == connected_session
        assert result["topic"] == "test/bitsperity/mqtt/mcp"
        assert result["payload"] == "Hello from Phase 2 MCP!"
        assert result["qos"] == 0
        assert result["retain"] == False
        assert "payload_size_bytes" in result
        assert "publish_duration_seconds" in result
        assert "timestamp" in result
        assert result["status"] == "success"
        
        # Payload size should be correct
        expected_size = len("Hello from Phase 2 MCP!".encode('utf-8'))
        assert result["payload_size_bytes"] == expected_size
    
    @pytest.mark.asyncio
    async def test_publish_message_qos_validation(self, mcp_server, connected_session):
        """Test publish_message tool QoS validation"""
        
        # Test invalid QoS
        request = {
            "jsonrpc": "2.0",
            "method": "publish_message",
            "params": {
                "session_id": connected_session,
                "topic": "test/qos",
                "payload": "test",
                "qos": 3  # Invalid QoS (must be 0, 1, or 2)
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        result = response["result"]
        assert result["status"] == "error"
        assert "qos must be 0, 1, or 2" in result["error"]
    
    @pytest.mark.asyncio
    async def test_publish_message_topic_validation(self, mcp_server, connected_session):
        """Test publish_message tool topic validation"""
        
        # Test topic with wildcards (not allowed for publishing)
        request = {
            "jsonrpc": "2.0",
            "method": "publish_message",
            "params": {
                "session_id": connected_session,
                "topic": "test/+/wildcard",  # Wildcards not allowed
                "payload": "test"
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        result = response["result"]
        assert result["status"] == "error"
        assert "Wildcards" in result["error"]
    
    @pytest.mark.asyncio
    async def test_publish_subscribe_integration(self, mcp_server, connected_session):
        """Test integration between publish and subscribe tools"""
        
        # First, start collecting messages from our test topic
        collect_request = {
            "jsonrpc": "2.0",
            "method": "subscribe_and_collect",
            "params": {
                "session_id": connected_session,
                "topic_pattern": "test/integration/+",
                "duration_seconds": 15  # Give enough time for publishing
            },
            "id": 1
        }
        
        # Start collection task
        collect_task = asyncio.create_task(mcp_server.handle_request(collect_request))
        
        # Wait a moment for subscription to be established
        await asyncio.sleep(2)
        
        # Publish a test message
        publish_request = {
            "jsonrpc": "2.0",
            "method": "publish_message",
            "params": {
                "session_id": connected_session,
                "topic": "test/integration/phase2",
                "payload": "Integration test message",
                "qos": 1
            },
            "id": 2
        }
        
        publish_response = await mcp_server.handle_request(publish_request)
        
        # Verify publish was successful
        assert publish_response["result"]["status"] == "success"
        
        # Wait for collection to complete
        collect_response = await collect_task
        
        # Verify we collected our published message
        assert collect_response["result"]["status"] == "success"
        messages = collect_response["result"]["messages"]
        
        # Check if our message was collected
        found_message = False
        for message in messages:
            if (message["topic"] == "test/integration/phase2" and 
                message["payload"] == "Integration test message"):
                found_message = True
                # Note: QoS might be downgraded by broker (e.g., QoS 1 -> QoS 0)
                # This is normal MQTT broker behavior
                assert message["qos"] in [0, 1], f"QoS should be 0 or 1, got {message['qos']}"
                break
        
        # Verify we found and successfully received our published message
        assert found_message, "Published message not found in collection"
        
        # Note: This test validates the complete publish->subscribe integration works
        print(f"✅ Integration test successful: Found message with QoS {message.get('qos', 'unknown') if found_message else 'N/A'}")


class TestPhase2ToolRegistry:
    """Test that all Phase 2 tools are properly registered"""
    
    @pytest_asyncio.fixture
    async def mcp_server(self):
        """Create MCP server instance for testing"""
        server = SimpleMCPServer()
        yield server
        await server.shutdown()
    
    @pytest.mark.asyncio
    async def test_all_phase2_tools_registered(self, mcp_server):
        """Test that all Phase 2 tools are registered in the server"""
        
        expected_tools = [
            # Phase 1 tools
            "establish_connection",
            "list_active_connections", 
            "close_connection",
            # Phase 2 tools
            "list_topics",
            "subscribe_and_collect",
            "publish_message"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in mcp_server.tools, f"Tool {tool_name} not registered"
        
        # Phase 3 Update: We now have 10 tools total (7 functional + 3 placeholder)
        # - 6 Phase 1+2 tools + 1 Phase 3 tool (get_topic_schema) = 7 functional
        # - 3 Phase 4 placeholder tools (debug_device, monitor_performance, test_connection)
        assert len(mcp_server.tools) == 10, f"Expected 10 tools total in Phase 3, got {len(mcp_server.tools)}"
    
    @pytest.mark.asyncio
    async def test_phase2_tools_respond_correctly(self, mcp_server):
        """Test that Phase 2 tools respond correctly to method calls"""
        
        # Define test cases with proper parameters for each tool
        phase2_tools = [
            ("list_topics", {"session_id": "invalid"}),
            ("subscribe_and_collect", {"session_id": "invalid", "topic_pattern": "test/#", "duration_seconds": 10}),
            ("publish_message", {"session_id": "invalid", "topic": "test", "payload": "test"})
        ]
        
        for tool_name, params in phase2_tools:
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
            # Should be an error due to invalid session, but not "not_implemented"
            assert response["result"]["status"] == "error" 