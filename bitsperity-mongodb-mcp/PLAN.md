# MongoDB MCP Server - Umbrel App Plan

## 🎯 App-Übersicht

Eine moderne, benutzerfreundliche Umbrel-App für MongoDB Model Context Protocol (MCP) Server, die es ermöglicht, MongoDB-Datenbanken nahtlos mit LLM-Anwendungen wie Cursor zu verbinden.

## 🚀 Features

### Core Funktionalität
- **Dynamic Connection Management**: Verbindungen werden zur Laufzeit basierend auf AI-Gespräch hergestellt
- **Multi-Database Support**: Gleichzeitige Arbeit mit mehreren MongoDB-Instanzen
- **Conversation-Context Connections**: Connection-Strings werden im Chat-Kontext übergeben
- **Database Discovery**: Automatische Erkennung aller verfügbaren Datenbanken
- **Collection Browsing**: Übersicht aller Collections mit Metadaten
- **Intelligent Querying**: Smart Query Interface für Collection-Analyse
- **Schema Inference**: Automatische Schema-Erkennung für besseres Verständnis
- **Real-time Monitoring**: Live-Status der MongoDB-Verbindung
- **Connection Pooling**: Effiziente Wiederverwendung von Verbindungen
- **Security-First**: Keine persistente Speicherung von Connection-Strings

### UX/UI Design
- **Modern Dark Theme**: Minimalistisches, augenfreundliches Design
- **Responsive Layout**: Optimiert für Desktop und Mobile
- **Interactive Dashboards**: Drag & Drop Query Builder
- **Real-time Updates**: WebSocket-basierte Live-Updates
- **Progressive Web App**: Offline-Funktionalität wo möglich

## 🏗️ System-Architektur

```mermaid
graph TB
    subgraph "Cursor IDE"
        A[Cursor] --> B[MCP Client]
    end
    
    subgraph "Umbrel App - MongoDB MCP"
        B --> C[MCP Server]
        C --> D[Web Interface]
        C --> E[MongoDB Connector]
        D --> F[Query Builder]
        D --> G[Schema Visualizer]
        D --> H[Connection Manager]
    end
    
    subgraph "External Services"
        E --> I[MongoDB Atlas/Local]
        E --> J[MongoDB Compass Data]
    end
    
    subgraph "Data Flow"
        C --> K[MCP Protocol Handler]
        K --> L[JSON-RPC 2.0]
        L --> M[Tools & Resources]
    end
    
    style A fill:#ff6b6b
    style C fill:#4ecdc4
    style D fill:#45b7d1
    style I fill:#96ceb4
```

## 📋 MCP Tools & Resources

```mermaid
classDiagram
    class MCPServer {
        +name: string
        +version: string
        +initialize()
        +listTools()
        +listResources()
        +handleToolCall()
    }
    
    class DatabaseTool {
        +list_databases()
        +get_database_info()
        +list_collections()
        +get_collection_schema()
        +query_collection()
        +aggregate_data()
    }
    
    class ConnectionManager {
        +connection_string: string
        +validate_connection()
        +test_connectivity()
        +get_server_info()
    }
    
    class SchemaAnalyzer {
        +analyze_collection()
        +infer_schema()
        +get_sample_documents()
        +get_field_statistics()
    }
    
    MCPServer --> DatabaseTool
    MCPServer --> ConnectionManager
    DatabaseTool --> SchemaAnalyzer
```

## 📋 Erweiterte MCP Tools & Resources

