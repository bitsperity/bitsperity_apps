# bitsperity-mqtt-mcp - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Umbrel Environment                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Cursor IDE     │  │ MQTT MCP Server │  │ Umbrel Services │  │ IoT Devices │ │
│  │  (AI Assistant) │  │   (Python)      │  │                 │  │             │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • Natural Lang  │◄─┤ • MCP Protocol  │◄─┤ • MQTT Broker   │◄─┤ • Sensors   │ │
│  │ • SSH Commands  │  │ • Session Mgmt  │  │ • Mosquitto     │  │ • Actuators │ │
│  │ • JSON-RPC 2.0  │  │ • Topic Monitor │  │ • Message Queue │  │ • Controllers│ │
│  │ • AI Processing │  │ • Message Coll. │  │ • Port 1883     │  │ • Devices   │ │
│  │                 │  │ • Web Interface │  │                 │  │             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                 │                                               │
│  ┌─────────────────────────────┘                                               │
│  │                                                                             │
│  ▼                                                                             │
│  ┌─────────────────┐                                                          │
│  │ Web Monitor     │                                                          │
│  │ (Port 8090)     │                                                          │
│  ├─────────────────┤                                                          │
│  │ • Live Status   │                                                          │
│  │ • Session Info  │                                                          │
│  │ • Message Stats │                                                          │
│  │ • Debug Logs    │                                                          │
│  └─────────────────┘                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. MCP Server (Core)
- **Technology**: Python 3.11+ with asyncio
- **Protocol**: JSON-RPC 2.0 over STDIO
- **Communication**: SSH + Docker exec (same as MongoDB MCP)
- **Session Management**: UUID-based, 1h TTL, max 5 concurrent
- **MQTT Library**: `aiomqtt` for full async support

### 2. MQTT Tools (10 Core Tools)
```python
# MVP Tools (Phase 1)
establish_connection()     # MQTT Broker connection
list_topics()             # Topic discovery with wildcards  
subscribe_and_collect()   # Time-bounded message collection
publish_message()         # Message publishing with QoS
list_active_connections() # Session management
close_connection()        # Session cleanup

# Advanced Tools (Phase 2)
get_topic_schema()        # Message structure analysis
debug_device()            # Device-specific monitoring
monitor_performance()     # Throughput & latency metrics
test_connection()         # Health check
```

### 3. Connection Manager
- **Session Isolation**: Unique UUID per MQTT connection
- **Security**: No credential persistence, memory-only storage
- **Resource Limits**: Max 5 concurrent MQTT connections
- **Auto-cleanup**: Expired session removal every 60s
- **Reconnection**: 3 retries with exponential backoff

### 4. Message Collector
- **Time-bounded**: 10-300 seconds configurable duration
- **Volume-limited**: Max 500 messages per collection
- **Intelligent Pruning**: Reduce to 50 messages for AI processing
- **QoS Support**: Full MQTT QoS 0, 1, 2 handling
- **Real-time**: Async message collection with stop conditions

### 5. Web Monitor Interface
- **Technology**: Python FastAPI (lightweight)
- **Port**: 8090 (consistent with MongoDB MCP)
- **Features**: Session status, message statistics, live logs
- **API**: REST endpoints for MCP server communication

## Data Flow Architecture

### 1. AI Assistant → MCP Server
```
Cursor IDE
  ↓ SSH Command
ssh umbrel@umbrel.local "docker exec -i bitsperity-mqtt-mcp_mcp-server_1 python src/simple_mcp_server.py"
  ↓ JSON-RPC 2.0 over STDIN
MCP Server (Python)
  ↓ Tool Execution
MQTT Client (aiomqtt)
  ↓ MQTT Protocol
IoT Broker (Mosquitto)
  ↓ Pub/Sub
IoT Devices
```

