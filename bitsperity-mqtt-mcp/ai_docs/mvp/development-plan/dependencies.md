# bitsperity-mqtt-mcp - Technical Dependencies

## Component Dependencies Map

```mermaid
graph TD
    subgraph "Phase 1: Foundation Components"
        A[SimpleMCPServer] --> B[JSON-RPC 2.0 Handler]
        A --> C[Tool Registry]
        A --> D[Error Handler]
        
        E[MQTTConnectionManager] --> F[Session Store]
        E --> G[Fernet Encryption]
        E --> H[Connection Pool]
        
        I[MQTTTools] --> J[Tool Implementations]
        I --> K[Parameter Validation]
    end
    
    subgraph "Phase 2: MQTT Core Components"
        L[aiomqtt Client] --> M[Async Connection]
        L --> N[QoS Support]
        L --> O[Reconnection Logic]
        
        P[MessageCollector] --> Q[Time-bounded Collection]
        P --> R[Topic Wildcards]
        P --> S[Message Queuing]
        
        T[Connection String Parser] --> U[URL Parsing]
        T --> V[Credential Extraction]
    end
    
    subgraph "Phase 3: AI Optimization Components"
        W[MessagePruner] --> X[Priority Algorithm]
        W --> Y[Temporal Sampling]
        W --> Z[Diversity Selection]
        
        AA[SchemaAnalyzer] --> BB[JSON Schema Generation]
        AA --> CC[Format Detection]
        AA --> DD[Pattern Analysis]
        
        EE[WebMonitor] --> FF[FastAPI Server]
        EE --> GG[Status Endpoints]
        EE --> HH[Session Statistics]
    end
    
    subgraph "Phase 4: Production Components"
        II[Advanced Tools] --> JJ[Device Debugging]
        II --> KK[Performance Monitoring]
        II --> LL[Health Checks]
        
        MM[Docker Integration] --> NN[Multi-stage Build]
        MM --> OO[Container Optimization]
        
        PP[Umbrel Integration] --> QQ[Service Registration]
        PP --> RR[Network Configuration]
    end
    
    %% Cross-phase dependencies
    A --> E
    E --> I
    I --> L
    L --> P
    P --> W
    W --> AA
    AA --> EE
    EE --> II
    II --> MM
    MM --> PP
```

## Library Dependencies

### Core Dependencies (Phase 1)
```python
# requirements.txt - Phase 1
asyncio>=3.11.0          # Built-in async support
cryptography>=41.0.8     # Fernet encryption for credentials
uuid>=0.0.0              # Built-in session ID generation
json>=0.0.0              # Built-in JSON-RPC 2.0 support
logging>=0.0.0           # Built-in logging framework
```

### MQTT Dependencies (Phase 2)
```python
# requirements.txt - Phase 2
aiomqtt>=2.0.1           # Async MQTT client (depends on paho-mqtt)
paho-mqtt>=1.6.1         # MQTT protocol implementation (aiomqtt dependency)
urllib.parse>=0.0.0      # Built-in URL parsing for connection strings
```

### AI Optimization Dependencies (Phase 3)
```python
# requirements.txt - Phase 3
fastapi>=0.104.1         # Web monitoring interface
uvicorn>=0.24.0          # ASGI server for FastAPI
pydantic>=2.5.0          # Data validation for API responses
json-schema>=4.0.0       # JSON schema generation (may use jsonschema library)
```

### Development Dependencies (All Phases)
```python
# requirements-dev.txt
pytest>=7.4.3           # Testing framework
pytest-asyncio>=0.21.1  # Async testing support
pytest-cov>=4.1.0       # Coverage reporting
black>=23.11.0           # Code formatting
ruff>=0.1.6             # Linting and import sorting
mypy>=1.7.1             # Type checking
pre-commit>=3.5.0       # Git hooks for quality gates
```

## External Service Dependencies

### Development Environment
```mermaid
graph LR
    subgraph "Local Development"
        A[Developer Machine] --> B[Python 3.11+]
        A --> C[Docker Desktop]
        A --> D[Git]
        
        E[Test MQTT Broker] --> F[192.168.178.57:1883]
        G[Test SSH Access] --> H[umbrel@umbrel.local]
    end
    
    subgraph "Development Services"
        I[External MQTT] --> J[mosquitto broker]
        K[SSH Target] --> L[Umbrel Host]
        M[Docker Registry] --> N[bitsperity/mqtt-mcp]
    end
    
    A --> E
    A --> G
    E --> I
    G --> K
    C --> M
```

