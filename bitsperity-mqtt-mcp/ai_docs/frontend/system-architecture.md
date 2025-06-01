# MQTT MCP Frontend - System Architecture

## Übersicht der Frontend-Erweiterung

Die Frontend-Erweiterung für den MQTT MCP Server bietet eine webbasierte Benutzeroberfläche zur Überwachung, Dokumentation und Verwaltung des MCP Servers. Die Architektur folgt dem Prinzip einer einfachen, aber leistungsfähigen Single-Page-Application ohne schwere Frameworks.

### Architekturziele
- **MCP Tool Education**: Primärer Fokus auf Tool-Verständnis und -Nutzung
- **Live Monitoring**: Echtzeit-Überwachung von Tool Calls und System Health
- **Minimaler Overhead**: Keine negativen Auswirkungen auf MCP Server Performance
- **Umbrel Integration**: Seamlose Integration in Umbrel Ecosystem

## Systemkomponenten Übersicht

```mermaid
graph TB
    subgraph "Frontend Architecture (Port 8091)"
        subgraph "Client-Side Components"
            A[HTML/CSS/JS Frontend]
            B[WebSocket Client]
            C[Chart.js Visualization]
            D[Local State Management]
        end
        
        subgraph "Backend Integration"
            E[Express.js Web Server]
            F[WebSocket Server]
            G[MongoDB Integration]
            H[MCP Server Logger]
        end
    end
    
    subgraph "Existing MQTT MCP Server"
        I[MCP Server :stdio]
        J[MQTT Tools (10 Tools)]
        K[Session Management]
    end
    
    subgraph "Data Persistence"
        L[(MongoDB)]
        M[mcp_tool_calls]
        N[mcp_system_logs]
        O[mcp_performance_metrics]
    end
    
    subgraph "AI Assistant Integration"
        P[Cursor/Claude]
        Q[SSH Connection]
        R[docker exec]
    end
    
    A --> E
    B --> F
    F --> G
    G --> L
    H --> I
    I --> J
    P --> Q
    Q --> R
    R --> I
    
    L --> M
    L --> N  
    L --> O
```

## Frontend Komponenten-Architektur

### 1. Client-Side Architecture

```mermaid
graph TD
    subgraph "Frontend Components"
        A[App.js - Main Application]
        
        subgraph "Feature Components"
            B[ToolDashboard.js]
            C[LiveMonitor.js]
            D[SessionManager.js]
            E[HealthDashboard.js]
            F[SystemLogs.js]
            G[TutorialOverlay.js]
        end
        
        subgraph "Shared Components"
            H[WebSocketClient.js]
            I[StateManager.js]
            J[APIClient.js]
            K[UIComponents.js]
        end
        
        subgraph "Utilities"
            L[DataFormatter.js]
            M[FilterEngine.js]
            N[ExportManager.js]
            O[ThemeManager.js]
        end
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    
    B --> H
    C --> H
    D --> H
    E --> H
    
    H --> I
    I --> J
    
    C --> M
    E --> L
    G --> N
```

### 2. State Management Architecture

```mermaid
graph TB
    subgraph "Application State"
        A[AppState Object]
        
        subgraph "Domain States"
            B[ToolState]
            C[MonitorState]
            D[SessionState]
            E[HealthState]
            F[LogState]
            G[UIState]
        end
        
        subgraph "State Operations"
            H[StateUpdater]
            I[ActionDispatcher]
            J[EventHandler]
        end
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    
    H --> A
    I --> H
    J --> I
    
    B -.-> |Tool Documentation| K[Tool Cards]
    C -.-> |Live Data| L[Monitor Feed]
    D -.-> |Session List| M[Session Cards] 
    E -.-> |Performance| N[Health Charts]
    F -.-> |Optional Logs| O[Log Panel]
    G -.-> |UI Settings| P[Theme/Layout]
```

## Data Flow Architecture

### 1. Tool Call Monitoring Flow

```mermaid
sequenceDiagram
    participant AI as AI Assistant
    participant MCP as MCP Server
    participant LOG as MongoDB Logger
    participant DB as MongoDB
    participant WS as WebSocket Server
    participant FE as Frontend Client

    AI->>MCP: execute_tool_call(params)
    MCP->>LOG: log_tool_call_start(call_id, tool, params)
    LOG->>DB: INSERT into mcp_tool_calls
    LOG->>WS: emit("tool_call_started", data)
    WS->>FE: WebSocket: tool_call_started
    FE->>FE: update_monitor_state()
    
    MCP->>MCP: execute_tool_logic()
    MCP->>LOG: log_tool_call_complete(call_id, result)
    LOG->>DB: UPDATE mcp_tool_calls SET result
    LOG->>WS: emit("tool_call_completed", data)
    WS->>FE: WebSocket: tool_call_completed
    FE->>FE: update_monitor_state()
    
    MCP->>AI: return tool_result
```

