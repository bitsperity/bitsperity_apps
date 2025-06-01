"""
Phase 3 Tests für bitsperity-mqtt-mcp
Tests für Simple Data Optimization - Message Pruning und Schema Analysis
"""

import pytest
import pytest_asyncio
import asyncio
import sys
import os
import json

# Import der zu testenden Module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simple_mcp_server import SimpleMCPServer
from message_pruner import SimpleMessagePruner, SchemaDetector


class TestPhase3MessagePruning:
    """Test Message Pruning Functionality"""
    
    @pytest.fixture
    def message_pruner(self):
        """Create message pruner for testing"""
        return SimpleMessagePruner(target_count=50)
    
    @pytest.fixture
    def sample_messages(self):
        """Create sample messages for testing"""
        messages = []
        
        # Add normal messages
        for i in range(200):
            messages.append({
                'topic': f'sensor/device{i % 10}/temperature',
                'payload': f'{{"temperature": {20 + i % 10}, "timestamp": "2025-01-23T{i:02d}:00:00Z"}}',
                'qos': 0,
                'retain': False,
                'timestamp': f'2025-01-23T{i:02d}:00:00Z'
            })
        
        # Add error messages (should be preserved)
        for i in range(5):
            messages.append({
                'topic': f'alarm/device{i}/error',
                'payload': f'{{"error": "Critical failure in device {i}", "severity": "critical"}}',
                'qos': 1,
                'retain': False,
                'timestamp': f'2025-01-23T{i + 200:02d}:00:00Z'
            })
        
        # Add warning messages (should be preserved)
        for i in range(3):
            messages.append({
                'topic': f'system/device{i}/warning',
                'payload': f'{{"warning": "Temperature high in device {i}", "level": "warning"}}',
                'qos': 0,
                'retain': False,
                'timestamp': f'2025-01-23T{i + 205:02d}:00:00Z'
            })
        
        return messages
    
    def test_message_pruning_basic(self, message_pruner, sample_messages):
        """Test basic message pruning functionality"""
        
        result = message_pruner.prune_messages(sample_messages, target_count=50)
        
        # Check result structure
        assert 'pruned_messages' in result
        assert 'original_count' in result
        assert 'pruned_count' in result
        assert 'reduction_ratio' in result
        assert 'pruning_stats' in result
        
        # Check counts
        assert result['original_count'] == len(sample_messages)
        assert result['pruned_count'] <= 50
        assert result['pruned_count'] > 0
        
        # Check reduction ratio
        assert 0 < result['reduction_ratio'] < 100
        
        # Check that pruned messages are valid
        for msg in result['pruned_messages']:
            assert 'topic' in msg
            assert 'payload' in msg
            assert 'timestamp' in msg
    
    def test_error_message_preservation(self, message_pruner, sample_messages):
        """Test that error/warning messages are preserved"""
        
        result = message_pruner.prune_messages(sample_messages, target_count=30)
        
        pruned_messages = result['pruned_messages']
        
        # Count error and warning messages in result
        error_count = 0
        warning_count = 0
        
        for msg in pruned_messages:
            topic = msg.get('topic', '')
            payload = msg.get('payload', '')
            
            if 'error' in topic.lower() or 'error' in payload.lower():
                error_count += 1
            elif 'warning' in topic.lower() or 'warning' in payload.lower():
                warning_count += 1
        
        # Should preserve all error messages (5) and warning messages (3)
        assert error_count == 5, f"Expected 5 error messages, got {error_count}"
        assert warning_count == 3, f"Expected 3 warning messages, got {warning_count}"
        
        # Check pruning stats
        stats = result['pruning_stats']
        assert stats['error_messages_preserved'] == 8  # 5 errors + 3 warnings
    
    def test_pruning_with_small_input(self, message_pruner):
        """Test pruning with input smaller than target"""
        
        small_messages = [
            {'topic': 'test', 'payload': 'test1', 'timestamp': '2025-01-23T10:00:00Z'},
            {'topic': 'test', 'payload': 'test2', 'timestamp': '2025-01-23T10:01:00Z'}
        ]
        
        result = message_pruner.prune_messages(small_messages, target_count=50)
        
        # Should return all messages without pruning
        assert result['pruned_count'] == 2
        assert result['original_count'] == 2
        assert result['reduction_ratio'] == 0
        assert result['status'] == 'no_pruning_needed'
    
    def test_pruning_with_empty_input(self, message_pruner):
        """Test pruning with empty input"""
        
        result = message_pruner.prune_messages([], target_count=50)
        
        assert result['pruned_count'] == 0
        assert result['original_count'] == 0
        assert result['status'] == 'empty_input'
        assert result['pruned_messages'] == []