```mermaid
classDiagram
    class MCPServer {
        +name: string
        +version: string
        +active_connections: Dict
        +initialize()
        +listTools()
        +listResources()
        +handleToolCall()
        +cleanup_connections()
    }
    
    class ConnectionManager {
        +establish_connection(connection_string)
        +validate_connection_string()
        +test_connectivity()
        +get_connection_info()
        +close_connection(session_id)
        +list_active_connections()
    }
    
    class DatabaseTool {
        +list_databases(session_id)
        +get_database_info(session_id, db_name)
        +list_collections(session_id, db_name)
        +get_collection_schema(session_id, db_name, collection)
        +query_collection(session_id, db_name, collection, query)
        +aggregate_data(session_id, db_name, collection, pipeline)
    }
    
    class SessionManager {
        +create_session()
        +get_session(session_id)
        +expire_session(session_id)
        +cleanup_expired_sessions()
    }
    
    class SchemaAnalyzer {
        +analyze_collection(session_id, db_name, collection)
        +infer_schema()
        +get_sample_documents()
        +get_field_statistics()
    }
    
    MCPServer --> ConnectionManager
    MCPServer --> SessionManager
    MCPServer --> DatabaseTool
    DatabaseTool --> SchemaAnalyzer
    ConnectionManager --> SessionManager
```

## 🔄 Sequence Diagramm - Query Flow

```mermaid
sequenceDiagram
    participant C as Cursor
    participant MCP as MCP Server
    participant DB as MongoDB
    participant UI as Web Interface
    
    C->>MCP: Request available tools
    MCP->>C: Return tools list
    
    C->>MCP: Call list_databases()
    MCP->>DB: Connect & query databases
    DB->>MCP: Return database list
    MCP->>C: Formatted database info
    
    C->>MCP: Call query_collection(db, collection, query)
    MCP->>DB: Execute MongoDB query
    DB->>MCP: Return results
    MCP->>C: Structured response
    
    Note over UI: Parallel Web Interface
    UI->>MCP: WebSocket connection
    MCP->>UI: Real-time updates
```

## 🔄 Sequence Diagramm - Dynamic Connection Flow

```mermaid
sequenceDiagram
    participant U as User
    participant C as Cursor
    participant MCP as MCP Server
    participant DB as MongoDB
    
    U->>C: "Connect to mongodb://user:pass@cluster.mongodb.net/mydb"
    C->>MCP: establish_connection(connection_string)
    MCP->>MCP: Validate & parse connection string
    MCP->>DB: Test connection
    DB->>MCP: Connection successful
    MCP->>C: Connection established (session_id)
    
    U->>C: "Show me all databases"
    C->>MCP: list_databases(session_id)
    MCP->>DB: Query databases using active connection
    DB->>MCP: Return database list
    MCP->>C: Formatted database info
    
    U->>C: "Query users collection in myapp database"
    C->>MCP: query_collection(session_id, "myapp", "users", query)
    MCP->>DB: Execute query
    DB->>MCP: Return results
    MCP->>C: Structured response
    
    Note over MCP: Connections auto-expire after inactivity
    MCP->>MCP: Cleanup expired connections
```

## 📁 Vollständige Dateisystem-Struktur

```
bitsperity-mongodb-mcp/
├── 📄 PLAN.md                          # Diese Datei
├── 📄 umbrel-app.yml                   # App Manifest
├── 📄 docker-compose.yml               # Container Konfiguration
├── 📄 exports.sh                       # Environment Export Script
├── 📄 Dockerfile                       # Custom Docker Image
├── 📁 src/                             # Hauptanwendung
│   ├── 📄 server.py                    # MCP Server Hauptlogik
│   ├── 📄 mongodb_tools.py             # MongoDB-spezifische Tools
│   ├── 📄 schema_analyzer.py           # Schema-Analyse Engine
│   ├── 📄 connection_manager.py        # Verbindungsmanagement
│   ├── 📄 web_interface.py             # Web UI Backend
│   └── 📄 requirements.txt             # Python Dependencies
├── 📁 web/                             # Frontend
│   ├── 📄 index.html                   # Haupt-HTML
│   ├── 📄 style.css                    # Styling
│   ├── 📄 app.js                       # Frontend Logic
│   ├── 📄 components/                  # UI Komponenten
│   │   ├── 📄 ConnectionForm.js
│   │   ├── 📄 DatabaseExplorer.js
│   │   ├── 📄 QueryBuilder.js
│   │   └── 📄 SchemaViewer.js
│   └── 📁 assets/                      # Statische Assets
│       ├── 📄 logo.svg
│       └── 📄 favicon.ico
├── 📁 config/                          # Konfigurationsdateien
│   ├── 📄 mcp_config.json              # MCP Server Config
│   └── 📄 logging.conf                 # Logging Configuration
├── 📁 data/                            # Persistente Daten
│   ├── 📄 connections.json             # Gespeicherte Verbindungen
│   └── 📄 query_history.json           # Query-Historie
├── 📁 scripts/                         # Utility Scripts
│   ├── 📄 setup.sh                     # Initial Setup
│   ├── 📄 health_check.sh              # Health Check
│   └── 📄 backup.sh                    # Backup Script
├── 📁 tests/                           # Tests
│   ├── 📄 test_mcp_server.py
│   ├── 📄 test_mongodb_tools.py
│   └── 📄 test_integration.py
└── 📁 docs/                            # Dokumentation
    ├── 📄 API.md                       # API Dokumentation
    ├── 📄 SETUP.md                     # Setup Guide
    └── 📄 TROUBLESHOOTING.md           # Fehlerbehebung
```