### 2. Real-time Data Synchronization

```mermaid
graph LR
    subgraph "Data Sources"
        A[Tool Call Events]
        B[System Log Events]
        C[Performance Metrics]
        D[Session Updates]
    end
    
    subgraph "Event Processing"
        E[Event Aggregator]
        F[Data Formatter]
        G[WebSocket Emitter]
    end
    
    subgraph "Frontend Reception"
        H[WebSocket Client]
        I[Event Router]
        J[State Updater]
    end
    
    subgraph "UI Components"
        K[Live Monitor]
        L[Health Dashboard]
        M[Session Manager]
        N[Optional Logs]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    
    J --> K
    J --> L
    J --> M
    J --> N
```

## Backend Integration Architecture

### 1. Web Server Components

```mermaid
graph TD
    subgraph "Express.js Web Server (Port 8091)"
        A[Static File Server]
        B[API Routes]
        C[WebSocket Handler]
        D[MongoDB Middleware]
    end
    
    subgraph "API Endpoints"
        E[GET /api/tools - Tool Documentation]
        F[GET /api/sessions - Active Sessions]
        G[GET /api/health - Health Metrics]
        H[GET /api/logs - System Logs]
        I[POST /api/export - Data Export]
    end
    
    subgraph "WebSocket Events"
        J[tool_call_started]
        K[tool_call_completed]
        L[system_log]
        M[health_update]
        N[session_change]
    end
    
    A --> |/| O[Frontend Assets]
    B --> E
    B --> F
    B --> G
    B --> H
    B --> I
    
    C --> J
    C --> K
    C --> L
    C --> M
    C --> N
```

### 2. MongoDB Integration Schema

```mermaid
erDiagram
    MCP_TOOL_CALLS {
        ObjectId _id
        String call_id
        DateTime timestamp_start
        DateTime timestamp_end
        String tool_name
        Object parameters
        String session_id
        Integer duration_ms
        String status
        Object response
        DateTime created_at
        DateTime expires_at
    }
    
    MCP_SYSTEM_LOGS {
        ObjectId _id
        DateTime timestamp
        String level
        String component
        String message
        Object context
        DateTime created_at
        DateTime expires_at
    }
    
    MCP_PERFORMANCE_METRICS {
        ObjectId _id
        DateTime timestamp
        Float cpu_percent
        Float memory_mb
        Integer active_sessions
        Integer health_score
        Object network_stats
        DateTime created_at
        DateTime expires_at
    }
```

## Deployment Architecture

### 1. Docker Integration

```mermaid
graph TB
    subgraph "Docker Container (bitsperity/mqtt-mcp)"
        subgraph "MCP Server Process"
            A[Python MCP Server :stdio]
            B[MQTT Tools]
            C[Session Manager]
        end
        
        subgraph "Frontend Server Process"
            D[Node.js Express Server :8091]
            E[Static File Serving]
            F[WebSocket Server]
            G[MongoDB Logger]
        end
        
        subgraph "Process Communication"
            H[Shared Memory/Events]
            I[File System Logging]
            J[IPC Messaging]
        end
    end
    
    subgraph "External Dependencies"
        K[(MongoDB Container)]
        L[MQTT Broker]
        M[SSH Access]
    end
    
    A --> H
    D --> H
    G --> K
    B --> L
    M --> A
    
    style A fill:#ff9999
    style D fill:#99ccff
    style K fill:#99ff99
```

### 2. Umbrel App Configuration

```yaml
# umbrel-app.yml
manifestVersion: 1
id: bitsperity-mqtt-mcp
category: automation
name: MQTT MCP Server
version: "1.0.0"
tagline: "MQTT Model Context Protocol Server for AI"
description: >
  AI-powered MQTT device analysis with Model Context Protocol.
  Includes web interface for tool monitoring and documentation.
  
developer: Bitsperity
website: https://github.com/bitsperity/mqtt-mcp
dependencies:
  - bitsperity-mongodb-mcp  # Shared MongoDB instance

repo: https://github.com/bitsperity/bitsperity-mqtt-mcp
support: https://github.com/bitsperity/bitsperity-mqtt-mcp/issues
port: 8091
gallery:
  - 1.jpg
  - 2.jpg
  - 3.jpg
path: ""

defaultUsername: ""
defaultPassword: ""

submitter: Bitsperity
submission: https://github.com/getumbrel/umbrel-apps/pull/xxx
```