### 2. Message Collection Flow
```
Input: session_id, topic_pattern, duration=30s, max_messages=100

1. Validate Session → Connection Manager
2. Subscribe to Topic → MQTT Client  
3. Start Collector → Message Collector (async)
4. Collect Messages → Real-time queue
5. Apply Stop Conditions → Time OR Message Limit
6. Intelligent Pruning → 50 messages for AI
7. Unsubscribe → Clean disconnect
8. Return Results → JSON to AI Assistant
```

### 3. Topic Discovery Flow
```
Input: session_id, pattern="#", duration=30s

1. Subscribe to Wildcard → MQTT Client
2. Collect Topic Names → Set (deduplication)
3. Track Timestamps → First/Last seen
4. Apply Limits → Max 1000 topics
5. Sort Results → Alphabetical order
6. Return Topic List → With metadata
```

## Integration Architecture

### 1. Umbrel Service Dependencies
```yaml
# docker-compose.yml dependencies
services:
  mcp-server:
    depends_on:
      - mosquitto_broker_1  # MQTT Broker service
    networks:
      - mosquitto_default   # Access to MQTT broker
    environment:
      MQTT_BROKER_URL: mosquitto_broker_1:1883  # Internal network
```

### 2. Development vs Production
```python
# Environment-aware MQTT broker configuration
config = {
    'mqtt_broker': {
        'development': {
            'host': '192.168.178.57',     # External access for testing
            'port': 1883,
            'debug': True
        },
        'production': {
            'host': 'mosquitto_broker_1', # Container network
            'port': 1883,
            'debug': False
        }
    }
}
```

### 3. Security & Isolation
- **Network Isolation**: Docker networks for service communication
- **Session Security**: No persistent credential storage
- **Data Privacy**: Memory-only message data, cleared on session end
- **Access Control**: Session validation for all operations

## Performance Architecture

### 1. Async Processing
- **MQTT Client**: Full async/await with aiomqtt
- **Message Collection**: Non-blocking queue processing
- **Session Management**: Async cleanup tasks
- **Web Interface**: FastAPI async endpoints

### 2. Memory Management
- **Message Limits**: Hard caps to prevent memory exhaustion
- **Intelligent Pruning**: Preserve important messages, sample others
- **Session Cleanup**: Automatic resource deallocation
- **Connection Pooling**: Efficient MQTT client reuse

### 3. Scalability Targets
- **Concurrent Sessions**: 5 MQTT connections
- **Message Throughput**: 100 messages/second
- **Topic Discovery**: 1000 topics maximum
- **Response Time**: <2s for message collection start
- **Memory Usage**: <256MB per session

## Error Handling Architecture

### 1. Connection Errors
- **Broker Unreachable**: Clear error with broker details
- **Authentication Failed**: Generic auth error (no credential exposure)
- **Timeout**: Graceful timeout with attempted duration
- **Network Issues**: Auto-reconnection with exponential backoff

### 2. Runtime Errors
- **Session Expired**: Clear session error, require new connection
- **Topic Invalid**: MQTT spec violation error
- **Payload Too Large**: Size limit error with current limit
- **QoS Not Supported**: Broker capability error

### 3. Recovery Strategies
- **Connection Lost**: 3 retries, exponential backoff (1s, 2s, 4s)
- **Subscription Failed**: Log error, continue with other subscriptions
- **Memory Pressure**: Trigger early pruning, reduce targets
- **Partial Results**: Return collected data on timeout

## Deployment Architecture

### 1. Docker Container Structure
```dockerfile
FROM python:3.11-slim
# Multi-stage build for minimal image size
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
CMD ["python", "src/simple_mcp_server.py"]
```

### 2. Umbrel App Integration
```yaml
# umbrel-app.yml
manifestVersion: 1
id: bitsperity-mqtt-mcp  
category: developer-tools
name: MQTT MCP Server
port: 8090
dependencies: []
```

### 3. Network Configuration
- **MCP Server**: Host network mode for SSH access
- **Web Interface**: Bridge network with port mapping 8090:8080
- **MQTT Client**: Access to mosquitto network for broker communication 