## 🎨 UI/UX Design Konzept

### 1. Dashboard Layout - Dynamic Connections
```
┌─────────────────────────────────────────────┐
│ 🏠 MongoDB MCP Server      ⚙️ Settings     │
├─────────────────────────────────────────────┤
│ 🔗 Active Connections                       │
│ ┌─────────────────────────────────────────┐ │
│ │ 🟢 Atlas Prod (session_abc123)         │ │
│ │    mongodb://cluster0.mongodb.net       │ │
│ │    Last activity: 2m ago                │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ 🟡 Local Dev (session_def456)          │ │
│ │    mongodb://localhost:27017            │ │
│ │    Last activity: 15m ago               │ │
│ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ 📊 How to Connect                           │
│ 1. Tell Cursor: "Connect to mongodb://..." │
│ 2. MCP Server establishes connection       │
│ 3. Start querying your databases!          │
├─────────────────────────────────────────────┤
│ 📋 Recent Queries                           │
│ • users.find({status: "active"})           │
│ • products.aggregate([...])                 │
│ • logs.countDocuments()                     │
└─────────────────────────────────────────────┘
```

### 2. Color Scheme
- **Primary**: `#2563eb` (Blue)
- **Secondary**: `#06b6d4` (Cyan)
- **Accent**: `#10b981` (Green)
- **Background**: `#0f172a` (Dark)
- **Surface**: `#1e293b` (Dark Gray)
- **Text**: `#f8fafc` (Light)

### 3. Interactive Elements
- **Hover Effects**: Smooth 200ms transitions
- **Loading States**: Skeleton screens and spinners
- **Error Handling**: Inline error messages mit Retry-Buttons
- **Success Feedback**: Toast notifications

## 🔧 Technische Spezifikationen

### Backend Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI für Web Interface
- **MCP Library**: `mcp` Python SDK
- **Database Driver**: `pymongo` mit Connection Pooling
- **Session Management**: In-memory session store mit TTL
- **WebSocket**: `uvicorn` mit WebSocket Support
- **Validation**: `pydantic` für Data Models
- **Security**: `cryptography` für Connection String Encryption

### Frontend Stack
- **Vanilla JavaScript**: Keine Frameworks für Simplicity
- **CSS Framework**: Tailwind CSS (via CDN)
- **Icons**: Lucide Icons
- **Charts**: Chart.js für Visualisierungen
- **WebSocket**: Native WebSocket API

### Container Specs
- **Base Image**: `python:3.11-alpine`
- **Memory Limit**: 256MB
- **CPU Limit**: 0.5 cores
- **Storage**: 100MB persistent volume

### Connection Management Features
- **Session-based Connections**: Jede Verbindung bekommt eine eindeutige Session-ID
- **Automatic Cleanup**: Verbindungen werden nach Inaktivität automatisch geschlossen
- **Connection Pooling**: Effiziente Wiederverwendung von DB-Verbindungen
- **Multi-tenant Support**: Gleichzeitige Arbeit mit verschiedenen MongoDB-Instanzen
- **Security**: Connection-Strings werden nur im Memory gehalten, nie persistiert

