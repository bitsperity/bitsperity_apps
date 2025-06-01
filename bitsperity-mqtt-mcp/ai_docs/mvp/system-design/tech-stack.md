# bitsperity-mqtt-mcp - Technology Stack

## Core Technology Stack

### Programming Language
- **Python 3.11+**
  - **Rationale**: Consistent with MongoDB MCP, excellent async support, rich MQTT ecosystem
  - **Benefits**: Type hints, performance improvements, asyncio maturity
  - **Libraries**: Strong ecosystem for MQTT (aiomqtt, paho-mqtt)

### MQTT Client Library
- **aiomqtt** (Primary Choice)
  - **Rationale**: Full async/await support, built on paho-mqtt, modern API
  - **Benefits**: Non-blocking operations, perfect for real-time collection
  - **Version**: Latest stable (2.x)
  - **QoS Support**: Full QoS 0, 1, 2 implementation
  - **Fallback**: paho-mqtt for specific edge cases

### MCP Protocol
- **JSON-RPC 2.0 over STDIO**
  - **Rationale**: MCP standard, same as MongoDB MCP
  - **Communication**: SSH + Docker exec integration
  - **Benefits**: Secure, standardized, AI assistant compatible

### Web Interface
- **FastAPI**
  - **Rationale**: Lightweight, async-native, excellent for monitoring APIs
  - **Benefits**: Auto-generated docs, type validation, minimal overhead
  - **Alternative Considered**: Flask (rejected - not async-native)

### Serialization & Validation
- **Pydantic v2**
  - **Rationale**: Type validation, JSON serialization, error handling
  - **Benefits**: Runtime type checking, clear error messages
  - **Usage**: Message models, tool parameter validation

### Security
- **cryptography (Fernet)**
  - **Rationale**: Same as MongoDB MCP, symmetric encryption for credentials
  - **Benefits**: Secure in-memory credential storage
  - **Scope**: Connection string encryption only

### Containerization
- **Docker with multi-stage builds**
  - **Base Image**: python:3.11-slim
  - **Benefits**: Minimal size, security, consistency
  - **Build Strategy**: Multi-stage for smaller production images

## Development Dependencies

### Testing Framework
- **pytest + pytest-asyncio**
  - **Rationale**: Industry standard, excellent async support
  - **Coverage**: pytest-cov for coverage reporting
  - **Mocking**: unittest.mock for MQTT client mocking

### Code Quality
- **black** (Code formatting)
- **ruff** (Linting and import sorting)
- **mypy** (Type checking)
- **pre-commit** (Git hooks for quality gates)

### Development Tools
- **uvicorn** (ASGI server for FastAPI development)
- **python-dotenv** (Environment variable management)

## Library Versions & Dependencies

### Production Dependencies (requirements.txt)
```txt
# MQTT Client
aiomqtt==2.0.1
paho-mqtt==1.6.1

# Web Framework  
fastapi==0.104.1
uvicorn==0.24.0

# Data Validation
pydantic==2.5.0

# Security
cryptography==41.0.8

# Utilities
python-dotenv==1.0.0
```

### Development Dependencies (requirements-dev.txt)
```txt
# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Code Quality
black==23.11.0
ruff==0.1.6
mypy==1.7.1
pre-commit==3.5.0

# Development Server
uvicorn[standard]==0.24.0
```

## Architecture Decisions Records (ADRs)

### ADR-001: MQTT Library Selection (aiomqtt vs paho-mqtt)

**Decision**: Use aiomqtt as primary MQTT client library

**Context**: Need async MQTT client for non-blocking message collection

**Options Considered**:
1. **aiomqtt**: Modern async wrapper around paho-mqtt
2. **paho-mqtt**: Standard MQTT library with blocking operations
3. **hbmqtt**: Pure async MQTT but less mature

**Decision Factors**:
- ✅ aiomqtt: Full async/await support, built on proven paho-mqtt
- ✅ Non-blocking message collection essential for time-bounded operations
- ✅ Active maintenance and modern Python practices
- ❌ paho-mqtt: Blocking operations would require thread management
- ❌ hbmqtt: Less mature, smaller community

**Consequences**:
- Real-time message collection without blocking
- Clean async/await code throughout
- Dependency on aiomqtt maintenance
- Slightly more complex error handling

### ADR-002: Session Management Approach

**Decision**: In-memory session store with encryption

**Context**: Need secure, fast session management for MQTT connections

**Options Considered**:
1. **In-memory with encryption** (chosen)
2. **External session store** (Redis, database)
3. **Stateless with token validation**

**Decision Factors**:
- ✅ In-memory: Fast access, automatic cleanup on restart
- ✅ Encryption: Secure credential storage
- ✅ Simplicity: No external dependencies
- ❌ External store: Adds complexity, network overhead
- ❌ Stateless: Complex token management

**Consequences**:
- Fast session access
- Automatic cleanup on container restart
- Sessions lost on restart (acceptable for development tool)
- Memory usage scales with session count