class TestPhase3SchemaDetection:
    """Test Schema Detection Functionality"""
    
    @pytest.fixture
    def schema_detector(self):
        """Create schema detector for testing"""
        return SchemaDetector()
    
    @pytest.fixture
    def mixed_messages(self):
        """Create mixed message types for schema testing"""
        messages = []
        
        # JSON sensor data
        for i in range(10):
            messages.append({
                'topic': f'sensor/temp{i}/data',
                'payload': json.dumps({
                    'temperature': 20 + i,
                    'humidity': 50 + i,
                    'timestamp': '2025-01-23T10:00:00Z'
                }),
                'qos': 0,
                'retain': False,
                'timestamp': '2025-01-23T10:00:00Z'
            })
        
        # Simple text messages
        for i in range(5):
            messages.append({
                'topic': f'device/pump{i}/status',
                'payload': 'ON' if i % 2 == 0 else 'OFF',
                'qos': 0,
                'retain': False,
                'timestamp': '2025-01-23T10:00:00Z'
            })
        
        # Numeric values
        for i in range(5):
            messages.append({
                'topic': f'meter/power{i}/consumption',
                'payload': str(100 + i * 10),
                'qos': 0,
                'retain': False,
                'timestamp': '2025-01-23T10:00:00Z'
            })
        
        # Binary data simulation
        messages.append({
            'topic': 'device/camera1/image',
            'payload': '<binary data: 1024 bytes>',
            'qos': 0,
            'retain': False,
            'timestamp': '2025-01-23T10:00:00Z'
        })
        
        return messages
    
    def test_schema_analysis_basic(self, schema_detector, mixed_messages):
        """Test basic schema analysis functionality"""
        
        result = schema_detector.analyze_messages(mixed_messages)
        
        # Check result structure
        assert 'topic_schemas' in result
        assert 'payload_types' in result
        assert 'common_fields' in result
        assert 'schema_summary' in result
        assert 'status' in result
        
        # Check payload type detection
        payload_types = result['payload_types']
        assert 'json' in payload_types
        assert 'text' in payload_types
        assert 'number' in payload_types
        assert 'binary' in payload_types
        
        # JSON should be dominant (10 out of 21 messages)
        assert payload_types['json'] == 10
        
        # Check schema summary
        summary = result['schema_summary']
        assert summary['total_messages'] == len(mixed_messages)
        assert summary['dominant_payload_type'] == 'json'
    
    def test_topic_pattern_detection(self, schema_detector, mixed_messages):
        """Test topic pattern generalization"""
        
        result = schema_detector.analyze_messages(mixed_messages)
        
        topic_schemas = result['topic_schemas']
        
        # Should detect patterns like sensor/+/data, device/+/status, etc.
        expected_patterns = ['sensor/+/data', 'device/+/status', 'meter/+/consumption']
        
        found_patterns = list(topic_schemas.keys())
        
        # Check that some patterns were detected
        assert len(found_patterns) >= 3
        
        # Check that each pattern has schema info
        for pattern, schema in topic_schemas.items():
            assert 'message_count' in schema
            assert 'payload_types' in schema
            assert schema['message_count'] > 0
    
    def test_json_field_extraction(self, schema_detector):
        """Test JSON field extraction"""
        
        json_messages = [
            {
                'topic': 'sensor/data',
                'payload': json.dumps({'temperature': 25, 'humidity': 60, 'location': 'room1'}),
                'timestamp': '2025-01-23T10:00:00Z'
            },
            {
                'topic': 'sensor/data',
                'payload': json.dumps({'temperature': 26, 'humidity': 65, 'location': 'room2'}),
                'timestamp': '2025-01-23T10:01:00Z'
            }
        ]
        
        result = schema_detector.analyze_messages(json_messages)
        
        # Check common fields detection
        common_fields = result['common_fields']
        
        # Should detect temperature, humidity, location fields
        assert 'temperature' in common_fields
        assert 'humidity' in common_fields
        assert 'location' in common_fields
        
        # Each field should appear 2 times
        assert common_fields['temperature'] == 2
        assert common_fields['humidity'] == 2
        assert common_fields['location'] == 2
    
    def test_schema_with_empty_input(self, schema_detector):
        """Test schema analysis with empty input"""
        
        result = schema_detector.analyze_messages([])
        
        assert result['status'] == 'empty_input'
        assert result['topic_schemas'] == {}
        assert result['payload_types'] == {}
        assert result['common_fields'] == {}


