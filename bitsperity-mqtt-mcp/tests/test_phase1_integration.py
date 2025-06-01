"""
Phase 1 Integration Tests für bitsperity-mqtt-mcp
Tests für JSON-RPC 2.0 MCP Server und Session Management
"""

import pytest
import pytest_asyncio
import asyncio
import json
import sys
from io import StringIO
import tempfile
import os

# Import der zu testenden Module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simple_mcp_server import SimpleMCPServer
from mqtt_connection_manager import MQTTConnectionManager
from mqtt_tools import MQTTTools


class TestPhase1MCP:
    """Test Phase 1 MCP Server Functionality"""
    
    @pytest_asyncio.fixture
    async def mcp_server(self):
        """Create MCP server instance for testing"""
        server = SimpleMCPServer()
        yield server
        await server.shutdown()
    
    @pytest.fixture
    def valid_mqtt_connection_string(self):
        """Valid MQTT connection string for testing"""
        return "mqtt://192.168.178.57:1883"
    
    @pytest.fixture
    def invalid_mqtt_connection_string(self):
        """Invalid MQTT connection string for testing"""
        return "http://invalid-protocol:1883"
    
    @pytest.mark.asyncio
    async def test_json_rpc_request_validation(self, mcp_server):
        """Test JSON-RPC 2.0 request validation"""
        
        # Valid JSON-RPC 2.0 request
        valid_request = {
            "jsonrpc": "2.0",
            "method": "establish_connection",
            "params": {"connection_string": "mqtt://192.168.178.57:1883"},
            "id": 1
        }
        
        response = await mcp_server.handle_request(valid_request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response or "error" in response
    
    @pytest.mark.asyncio
    async def test_json_rpc_error_responses(self, mcp_server):
        """Test JSON-RPC 2.0 error response format"""
        
        # Invalid JSON-RPC version
        invalid_request = {
            "jsonrpc": "1.0",
            "method": "establish_connection",
            "id": 1
        }
        
        response = await mcp_server.handle_request(invalid_request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32600
    
    @pytest.mark.asyncio
    async def test_method_not_found_error(self, mcp_server):
        """Test method not found error"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "non_existent_method",
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_establish_connection_tool(self, mcp_server, valid_mqtt_connection_string):
        """Test establish_connection tool"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "establish_connection",
            "params": {"connection_string": valid_mqtt_connection_string},
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        
        result = response["result"]
        assert "session_id" in result
        assert result["broker"] == "192.168.178.57"
        assert result["port"] == 1883
        assert result["tool"] == "establish_connection"
    
    @pytest.mark.asyncio
    async def test_list_active_connections_tool(self, mcp_server):
        """Test list_active_connections tool"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "list_active_connections",
            "params": {},
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        
        result = response["result"]
        assert "active_connections" in result
        assert "total_count" in result
        assert "max_connections" in result
        assert result["tool"] == "list_active_connections"
    
    @pytest.mark.asyncio
    async def test_close_connection_tool(self, mcp_server, valid_mqtt_connection_string):
        """Test close_connection tool"""
        
        # First establish a connection
        establish_request = {
            "jsonrpc": "2.0",
            "method": "establish_connection",
            "params": {"connection_string": valid_mqtt_connection_string},
            "id": 1
        }
        
        establish_response = await mcp_server.handle_request(establish_request)
        session_id = establish_response["result"]["session_id"]
        
        # Then close it
        close_request = {
            "jsonrpc": "2.0",
            "method": "close_connection",
            "params": {"session_id": session_id},
            "id": 2
        }
        
        close_response = await mcp_server.handle_request(close_request)
        
        assert close_response["jsonrpc"] == "2.0"
        assert "result" in close_response
        
        result = close_response["result"]
        assert result["session_id"] == session_id
        assert result["status"] == "closed"
        assert result["tool"] == "close_connection"
    
    @pytest.mark.asyncio
    async def test_invalid_connection_string(self, mcp_server, invalid_mqtt_connection_string):
        """Test error handling for invalid connection string"""
        
        request = {
            "jsonrpc": "2.0",
            "method": "establish_connection",
            "params": {"connection_string": invalid_mqtt_connection_string},
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        
        result = response["result"]
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_session_lifecycle(self, mcp_server, valid_mqtt_connection_string):
        """Test complete session lifecycle"""
        
        # 1. Establish connection
        establish_response = await mcp_server.handle_request({
            "jsonrpc": "2.0",
            "method": "establish_connection",
            "params": {"connection_string": valid_mqtt_connection_string},
            "id": 1
        })
        
        session_id = establish_response["result"]["session_id"]
        
        # 2. List connections (should show 1)
        list_response = await mcp_server.handle_request({
            "jsonrpc": "2.0",
            "method": "list_active_connections",
            "params": {},
            "id": 2
        })
        
        assert list_response["result"]["total_count"] == 1
        
        # 3. Close connection
        close_response = await mcp_server.handle_request({
            "jsonrpc": "2.0",
            "method": "close_connection",
            "params": {"session_id": session_id},
            "id": 3
        })
        
        assert close_response["result"]["status"] == "closed"
        
        # 4. List connections again (should show 0)
        list_response2 = await mcp_server.handle_request({
            "jsonrpc": "2.0",
            "method": "list_active_connections",
            "params": {},
            "id": 4
        })
        
        assert list_response2["result"]["total_count"] == 0


class TestPhase1SessionManagement:
    """Test Session Management und Encryption"""
    
    @pytest_asyncio.fixture
    async def connection_manager(self):
        """Create connection manager for testing"""
        return MQTTConnectionManager(max_connections=3)
    
    @pytest.mark.asyncio
    async def test_session_creation(self, connection_manager):
        """Test session creation and encryption"""
        
        connection_string = "mqtt://user:pass@192.168.178.57:1883/test_client"
        
        result = await connection_manager.establish_connection(connection_string)
        
        assert "session_id" in result
        assert result["broker"] == "192.168.178.57"
        assert result["port"] == 1883
        assert result["status"] == "connected"
        
        # Check session was created
        session = await connection_manager.get_session(result["session_id"])
        assert session is not None
        assert session.parsed_connection["client_id"] == "test_client"
        
        # Check credentials are encrypted
        credentials = session.get_credentials()
        assert credentials["username"] == "user"
        assert credentials["password"] == "pass"
    
    @pytest.mark.asyncio
    async def test_max_connections_limit(self, connection_manager):
        """Test maximum connections limit (3)"""
        
        connection_string = "mqtt://192.168.178.57:1883"
        
        # Create 3 connections (should work)
        sessions = []
        for i in range(3):
            result = await connection_manager.establish_connection(f"{connection_string}/client{i}")
            sessions.append(result["session_id"])
        
        # Try to create 4th connection (should fail)
        with pytest.raises(Exception) as exc_info:
            await connection_manager.establish_connection(f"{connection_string}/client4")
        
        assert "Maximum connections reached" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self, connection_manager):
        """Test session cleanup functionality"""
        
        connection_string = "mqtt://192.168.178.57:1883"
        
        # Create connection
        result = await connection_manager.establish_connection(connection_string)
        session_id = result["session_id"]
        
        # Verify session exists
        connections = connection_manager.list_active_connections()
        assert connections["total_count"] == 1
        
        # Close session
        await connection_manager.close_session(session_id)
        
        # Verify session is gone
        connections = connection_manager.list_active_connections()
        assert connections["total_count"] == 0


class TestPhase1Tools:
    """Test MQTT Tools Implementation"""
    
    @pytest_asyncio.fixture
    async def mqtt_tools(self):
        """Create MQTT tools for testing"""
        connection_manager = MQTTConnectionManager()
        return MQTTTools(connection_manager)
    
    @pytest.mark.asyncio
    async def test_phase2_tools_now_implemented(self, mqtt_tools):
        """Test that Phase 2 tools are now implemented and respond with real functionality"""

        phase2_tools = [
            ("list_topics", {"session_id": "test_session_invalid"}),
            ("subscribe_and_collect", {"session_id": "test_session_invalid", "topic_pattern": "test/#", "duration_seconds": 10}),
            ("publish_message", {"session_id": "test_session_invalid", "topic": "test/topic", "payload": "test"})
        ]

        for tool_name, params in phase2_tools:
            tool_method = getattr(mqtt_tools, tool_name)
            result = await tool_method(**params)

            # Should no longer return "not_implemented" - now returns real errors for invalid session
            assert result["status"] == "error"
            assert result["tool"] == tool_name
            # Should contain session-related error, not "not_implemented"
            assert "Session" in result["error"] or "session_id" in result["error"]
            assert "not_implemented" not in str(result).lower()


@pytest.mark.asyncio
async def test_memory_usage():
    """Test memory usage stays under 128MB (Phase 1 target)"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Create MCP server and simulate usage
    server = SimpleMCPServer()
    
    # Create multiple sessions
    for i in range(5):
        request = {
            "jsonrpc": "2.0",
            "method": "establish_connection",
            "params": {"connection_string": f"mqtt://192.168.178.57:1883/client{i}"},
            "id": i
        }
        await server.handle_request(request)
    
    current_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_used = current_memory - initial_memory
    
    # Cleanup
    await server.shutdown()
    
    # Assert memory usage is reasonable (under 128MB total)
    assert current_memory < 128, f"Memory usage {current_memory:.1f}MB exceeds 128MB limit"
    
    print(f"Memory test: Initial={initial_memory:.1f}MB, Used={memory_used:.1f}MB, Current={current_memory:.1f}MB") 