### Production Environment
```mermaid
graph TD
    subgraph "Umbrel Environment"
        A[Umbrel Host] --> B[Docker Engine]
        B --> C[Container Networks]
        
        D[bitsperity-mqtt-mcp] --> E[MCP Server Container]
        D --> F[Web Monitor Container]
        
        G[External Dependencies] --> H[mosquitto_broker_1]
        G --> I[SSH Access via Host Network]
    end
    
    subgraph "Network Dependencies"
        J[mosquitto_default] --> K[MQTT Broker Access]
        L[host network] --> M[SSH Integration]
        N[bridge network] --> O[Web Interface Port 8090]
    end
    
    E --> H
    E --> I
    F --> O
```

## Phase Implementation Dependencies

### Phase 1 → Phase 2 Handoff
```mermaid
sequenceDiagram
    participant P1 as Phase 1
    participant Test as Testing
    participant P2 as Phase 2
    
    P1->>Test: SimpleMCPServer functional
    Test->>Test: Validate JSON-RPC 2.0 compliance
    Test->>Test: Validate session management
    Test->>Test: Validate SSH integration
    
    Test->>P2: Foundation components ready ✅
    P2->>P2: Build aiomqtt integration
    P2->>P2: Implement MQTT tools
    
    Note over P1,P2: Requirement: Basic MCP server must handle tool registration
    Note over P1,P2: Requirement: Session management must support MQTT clients
```

### Phase 2 → Phase 3 Handoff
```mermaid
sequenceDiagram
    participant P2 as Phase 2
    participant Test as Testing
    participant P3 as Phase 3
    
    P2->>Test: MQTT tools functional
    Test->>Test: Validate broker connection
    Test->>Test: Validate message collection
    Test->>Test: Validate topic discovery
    
    Test->>P3: MQTT operations ready ✅
    P3->>P3: Implement message pruning
    P3->>P3: Add schema analysis
    P3->>P3: Build web monitoring
    
    Note over P2,P3: Requirement: Message collection must provide raw data
    Note over P2,P3: Requirement: MQTT client must be accessible for analysis
```

### Phase 3 → Phase 4 Handoff
```mermaid
sequenceDiagram
    participant P3 as Phase 3
    participant Test as Testing
    participant P4 as Phase 4
    
    P3->>Test: AI optimization functional
    Test->>Test: Validate message pruning
    Test->>Test: Validate schema analysis
    Test->>Test: Validate web interface
    
    Test->>P4: Core features ready ✅
    P4->>P4: Implement advanced tools
    P4->>P4: Create production deployment
    P4->>P4: Complete testing suite
    
    Note over P3,P4: Requirement: All core tools must be performance-optimized
    Note over P3,P4: Requirement: Web interface must be production-ready
```

## Critical Path Analysis

```mermaid
graph TD
    A[Project Start] --> B[Python Environment Setup]
    B --> C[MCP Protocol Implementation]
    C --> D[Session Management]
    D --> E[MQTT Integration] 
    E --> F[Core Tool Implementation]
    F --> G[Message Collection]
    G --> H[AI Optimization]
    H --> I[Production Deployment]
    I --> J[Project Complete]
    
    %% Critical path highlighted
    style A fill:#ff9999
    style C fill:#ff9999
    style E fill:#ff9999
    style G fill:#ff9999
    style I fill:#ff9999
    style J fill:#ff9999
    
    %% Parallel tracks
    K[Error Handling] --> F
    L[Web Interface] --> H
    M[Docker Setup] --> I
    N[Testing Suite] --> I
    
    style K fill:#99ccff
    style L fill:#99ccff
    style M fill:#99ccff
    style N fill:#99ccff
```

## Dependency Risk Assessment

### High Risk Dependencies
```mermaid
graph LR
    subgraph "High Risk"
        A[aiomqtt Library] --> A1[Version Compatibility]
        A --> A2[Async Performance]
        A --> A3[MQTT Broker Support]
        
        B[SSH Integration] --> B1[Docker exec Stability]
        B --> B2[Network Configuration]
        B --> B3[Authentication Issues]
        
        C[Umbrel Platform] --> C1[App Store Requirements]
        C --> C2[Container Networking]
        C --> C3[Service Discovery]
    end
    
    subgraph "Mitigation Strategies"
        A1 --> D[Pin exact versions]
        A2 --> E[Performance testing]
        A3 --> F[Broker compatibility matrix]
        
        B1 --> G[Test early and often]
        B2 --> H[Network debugging tools]
        B3 --> I[Fallback auth methods]
        
        C1 --> J[Follow Umbrel standards]
        C2 --> K[Docker compose validation]
        C3 --> L[Service registration testing]
    end
```