### ADR-003: Message Collection Strategy

**Decision**: Time-bounded collection with intelligent pruning

**Context**: Need to handle high-volume MQTT streams for AI processing

**Options Considered**:
1. **Time-bounded with pruning** (chosen)
2. **Fixed message count only**
3. **Streaming with real-time analysis**

**Decision Factors**:
- ✅ Time-bounded: Predictable operation duration
- ✅ Pruning: Optimized for AI context limits
- ✅ Stop conditions: Either time OR message limit
- ❌ Fixed count: Unpredictable duration
- ❌ Streaming: Complex for AI integration

**Consequences**:
- Predictable tool execution time
- Optimized AI assistant processing
- Complex pruning algorithm needed
- Potential data loss in high-volume scenarios

### ADR-004: Web Interface Technology

**Decision**: FastAPI for monitoring interface

**Context**: Need lightweight web interface for status monitoring

**Options Considered**:
1. **FastAPI** (chosen)
2. **Flask with async extensions**
3. **Simple HTTP server**

**Decision Factors**:
- ✅ FastAPI: Async-native, auto-docs, type validation
- ✅ Lightweight: Minimal resource usage
- ✅ Modern: Pydantic integration, OpenAPI support
- ❌ Flask: Async bolt-on, more complex
- ❌ Simple HTTP: No validation, manual routing

**Consequences**:
- Consistent async architecture
- Auto-generated API documentation
- Type-safe request/response handling
- Additional dependency for monitoring

### ADR-005: Error Handling Strategy

**Decision**: Hierarchical error classes with recovery

**Context**: Need consistent error handling across MQTT operations

**Error Hierarchy**:
```python
MQTTMCPError (base)
├── ConnectionError
│   ├── BrokerUnreachableError  
│   ├── AuthenticationError
│   └── TimeoutError
├── SessionError
│   ├── SessionExpiredError
│   └── ResourceLimitError
└── OperationError
    ├── TopicValidationError
    ├── PayloadSizeError
    └── QoSNotSupportedError
```

**Recovery Strategies**:
- **ConnectionError**: Auto-reconnect with exponential backoff
- **SessionError**: Clear session, require re-establishment
- **OperationError**: Immediate failure with clear message

## Performance Targets

### Response Time
- **Connection establishment**: <30 seconds
- **Message collection start**: <2 seconds  
- **Topic discovery**: <60 seconds (for 1000 topics)
- **Tool execution overhead**: <100ms

### Resource Usage
- **Memory per session**: <50MB
- **Total memory limit**: <256MB
- **CPU usage**: <0.5 cores under normal load
- **Network bandwidth**: Depends on MQTT traffic

### Scalability Limits
- **Concurrent sessions**: 5 (configurable)
- **Messages per collection**: 500 maximum
- **Topic discovery limit**: 1000 topics
- **Session duration**: 1 hour TTL

## Security Considerations

### Credential Security
- **Encryption**: Fernet symmetric encryption for connection strings
- **Storage**: Memory-only, no disk persistence
- **Isolation**: Session-based credential isolation
- **Cleanup**: Automatic cleanup on session expiration

### Network Security
- **MQTT**: Plain TCP (TLS to be added in future)
- **Docker**: Network isolation between containers
- **SSH**: Secure communication for MCP protocol
- **No Internet**: Local network operation only

### Input Validation
- **Connection strings**: URL parsing and validation
- **Topic names**: MQTT specification compliance
- **Payload size**: Hard limits to prevent DoS
- **Parameters**: Pydantic validation for all inputs

## Deployment Strategy

### Container Strategy
```dockerfile
# Multi-stage build for minimal production image
FROM python:3.11-slim as builder
# Build dependencies
FROM python:3.11-slim as runtime  
# Runtime dependencies only
```

### Environment Configuration
```python
# Environment-aware configuration
DEVELOPMENT = {
    'mqtt_broker': '192.168.178.57:1883',
    'log_level': 'DEBUG',
    'web_monitor': True
}

PRODUCTION = {
    'mqtt_broker': 'mosquitto_broker_1:1883', 
    'log_level': 'INFO',
    'web_monitor': True
}
```

### Resource Limits
```yaml
# Docker Compose resource limits
deploy:
  resources:
    limits:
      memory: 256M
      cpus: '0.5'
    reservations:
      memory: 128M  
      cpus: '0.25'
```

## Future Technology Considerations

### Potential Upgrades
- **MQTT 5.0**: Enhanced features, topic aliases, shared subscriptions
- **TLS Support**: Encrypted MQTT communications
- **Message Persistence**: Optional Redis backend for session persistence
- **Metrics**: Prometheus metrics for production monitoring

### Compatibility
- **Python**: Forward compatible with Python 3.12+
- **MQTT**: Compatible with MQTT 3.1.1 and 5.0 brokers
- **MCP**: Compatible with current MCP protocol specification
- **Umbrel**: Compatible with Umbrel app standards 