# bitsperity-mqtt-mcp - Development Phases

## Projekt Overview
- **App Name**: bitsperity-mqtt-mcp
- **Purpose**: MQTT Model Context Protocol Server für AI-gestützte IoT Device Analysis
- **Target Platform**: Umbrel App Store
- **Development Duration**: 4 Phasen (4-5 Wochen total)

## Development Timeline

```mermaid
gantt
    title MQTT MCP Development Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1: MCP Foundation
    Project Setup          :p1-1, 2024-01-15, 2d
    Python Environment     :p1-2, after p1-1, 1d
    Basic MCP Server       :p1-3, after p1-2, 3d
    Connection Management  :p1-4, after p1-3, 2d
    
    section Phase 2: MQTT Core Tools
    MQTT Connection Tool   :p2-1, after p1-4, 2d
    Topic Discovery        :p2-2, after p2-1, 2d
    Message Collection     :p2-3, after p2-2, 3d
    Message Publishing     :p2-4, after p2-3, 2d
    
    section Phase 3: AI Optimization
    Message Pruning        :p3-1, after p2-4, 3d
    Schema Analysis        :p3-2, after p3-1, 2d
    Web Monitor Interface  :p3-3, after p3-2, 2d
    
    section Phase 4: Production Ready
    Advanced Tools         :p4-1, after p3-3, 3d
    Docker Integration     :p4-2, after p4-1, 2d
    Umbrel Deployment      :p4-3, after p4-2, 2d
    Testing & Documentation :p4-4, after p4-3, 2d
```

## Phase Dependencies

```mermaid
graph TD
    subgraph "Phase 1: MCP Foundation"
        A[Project Setup] --> B[Python Environment]
        B --> C[Basic MCP Server]
        C --> D[Connection Management]
    end
    
    subgraph "Phase 2: MQTT Core Tools"
        E[MQTT Connection Tool] --> F[Topic Discovery]
        F --> G[Message Collection]
        G --> H[Message Publishing]
    end
    
    subgraph "Phase 3: AI Optimization"
        I[Message Pruning] --> J[Schema Analysis]
        J --> K[Web Monitor Interface]
    end
    
    subgraph "Phase 4: Production Ready"
        L[Advanced Tools] --> M[Docker Integration]
        M --> N[Umbrel Deployment]
        N --> O[Testing & Documentation]
    end
    
    D --> E
    H --> I
    K --> L
    
    subgraph "Milestones"
        M1[MVP Ready]
        M2[AI Optimized]
        M3[Production Ready]
    end
    
    D --> M1
    K --> M2
    O --> M3
```

## Phase 1: MCP Foundation (Woche 1)
**Goal**: Funktionsfähiger MCP Server mit Session Management
**User Value**: AI Assistant kann sich zu MQTT Brokern verbinden

### Deliverables
- ✅ Python 3.11+ Projekt mit asyncio setup
- ✅ SimpleMCPServer mit JSON-RPC 2.0 über STDIO
- ✅ MQTTConnectionManager mit session lifecycle
- ✅ Basic error handling und logging
- ✅ SSH + docker exec Integration (wie MongoDB MCP)

### Success Criteria
- [ ] AI Assistant kann MCP Server über SSH erreichen
- [ ] Session Management funktioniert (create, list, close)
- [ ] Credential encryption mit Fernet funktioniert
- [ ] Basic tool registration und execution works
- [ ] Error responses sind JSON-RPC 2.0 compliant

### MVP Tools (Phase 1)
1. **establish_connection** - MQTT broker connection
2. **list_active_connections** - Session management  
3. **close_connection** - Session cleanup

### Technical Components
```mermaid
graph LR
    A[SimpleMCPServer] --> B[MQTTConnectionManager]
    A --> C[MQTTTools]
    B --> D[MQTTSession]
    B --> E[Fernet Encryption]
    C --> F[Tool Registry]
    
    subgraph "External"
        G[SSH + docker exec]
        H[AI Assistant]
    end
    
    G --> A
    A --> H
```

## Phase 2: MQTT Core Tools (Woche 2)
**Goal**: Vollständige MQTT Operations für AI Assistant
**User Value**: AI kann MQTT brokers erkunden und Messages sammeln