## 🚀 Implementation Roadmap

### Phase 1: Core MCP Server (Woche 1)
- [ ] Basic MCP Server Setup
- [ ] MongoDB Connection Management
- [ ] Essential Tools Implementation
- [ ] Docker Container Build

### Phase 2: Advanced Features (Woche 2)
- [ ] Schema Analysis Engine
- [ ] Query Builder Backend
- [ ] Error Handling & Validation
- [ ] Logging & Monitoring

### Phase 3: Web Interface (Woche 3)
- [ ] Frontend Development
- [ ] Real-time Updates
- [ ] User Experience Polish
- [ ] Mobile Responsiveness

### Phase 4: Integration & Testing (Woche 4)
- [ ] Cursor Integration Testing
- [ ] Performance Optimization
- [ ] Security Hardening
- [ ] Documentation

## 🔒 Sicherheitskonzept

### 1. Connection Security
- **Ephemeral Connections**: Connection-Strings werden nur temporär im Memory gespeichert
- **Session-based Security**: Jede Verbindung ist an eine Session gebunden
- **Auto-Expire**: Verbindungen laufen automatisch nach Inaktivität ab
- **Encrypted Memory**: Sensitive Daten werden im Memory verschlüsselt
- **SSL/TLS**: Erzwungene sichere Verbindungen zu MongoDB
- **Input Validation**: Strenge Validierung aller Connection-Strings und Queries

### 2. Access Control
- **Session Isolation**: Sessions sind voneinander isoliert
- **Rate Limiting**: Schutz vor Missbrauch
- **Query Complexity Limits**: Schutz vor ressourcenintensiven Queries
- **Connection Limits**: Maximale Anzahl gleichzeitiger Verbindungen

### 3. Data Protection
- **No Persistent Storage**: Keine Speicherung von Connection-Strings auf Disk
- **Memory Clearing**: Sensitive Daten werden explizit aus dem Memory gelöscht
- **Audit Logging**: Logging von Verbindungsversuchen (ohne Credentials)
- **Secure Headers**: HTTPS-only, HSTS, CSP Headers

## 📊 Monitoring & Analytics

### Key Metrics
- Connection Health Status
- Query Performance (latency, errors)
- Resource Usage (CPU, Memory)
- User Interaction Analytics

### Alerting
- Connection failures
- High error rates
- Resource limits exceeded

## 🔄 Update Strategy

### Versioning
- Semantic Versioning (MAJOR.MINOR.PATCH)
- Backward compatibility für MCP Protocol
- Database schema migrations

### Deployment
- Rolling updates via Docker
- Configuration hot-reload
- Zero-downtime updates

---

*Dieses Design fokussiert auf Simplicity, Performance und hervorragende User Experience für nahtlose MongoDB-Integration mit Cursor und anderen MCP-Clients.* 

## 💬 Verwendung mit Cursor

### Beispiel-Konversation:
```
👤 User: "Verbinde dich mit meiner MongoDB: mongodb://user:pass@cluster0.mongodb.net/myapp"

🤖 Cursor: *calls establish_connection tool*
"✅ Verbindung hergestellt! Session ID: abc123. Verfügbare Datenbanken: myapp, analytics, logs"

👤 User: "Zeige mir alle Collections in der myapp Datenbank"

🤖 Cursor: *calls list_collections tool*
"📁 Collections in myapp: users (1.2K docs), products (856 docs), orders (3.4K docs)"

👤 User: "Analysiere das Schema der users Collection"

🤖 Cursor: *calls get_collection_schema tool*
"📊 Schema der users Collection:
- _id: ObjectId (required)
- email: String (required, unique)
- name: String (required)
- createdAt: Date (required)
- profile: Object (optional)
  - avatar: String
  - bio: String"
``` 