### Medium Risk Dependencies
```mermaid
quadrantChart
    title Dependency Risk Assessment
    x-axis Low Impact --> High Impact
    y-axis Low Risk --> High Risk
    
    Python 3.11: [0.2, 0.1]
    asyncio: [0.3, 0.1]
    cryptography: [0.5, 0.2]
    aiomqtt: [0.9, 0.7]
    FastAPI: [0.4, 0.2]
    Docker: [0.7, 0.3]
    SSH Integration: [0.9, 0.6]
    Umbrel Platform: [0.8, 0.5]
```

## Integration Testing Dependencies

### Component Integration Tests
```python
# Test dependency matrix
class TestMatrix:
    """
    Test dependencies between components
    """
    
    def test_mcp_server_with_connection_manager():
        """Phase 1: MCP Server → Connection Manager integration"""
        pass
    
    def test_connection_manager_with_mqtt_client():
        """Phase 2: Connection Manager → MQTT Client integration"""
        pass
    
    def test_mqtt_tools_with_message_collector():
        """Phase 2: MQTT Tools → Message Collector integration"""
        pass
    
    def test_message_collector_with_pruner():
        """Phase 3: Message Collector → Pruner integration"""
        pass
    
    def test_pruner_with_schema_analyzer():
        """Phase 3: Pruner → Schema Analyzer integration"""
        pass
    
    def test_web_monitor_with_mcp_server():
        """Phase 3: Web Monitor → MCP Server integration"""
        pass
```

### End-to-End Testing Flow
```mermaid
stateDiagram-v2
    [*] --> Setup
    Setup --> MCPConnection : Start MCP Server
    MCPConnection --> MQTTBroker : Establish MQTT Connection
    MQTTBroker --> TopicDiscovery : Discover Topics
    TopicDiscovery --> MessageCollection : Collect Messages
    MessageCollection --> MessagePruning : Apply AI Optimization
    MessagePruning --> SchemaAnalysis : Analyze Structure
    SchemaAnalysis --> WebMonitoring : Display Status
    WebMonitoring --> Cleanup : Test Complete
    Cleanup --> [*]
    
    MCPConnection --> [*] : Connection Failed
    MQTTBroker --> [*] : Broker Unreachable
    TopicDiscovery --> [*] : No Topics Found
    MessageCollection --> [*] : Collection Timeout
    MessagePruning --> [*] : Pruning Failed
    SchemaAnalysis --> [*] : Analysis Error
    WebMonitoring --> [*] : Monitoring Error
```

## Deployment Dependencies

### Docker Build Dependencies
```dockerfile
# Multi-stage build dependency chain
FROM python:3.11-slim as base
# System dependencies: curl, basic tools

FROM base as dependencies
# Python dependencies: aiomqtt, fastapi, cryptography

FROM dependencies as testing
# Test dependencies: pytest, coverage tools

FROM dependencies as production
# Production code only, minimal dependencies
```

### Umbrel Deployment Dependencies
```yaml
# docker-compose.yml dependency chain
services:
  mcp-server:
    depends_on:
      - mosquitto_broker_1    # MQTT broker must be running
    networks:
      - mosquitto_default     # Access to MQTT network
      - host                  # SSH access for AI Assistant
    
  web:
    depends_on:
      - mcp-server           # Web interface depends on MCP server
    networks:
      - bridge               # Isolated web network
```

## Dependency Management Strategy

### Version Pinning Strategy
```python
# Exact version pinning for critical dependencies
aiomqtt==2.0.1          # EXACT: MQTT functionality critical
cryptography==41.0.8    # EXACT: Security critical
fastapi>=0.104.1,<0.105 # COMPATIBLE: Feature stable
pytest>=7.4.0          # MINIMUM: Testing framework flexible
```

### Dependency Update Policy
1. **Phase 1-2**: Pin all versions exactly (stability focus)
2. **Phase 3**: Allow compatible updates for non-critical libraries
3. **Phase 4**: Comprehensive dependency audit and update
4. **Production**: Lock all versions, security updates only

### Backup Plans
- **aiomqtt fails**: Fallback to direct paho-mqtt with threading
- **FastAPI issues**: Use simple HTTP server for web interface
- **Encryption problems**: Use environment variables for development
- **SSH integration breaks**: Add direct TCP fallback for debugging 