### 3. Network Architecture

```mermaid
graph TB
    subgraph "Umbrel Host Network"
        A[umbrel.local:8091 - Web Interface]
        B[SSH Access for AI Assistants]
        C[Docker Host Network Mode]
    end
    
    subgraph "Container Network"
        D[MCP Server :stdio]
        E[Frontend Server :8091]
        F[MongoDB Connection]
        G[MQTT Broker Access]
    end
    
    subgraph "External Access"
        H[AI Assistant - Cursor/Claude]
        I[Web Browser - User]
        J[MQTT Broker - IoT Devices]
    end
    
    H --> B
    B --> D
    I --> A
    A --> E
    E --> F
    D --> G
    G --> J
    
    style A fill:#ff9999
    style D fill:#99ccff
    style H fill:#99ff99
```

## Security Architecture

### 1. Access Control

```mermaid
graph TD
    subgraph "Security Layers"
        A[Local Network Access Only]
        B[No Authentication Required]
        C[Data Isolation per Session]
        D[TTL-based Data Cleanup]
    end
    
    subgraph "Data Privacy"
        E[No Credential Persistence]
        F[Memory-only MQTT Credentials]
        G[Session-based Encryption]
        H[Automatic Data Expiration]
    end
    
    subgraph "Network Security"
        I[Umbrel Network Isolation]
        J[Docker Container Isolation]
        K[Host Network for SSH Only]
        L[No External API Exposure]
    end
    
    A --> I
    C --> E
    D --> H
    K --> B
```

### 2. Data Security Flow

```mermaid
sequenceDiagram
    participant USER as Web Browser
    participant FE as Frontend Server
    participant DB as MongoDB
    participant MCP as MCP Server

    USER->>FE: HTTP Request (Local Network)
    Note over FE: No Auth Required (Local Only)
    
    FE->>DB: Query Tool Calls
    Note over DB: TTL Cleanup (24h Tool Calls)
    
    DB->>FE: Return Data
    Note over FE: Filter Sensitive Data
    
    FE->>USER: JSON Response
    Note over USER: Client-side State Only
    
    MCP->>DB: Log Tool Call
    Note over DB: Session Isolation
    
    DB->>DB: Auto-expire Old Data
    Note over DB: Privacy Protection
```

## Performance Architecture

### 1. Frontend Performance Optimization

```mermaid
graph TD
    subgraph "Client Performance"
        A[Virtual Scrolling for Large Lists]
        B[Lazy Loading of Components]
        C[Debounced Filter Updates]
        D[Memory-efficient State Management]
    end
    
    subgraph "Data Optimization"
        E[Rolling Window (500 Tool Calls)]
        F[Response Truncation (1KB limit)]
        G[Intelligent Caching]
        H[Background Data Cleanup]
    end
    
    subgraph "Network Optimization"
        I[WebSocket for Real-time]
        J[Compressed JSON Responses]
        K[Delta Updates Only]
        L[Connection Pooling]
    end
    
    A --> E
    B --> G
    C --> I
    D --> H
```

### 2. Resource Management

```mermaid
graph LR
    subgraph "Memory Management"
        A[Frontend: <50MB]
        B[Tool Calls: Rolling 500]
        C[Logs: Max 200 entries]
        D[Charts: 24h data max]
    end
    
    subgraph "CPU Optimization"
        E[Async Operations]
        F[Worker Threads for Export]
        G[Throttled UI Updates]
        H[Efficient DOM Manipulation]
    end
    
    subgraph "Storage Optimization"
        I[MongoDB TTL Indexes]
        J[Compressed Chart Data]
        K[LocalStorage for UI State]
        L[No File System Usage]
    end
    
    A --> E
    B --> F
    C --> G
    D --> H
    
    E --> I
    F --> J
    G --> K
    H --> L
```

## Integration Points

### 1. MCP Server Integration

```mermaid
graph TB
    subgraph "MCP Server Extensions"
        A[Tool Call Interceptor]
        B[Logging Middleware]
        C[Performance Monitor]
        D[Health Check Endpoint]
    end
    
    subgraph "Frontend Bridges"
        E[Event Emitter]
        F[Data Aggregator] 
        G[WebSocket Publisher]
        H[API Server]
    end
    
    subgraph "Shared Resources"
        I[MongoDB Connection]
        J[Configuration Files]
        K[Log Rotation]
        L[Error Handling]
    end
    
    A --> E
    B --> F
    C --> G
    D --> H
    
    E --> I
    F --> J
    G --> K
    H --> L
```