### Deliverables
- ✅ aiomqtt Integration für async MQTT operations
- ✅ MessageCollector mit time-bounded collection
- ✅ Topic discovery mit MQTT wildcards (+ und #)
- ✅ Message publishing mit QoS support
- ✅ Connection string parsing (mqtt://user:pass@host:port/client_id)

### Success Criteria  
- [ ] MQTT broker connection innerhalb 30 Sekunden
- [ ] Topic discovery findet verfügbare topics
- [ ] Message collection sammelt messages für specified duration
- [ ] Message publishing erreicht broker successfully
- [ ] QoS 0, 1, 2 support funktioniert

### MVP Tools (Phase 2)
4. **list_topics** - Topic discovery mit wildcards
5. **subscribe_and_collect** - Time-bounded message collection
6. **publish_message** - Message publishing mit QoS

### MQTT Integration Flow
```mermaid
sequenceDiagram
    participant AI as AI Assistant
    participant MCP as MCP Server
    participant MQTT as MQTT Broker
    participant IOT as IoT Device

    AI->>MCP: establish_connection(mqtt://broker:1883)
    MCP->>MQTT: Connect with aiomqtt
    MQTT->>MCP: Connection established
    MCP->>AI: Session ID returned

    AI->>MCP: list_topics(session_id, "#", 30s)
    MCP->>MQTT: Subscribe to wildcard
    IOT->>MQTT: Publish to various topics
    MQTT->>MCP: Forward topic messages
    MCP->>MCP: Collect unique topic names
    MCP->>AI: Topic list with metadata

    AI->>MCP: subscribe_and_collect(session_id, "sensor/+/data", 60s)
    MCP->>MQTT: Subscribe to pattern
    IOT->>MQTT: Publish sensor data
    MQTT->>MCP: Forward messages
    MCP->>MCP: Time-bounded collection
    MCP->>AI: Message collection result
```

## Phase 3: AI Optimization (Woche 3)
**Goal**: AI-optimierte Message Processing und Monitoring
**User Value**: AI bekommt intelligently pruned data für bessere analysis

### Deliverables
- ✅ MessagePruner mit intelligent pruning algorithm
- ✅ SchemaAnalyzer für message structure analysis
- ✅ WebMonitor FastAPI interface (Port 8090)
- ✅ Performance optimization für large message volumes
- ✅ Enhanced error handling mit recovery strategies

### Success Criteria
- [ ] Message pruning reduziert 500+ messages auf 50 für AI
- [ ] Schema analysis erkennt JSON/XML/binary patterns
- [ ] Web interface zeigt live session status
- [ ] Memory usage bleibt unter 256MB
- [ ] Message collection startet innerhalb 2 Sekunden

### Advanced Features (Phase 3)
- **Intelligent Pruning**: Preserve errors, first/last, temporal distribution
- **Schema Analysis**: JSON schema generation from message samples
- **Web Monitoring**: Real-time status und statistics interface
- **Performance**: Memory limits, connection pooling, async optimization

### Message Pruning Strategy
```mermaid
flowchart TD
    A[Raw Messages<br/>500+ messages] --> B{Message Count > 50?}
    B -->|No| C[Return All Messages]
    B -->|Yes| D[Prioritize Messages]
    
    D --> E[Error Messages<br/>High Priority]
    D --> F[First/Last Messages<br/>Timeline Boundaries]
    D --> G[Diverse Payloads<br/>Structure Variety]
    D --> H[Temporal Sample<br/>Even Distribution]
    
    E --> I[Combine Top 50]
    F --> I
    G --> I
    H --> I
    
    I --> J[Pruned Collection<br/>≤50 messages optimized for AI]
```

## Phase 4: Production Ready (Woche 4)
**Goal**: Production-ready Umbrel App deployment
**User Value**: Einfache Installation und reliable operation

### Deliverables
- ✅ Advanced MCP tools (get_topic_schema, debug_device, monitor_performance, test_connection)
- ✅ Docker multi-stage builds für optimized images
- ✅ Umbrel app integration (umbrel-app.yml, docker-compose.yml)
- ✅ Comprehensive testing suite
- ✅ Production documentation und troubleshooting guides

### Success Criteria
- [ ] Alle 10 MCP tools funktionieren correctly
- [ ] Docker image size unter 500MB
- [ ] Umbrel deployment funktioniert out-of-the-box
- [ ] All tests pass (unit, integration, e2e)
- [ ] Performance targets erreicht (siehe system architecture)

### Complete Tool Set (Phase 4)
7. **get_topic_schema** - Message structure analysis
8. **debug_device** - Device-specific monitoring 
9. **monitor_performance** - Throughput & latency metrics
10. **test_connection** - Health check

### Production Deployment Flow
```mermaid
stateDiagram-v2
    [*] --> Development
    Development --> Testing : Phase Complete
    Testing --> Staging : Tests Pass
    Staging --> Production : Validation Success
    
    Testing --> Development : Issues Found
    Staging --> Testing : Validation Failed
    Production --> Monitoring : Deployment Complete
    
    Monitoring --> [*] : Success
    Monitoring --> Staging : Issues Detected
    
    note right of Testing
        • Unit tests
        • Integration tests  
        • MQTT broker tests
        • Performance tests
    end note
    
    note right of Staging
        • Docker build test
        • Umbrel deployment test
        • Full tool validation
        • Memory/CPU checks
    end note
    
    note right of Production
        • Umbrel App Store ready
        • Documentation complete
        • User support ready
        • Monitoring active
    end note
```

## Feature Implementation Priority

```mermaid
flowchart LR
    subgraph "Must-Have MVP (Phase 1-2)"
        A[MCP Protocol] --> B[Session Management]
        B --> C[MQTT Connection]
        C --> D[Topic Discovery]
        D --> E[Message Collection]
    end
    
    subgraph "Should-Have Optimization (Phase 3)"
        F[Message Pruning] --> G[Schema Analysis]
        G --> H[Web Monitoring]
        H --> I[Performance Tuning]
    end
    
    subgraph "Could-Have Advanced (Phase 4)"
        J[Device Debugging] --> K[Performance Metrics]
        K --> L[Health Checks]
        L --> M[Production Deploy]
    end
    
    E --> F
    I --> J
    
    style A fill:#ff9999
    style E fill:#ff9999
    style F fill:#99ccff
    style I fill:#99ccff
    style J fill:#99ff99
    style M fill:#99ff99
```

## Risk Assessment

```mermaid
quadrantChart
    title Development Risks vs Impact
    x-axis Low Impact --> High Impact
    y-axis Low Risk --> High Risk
    
    MQTT Connection Issues: [0.9, 0.4]
    Session Management Bugs: [0.7, 0.3]
    Message Collection Performance: [0.8, 0.6]
    AI Pruning Algorithm: [0.6, 0.5]
    Docker Integration: [0.8, 0.3]
    Umbrel Deployment: [0.9, 0.2]
    Testing Coverage: [0.5, 0.2]
    Documentation Quality: [0.4, 0.1]
```

## Development Resources

```mermaid
pie title Development Effort Distribution
    "MCP Protocol Implementation" : 25
    "MQTT Integration & Tools" : 30
    "AI Optimization & Pruning" : 20
    "Web Interface & Monitoring" : 10
    "Docker & Deployment" : 10
    "Testing & Documentation" : 5
```

## Quality Gates per Phase

### Phase 1 Gates
- [ ] SSH integration funktioniert identical zu MongoDB MCP
- [ ] Session management mit encryption works
- [ ] Basic MCP tools respond correctly
- [ ] Error handling follows JSON-RPC 2.0
- [ ] Memory usage acceptable (<128MB)

### Phase 2 Gates  
- [ ] MQTT broker connection reliable
- [ ] Topic discovery finds actual topics
- [ ] Message collection time-bounded works
- [ ] Message publishing reaches broker
- [ ] QoS levels function correctly

### Phase 3 Gates
- [ ] Message pruning optimizes for AI context
- [ ] Schema analysis provides useful insights
- [ ] Web interface shows accurate status
- [ ] Performance targets met
- [ ] Memory limits enforced

### Phase 4 Gates
- [ ] All 10 tools pass integration tests
- [ ] Docker builds successfully
- [ ] Umbrel deployment automated
- [ ] Documentation complete
- [ ] Production monitoring ready

## Success Metrics

### Technical Metrics
- **Connection Time**: <30 seconds to MQTT broker
- **Message Collection**: Start within 2 seconds
- **Memory Usage**: <256MB total, <50MB per session
- **Concurrent Sessions**: 5 MQTT connections supported
- **Tool Response Time**: <100ms overhead per tool call

### User Experience Metrics
- **Installation Time**: <5 minutes on Umbrel
- **Learning Curve**: AI Assistant productive within 10 minutes
- **Error Recovery**: Clear error messages, automatic retries
- **Documentation**: Complete troubleshooting guides
- **Support**: Community discussions und bug reports 