class TestPhase3ToolIntegration:
    """Test Phase 3 Tool Integration"""
    
    @pytest_asyncio.fixture
    async def mcp_server(self):
        """Create MCP server instance for testing"""
        server = SimpleMCPServer()
        yield server
        await server.shutdown()
    
    @pytest.mark.asyncio
    async def test_get_topic_schema_tool_registered(self, mcp_server):
        """Test that get_topic_schema tool is registered"""
        
        assert 'get_topic_schema' in mcp_server.tools
        
        # Test invalid session (should respond with error, not method not found)
        request = {
            "jsonrpc": "2.0",
            "method": "get_topic_schema",
            "params": {
                "session_id": "invalid",
                "topic_pattern": "test/#"
            },
            "id": 1
        }
        
        response = await mcp_server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert response["result"]["tool"] == "get_topic_schema"
        assert response["result"]["status"] == "error"
    
    @pytest.mark.asyncio
    async def test_server_has_seven_tools(self, mcp_server):
        """Test that server now has 7 tools (including get_topic_schema)"""
        
        expected_tools = [
            # Phase 1
            "establish_connection",
            "list_active_connections", 
            "close_connection",
            # Phase 2
            "list_topics",
            "subscribe_and_collect",
            "publish_message",
            # Phase 3
            "get_topic_schema"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in mcp_server.tools
        
        # Should have exactly 7 functional tools (plus 3 placeholder Phase 4 tools)
        assert len(mcp_server.tools) == 10  # 7 functional + 3 placeholder


class TestPhase3Performance:
    """Test Phase 3 Performance Improvements"""
    
    def test_pruning_performance(self):
        """Test that message pruning is fast"""
        import time
        
        # Create large message collection
        large_messages = []
        for i in range(1000):
            large_messages.append({
                'topic': f'sensor/device{i % 100}/data',
                'payload': f'{{"value": {i}, "timestamp": "2025-01-23T10:00:00Z"}}',
                'qos': 0,
                'retain': False,
                'timestamp': '2025-01-23T10:00:00Z'
            })
        
        pruner = SimpleMessagePruner(target_count=50)
        
        start_time = time.time()
        result = pruner.prune_messages(large_messages, target_count=50)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should process 1000 messages in under 1 second
        assert processing_time < 1.0, f"Pruning took {processing_time:.3f}s, expected <1.0s"
        
        # Should produce exactly 50 messages
        assert result['pruned_count'] == 50
        
        # Check processing time is reported
        assert 'processing_time_seconds' in result
        assert result['processing_time_seconds'] > 0
    
    def test_schema_analysis_performance(self):
        """Test that schema analysis is reasonably fast"""
        import time
        
        # Create diverse message collection
        diverse_messages = []
        for i in range(200):
            diverse_messages.append({
                'topic': f'sensor/type{i % 10}/data{i % 5}',
                'payload': json.dumps({
                    'value': i,
                    'type': f'sensor_type_{i % 10}',
                    'location': f'zone_{i % 5}',
                    'timestamp': '2025-01-23T10:00:00Z'
                }),
                'qos': 0,
                'retain': False,
                'timestamp': '2025-01-23T10:00:00Z'
            })
        
        detector = SchemaDetector()
        
        start_time = time.time()
        result = detector.analyze_messages(diverse_messages)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should analyze 200 messages in under 2 seconds
        assert processing_time < 2.0, f"Schema analysis took {processing_time:.3f}s, expected <2.0s"
        
        # Should detect multiple topic patterns
        assert len(result['topic_schemas']) > 1
        
        # Check processing time is reported
        assert 'processing_time_seconds' in result
        assert result['processing_time_seconds'] > 0 