### 2. AI Assistant Integration

```mermaid
sequenceDiagram
    participant AI as AI Assistant (Cursor)
    participant SSH as SSH Connection
    participant DOCKER as Docker Exec
    participant MCP as MCP Server
    participant FE as Frontend Logger
    participant WEB as Web Interface

    AI->>SSH: Connect to Umbrel Host
    SSH->>DOCKER: docker exec -it mqtt-mcp
    DOCKER->>MCP: Start MCP Session
    
    Note over AI,MCP: Normal MCP Protocol Communication
    AI->>MCP: Tool Call Request
    MCP->>FE: Log Tool Call (Background)
    FE->>WEB: Update Live Monitor
    MCP->>AI: Tool Call Response
    
    Note over WEB: User can monitor AI's tool usage in real-time
```

## Development Workflow

### 1. Build Pipeline

```mermaid
graph LR
    subgraph "Development Phase"
        A[Local Development]
        B[Frontend Build]
        C[Integration Testing]
        D[Performance Testing]
    end
    
    subgraph "Deployment Phase"
        E[Docker Build]
        F[Multi-stage Optimization]
        G[Docker Hub Push]
        H[Umbrel Deployment]
    end
    
    subgraph "Testing Phase"
        I[Unit Tests]
        J[Integration Tests]
        K[E2E Tests]
        L[Performance Tests]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    
    I --> J
    J --> K
    K --> L
    L --> E
```

### 2. Deployment Strategy

```bash
# Dockerfile Multi-stage Build
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/ .
RUN npm install && npm run build

FROM python:3.11-slim AS final
# MCP Server installation
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
# Combined deployment
```

## Monitoring und Logging

### 1. System Monitoring

```mermaid
graph TD
    subgraph "Application Monitoring"
        A[Tool Call Metrics]
        B[WebSocket Connection Status]
        C[Frontend Performance]
        D[User Interaction Tracking]
    end
    
    subgraph "Infrastructure Monitoring"
        E[Container Resource Usage]
        F[MongoDB Performance]
        G[Network Throughput]
        H[Error Rate Tracking]
    end
    
    subgraph "Health Checks"
        I[MCP Server Health]
        J[Frontend Server Health]
        K[Database Connectivity]
        L[External Service Health]
    end
    
    A --> E
    B --> F
    C --> G
    D --> H
    
    E --> I
    F --> J
    G --> K
    H --> L
```

### 2. Error Handling Strategy

```mermaid
flowchart TD
    A[Error Occurs] --> B{Error Type?}
    
    B -->|Network Error| C[Retry with Backoff]
    B -->|Data Error| D[Show User Message]
    B -->|System Error| E[Log and Alert]
    
    C --> F{Retry Successful?}
    F -->|Yes| G[Continue Operation]
    F -->|No| H[Graceful Degradation]
    
    D --> I[Toast Notification]
    E --> J[Error Dashboard]
    
    H --> K[Offline Mode]
    I --> L[User Feedback]
    J --> M[Admin Alert]
    
    style A fill:#ff9999
    style G fill:#99ff99
    style K fill:#ffff99
```

## Fazit der Architektur

Die Frontend-Architektur für den MQTT MCP Server ist als leichtgewichtige, aber funktionsreiche Erweiterung konzipiert, die:

### Hauptvorteile:
1. **Minimaler Impact**: Keine Performance-Beeinträchtigung des MCP Servers
2. **Echtzeit-Fähigkeiten**: Live-Monitoring über WebSocket
3. **Benutzerfreundlichkeit**: Intuitive Bedienung ohne komplexe Setup
4. **Skalierbarkeit**: Modularer Aufbau für zukünftige Erweiterungen
5. **Umbrel-Integration**: Nahtlose Integration in Umbrel Ecosystem

### Technische Highlights:
- **Vanilla JavaScript**: Keine schweren Framework-Dependencies
- **MongoDB Integration**: Shared Instance mit MCP Server
- **Docker-optimiert**: Multi-stage Build für minimale Image-Größe
- **Security-first**: Local-only Access, automatische Data Cleanup
- **Performance-optimiert**: Virtual Scrolling, Memory Management

Die Architektur ist bereit für die Implementierung und folgt allen Requirements aus der umfassenden Frontend-Dokumentation. 