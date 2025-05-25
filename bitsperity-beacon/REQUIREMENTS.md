# Bitsperity Beacon - Service Discovery Server

## 🎯 Überblick

**Bitsperity Beacon** ist ein zentraler Service Discovery Server, der als Umbrel App implementiert wird. Er ermöglicht es Services im lokalen Netzwerk, sich zu registrieren und von anderen Geräten gefunden zu werden. Die App fungiert als "Leuchtfeuer" (Beacon) für alle Services im Bitsperity-Ökosystem.

### 🔗 Umbrel Ecosystem Integration

**Bitsperity Beacon** nutzt die bereits vorhandene **bitsperity-mongodb** App als Datenbank-Backend. Dies bietet mehrere Vorteile:

- **Shared Infrastructure**: Nutzt vorhandene MongoDB-Instanz
- **Konsistenz**: Alle Bitsperity Apps verwenden MongoDB
- **Skalierbarkeit**: MongoDB ist optimal für Service-Metadaten
- **Development**: Integration mit bitsperity-mongodb-mcp für Debugging
- **Resource Efficiency**: Keine zusätzliche Datenbank erforderlich

## 🏗️ Techstack

### Backend
- **Framework**: FastAPI (Python 3.11+) - **Optimal für mDNS/Service Discovery**
- **Database**: MongoDB (via bitsperity-mongodb App) mit Motor (async MongoDB driver)
- **mDNS Server**: python-zeroconf (667⭐, sehr mature) für Bonjour/mDNS
- **WebSocket**: FastAPI WebSocket für Real-time Updates
- **API**: RESTful API + WebSocket + mDNS
- **Validation**: Pydantic Models
- **Logging**: Python logging mit strukturierten Logs
- **Health Checks**: Integrierte Health-Check Endpoints
- **Performance**: Cython Extensions für kritische mDNS-Operationen

### Frontend
- **Framework**: React 18 mit TypeScript
- **UI Library**: Tailwind CSS + Headless UI
- **State Management**: Zustand
- **Real-time**: WebSocket Client
- **Charts**: Recharts für Visualisierungen
- **Icons**: Heroicons
- **Build Tool**: Vite

### Infrastructure
- **Container**: Docker mit Multi-stage Build
- **Reverse Proxy**: Nginx
- **Process Manager**: Supervisor
- **Network**: Docker Bridge Network
- **Storage**: MongoDB Connection zu bitsperity-mongodb App

## 🎯 Funktionsumfang

### Core Features

#### 1. Service Registration
- **REST API Endpoint**: `POST /api/v1/services/register`
- Services können sich mit Metadaten registrieren
- Automatische Health-Check Integration
- TTL (Time-To-Live) basierte Registrierung
- Service-Tags und Kategorien

#### 2. Service Discovery (mDNS/Bonjour)
- **mDNS Server**: Automatische Service-Ankündigung im lokalen Netzwerk
- **Bonjour/Zeroconf**: Zero-Configuration Service Discovery
- Services werden automatisch als `_servicetype._tcp.local` angekündigt
- Clients können Services über Standard mDNS-Queries finden
- **Backup REST API**: `GET /api/v1/services/discover` für Legacy-Support

#### 3. TTL-basierte Service-Verwaltung
- **TTL (Time-To-Live)** für automatische Service-Deregistrierung
- **Heartbeat-System**: Services senden periodische "Keep-Alive" Signale
- **Optionale Health Checks**: Nur für Services die es unterstützen
- **Graceful Degradation**: Services ohne Health Checks funktionieren trotzdem

#### 4. Real-time Updates
- WebSocket-basierte Live-Updates
- Service-Status Änderungen in Echtzeit
- Neue Service-Registrierungen
- Service-Deregistrierungen

#### 5. Web Dashboard
- Übersicht aller registrierten Services
- Service-Status Visualisierung
- Network Topology View
- Service-Details und Metadaten
- Health-Check Logs
- Service-Registrierung über UI

### Extended Features

#### 6. Service Groups
- Logische Gruppierung von Services
- Load Balancing Informationen
- Service Dependencies

#### 7. Network Discovery
- **mDNS/Bonjour Server**: Zentrale Service-Ankündigung
- **Service-Type Mapping**: Automatische Zuordnung zu mDNS Service-Types
  - `_mqtt._tcp.local` für MQTT Broker
  - `_http._tcp.local` für HTTP Services
  - `_iot._tcp.local` für IoT Devices
- **TXT Records**: Metadaten in DNS TXT Records
- **Automatische Netzwerk-Scanning** für Discovery bestehender Services
- **UPnP Integration** für zusätzliche Discovery-Methoden

#### 8. API Gateway Integration
- Service Routing Informationen
- API Endpoint Mapping
- Rate Limiting Konfiguration

## 🔧 Funktionsweise

### Service Registration Flow

```
1. Service startet (egal wo im Netzwerk)
2. Service sendet POST Request an /api/v1/services/register mit TTL
3. Beacon validiert Service-Daten
4. Beacon speichert Service in Database mit Ablaufzeit
5. Beacon kündigt Service via mDNS an
6. Beacon sendet WebSocket Update an alle Clients
7. Service ist nun discoverable
8. Service sendet periodische Heartbeats (optional)
```

### Service Discovery Flow (mDNS)

```
1. Service registriert sich bei Beacon
2. Beacon kündigt Service via mDNS als "_mqtt._tcp.local" an
3. Client (Arduino/HomegrowClient) macht mDNS Query für "_mqtt._tcp.local"
4. mDNS Server antwortet mit Service-Details (IP, Port, TXT Records)
5. Client kann sich direkt mit Service verbinden
6. Kein expliziter API-Call nötig - alles automatisch!
```

### TTL & Heartbeat Flow

```
1. Service registriert sich mit TTL (z.B. 300 Sekunden)
2. Beacon setzt Ablaufzeit für Service
3. Service sendet alle 60 Sekunden Heartbeat (PUT /api/v1/services/{id}/heartbeat)
4. Beacon verlängert TTL bei jedem Heartbeat
5. Bei TTL-Ablauf: Service wird automatisch deregistriert
6. mDNS Announcement wird gestoppt
7. WebSocket Update an alle Clients
```

## 📁 Filesystem Struktur

```
bitsperity-beacon/
├── README.md
├── REQUIREMENTS.md
├── umbrel-app.yml
├── docker-compose.yml
├── Dockerfile
├── .dockerignore
├── nginx.conf
├── supervisord.conf
├── .env.example
├── deploy-local.sh
├── deploy-github.sh
├── deploy-dockerhub.sh
├── applogo.svg
├── applogo.png
├── gallery/
│   ├── 1.png
│   ├── 2.png
│   └── 3.png
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── health_check.py
│   │   │   ├── service_group.py
│   │   │   └── base.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── health_check.py
│   │   │   └── discovery.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── services.py
│   │   │   │   ├── discovery.py
│   │   │   │   ├── health.py
│   │   │   │   └── websocket.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── ttl_manager.py
│   │   │   ├── service_registry.py
│   │   │   ├── mdns_server.py
│   │   │   ├── network_scanner.py
│   │   │   └── websocket_manager.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── validators.py
│   ├── requirements.txt
│   └── tests/
│       ├── __init__.py
│       ├── test_services.py
│       ├── test_discovery.py
│       └── test_health_checks.py
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   ├── public/
│   │   ├── favicon.ico
│   │   └── logo.png
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── components/
│       │   ├── Dashboard/
│       │   │   ├── ServiceGrid.tsx
│       │   │   ├── ServiceCard.tsx
│       │   │   ├── StatusIndicator.tsx
│       │   │   └── NetworkTopology.tsx
│       │   ├── ServiceDetails/
│       │   │   ├── ServiceModal.tsx
│       │   │   ├── HealthHistory.tsx
│       │   │   └── ServiceLogs.tsx
│       │   ├── Registration/
│       │   │   ├── RegisterForm.tsx
│       │   │   └── ServiceForm.tsx
│       │   └── Layout/
│       │       ├── Header.tsx
│       │       ├── Sidebar.tsx
│       │       └── Footer.tsx
│       ├── hooks/
│       │   ├── useWebSocket.ts
│       │   ├── useServices.ts
│       │   └── useHealthChecks.ts
│       ├── stores/
│       │   ├── serviceStore.ts
│       │   └── uiStore.ts
│       ├── types/
│       │   ├── service.ts
│       │   ├── health.ts
│       │   └── api.ts
│       └── utils/
│           ├── api.ts
│           ├── websocket.ts
│           └── formatters.ts
└── docs/
    ├── API.md
    ├── DEPLOYMENT.md
    └── EXAMPLES.md
```

## 🏛️ Klassendiagramm

```mermaid
classDiagram
    class Service {
        +_id: ObjectId
        +service_id: str
        +name: str
        +type: str
        +host: str
        +port: int
        +protocol: str
        +tags: List~str~
        +metadata: dict
        +ttl: int
        +expires_at: datetime
        +created_at: datetime
        +updated_at: datetime
        +last_heartbeat: datetime
        +register()
        +update()
        +deregister()
        +send_heartbeat()
    }

    class ServiceGroup {
        +id: UUID
        +name: str
        +description: str
        +services: List~Service~
        +load_balancing: dict
        +add_service(service)
        +remove_service(service)
    }

    class HealthCheck {
        +id: UUID
        +service_id: UUID
        +status: HealthStatus
        +response_time: float
        +error_message: str
        +checked_at: datetime
        +perform_check()
        +update_status()
    }

    class ServiceRegistry {
        +services: Dict~UUID_Service~
        +register_service(service_data)
        +discover_services(filters)
        +update_service(service_id, data)
        +deregister_service(service_id)
        +get_service_by_id(service_id)
        +extend_ttl(service_id)
    }

    class TTLManager {
        +cleanup_interval: int
        +start_cleanup_task()
        +stop_cleanup_task()
        +check_expired_services()
        +extend_service_ttl(service_id)
        +remove_expired_service(service_id)
    }

    class WebSocketManager {
        +connections: List~WebSocket~
        +connect(websocket)
        +disconnect(websocket)
        +broadcast_update(message)
        +send_to_client(websocket, message)
    }

    class MDNSServer {
        +zeroconf: Zeroconf
        +services: Dict~str_ServiceInfo~
        +register_service(service)
        +unregister_service(service_id)
        +update_service(service_id, data)
        +start_server()
        +stop_server()
    }

    class NetworkScanner {
        +scan_network()
        +discover_mdns_services()
        +discover_upnp_services()
        +validate_service(host, port)
    }

    Service --> HealthCheck : has optional
    ServiceGroup --> Service : contains
    ServiceRegistry --> Service : manages
    TTLManager --> Service : manages lifecycle
    WebSocketManager --> Service : broadcasts
    MDNSServer --> Service : announces
    NetworkScanner --> Service : discovers
```

## 🔄 Sequenzdiagramm

### Service Registration Sequence

```mermaid
sequenceDiagram
    participant HC as HomegrowClient
    participant API as BeaconAPI
    participant DB as Database
    participant HM as HealthChecker
    participant WS as WebSocketManager
    participant UI as Dashboard

    HC->>API: POST /api/v1/services/register
    Note over HC,API: {name: "homegrow-client", type: "iot", host: "192.168.1.100", port: 8080, ttl: 300}
    
    API->>API: Validate service data
    API->>DB: Store service with expiry time
    DB-->>API: Service ID
    
    API->>mDNS: Announce service via mDNS
    mDNS-->>API: Service announced
    
    API->>WS: Broadcast service registration
    WS->>UI: WebSocket: new service registered
    
    API-->>HC: 201 Created {service_id, expires_at: "2024-01-01T12:05:00Z"}
    
    loop Every 60 seconds (optional)
        HC->>API: PUT /api/v1/services/{id}/heartbeat
        API->>DB: Extend TTL
        Note over HC,API: Service bleibt aktiv
    end
```

### Service Discovery Sequence (mDNS)

```mermaid
sequenceDiagram
    participant Arduino as ArduinoDevice
    participant mDNS as mDNSServer
    participant MQTT as MQTTBroker
    participant Beacon as BeaconAPI

    Note over Beacon,mDNS: MQTT Service bereits bei Beacon registriert
    Beacon->>mDNS: Announce "_mqtt._tcp.local" service
    
    Arduino->>mDNS: mDNS Query "_mqtt._tcp.local"
    mDNS-->>Arduino: Service Response {host: "192.168.1.50", port: 1883, txt: metadata}
    
    Arduino->>MQTT: Connect to MQTT Broker
    MQTT-->>Arduino: Connection established
    
    Note over Arduino,MQTT: Arduino can now publish/subscribe to MQTT topics
```

### TTL Expiration Sequence

```mermaid
sequenceDiagram
    participant TTL as TTLManager
    participant DB as Database
    participant mDNS as mDNSServer
    participant WS as WebSocketManager
    participant UI as Dashboard

    loop Every 30 seconds
        TTL->>DB: Check for expired services
        DB-->>TTL: List of expired services
        
        loop For each expired service
            TTL->>mDNS: Stop mDNS announcement
            TTL->>DB: Remove service from registry
            TTL->>WS: Broadcast service removed
            WS->>UI: WebSocket: service deregistered
        end
        
        Note over TTL,UI: Services ohne Heartbeat werden automatisch entfernt
    end
```

## 🌐 API Endpoints

### Service Management
- `POST /api/v1/services/register` - Service registrieren (mit TTL)
- `PUT /api/v1/services/{service_id}/heartbeat` - TTL verlängern (Heartbeat)
- `PUT /api/v1/services/{service_id}` - Service aktualisieren
- `DELETE /api/v1/services/{service_id}` - Service deregistrieren
- `GET /api/v1/services/{service_id}` - Service Details

### Discovery
- **mDNS/Bonjour**: Automatische Service-Ankündigung (Hauptmethode)
- `GET /api/v1/services/discover` - Services entdecken (Legacy/Backup)
- `GET /api/v1/services/types` - Verfügbare Service-Typen
- `GET /api/v1/services/tags` - Verfügbare Tags

### Monitoring & Status
- `GET /api/v1/health` - Beacon Health Status
- `GET /api/v1/services/{service_id}/status` - Service Status & TTL Info
- `GET /api/v1/services/expired` - Liste abgelaufener Services

### WebSocket
- `WS /api/v1/ws` - Real-time Updates

## 🚀 Deployment

### Umbrel Integration Standards
Basierend auf erfolgreichen Bitsperity Apps (bitsperity-mongodb, bitsperity-mongodb-mcp):

#### **umbrel-app.yml Manifest**
```yaml
manifestVersion: 1
id: "bitsperity-beacon"
name: "Bitsperity Beacon"
tagline: "Service Discovery Server für das lokale Netzwerk"
icon: "https://raw.githubusercontent.com/bitsperity/bitsperity_apps/master/bitsperity-beacon/applogo.svg"
category: "networking"
version: "1.0.0"
port: 8080
description: >-
  Bitsperity Beacon ist ein zentraler Service Discovery Server mit mDNS/Bonjour-Unterstützung.
  Ermöglicht es Services im lokalen Netzwerk, sich zu registrieren und von anderen Geräten 
  gefunden zu werden. Perfekt für IoT-Geräte, Microservices und verteilte Anwendungen.
  
  Features:
  • mDNS/Bonjour Service Discovery
  • TTL-basierte Service-Verwaltung
  • Real-time Web Dashboard
  • REST API + WebSocket
  • Automatische Service-Cleanup
  • Netzwerk-agnostisch (funktioniert über Umbrel hinaus)

developer: "Bitsperity"
website: "https://bitsperity.com"
submitter: "Bitsperity"
submission: "https://github.com/bitsperity/bitsperity_apps"
repo: "https://github.com/bitsperity/bitsperity_apps"
support: "https://github.com/bitsperity/bitsperity_apps/issues"
gallery:
  - https://raw.githubusercontent.com/bitsperity/bitsperity_apps/master/bitsperity-beacon/gallery/1.png
  - https://raw.githubusercontent.com/bitsperity/bitsperity_apps/master/bitsperity-beacon/gallery/2.png
  - https://raw.githubusercontent.com/bitsperity/bitsperity_apps/master/bitsperity-beacon/gallery/3.png
releaseNotes: "Initial release: mDNS Service Discovery Server mit Web Dashboard"
dependencies: ["bitsperity-mongodb"]
path: ""
defaultUsername: ""
defaultPassword: ""
```

#### **docker-compose.yml Standards**
```yaml
services:
  beacon-api:
    image: bitsperity/beacon:latest
    container_name: bitsperity-beacon-api
    restart: unless-stopped
    stop_grace_period: 30s
    network_mode: host  # Für mDNS Multicast erforderlich
    volumes:
      - ${APP_DATA_DIR:-./data}/data:/app/data
      - ${APP_DATA_DIR:-./data}/logs:/app/logs
    environment:
      # Beacon Configuration
      BEACON_PORT: ${BEACON_PORT:-8080}
      BEACON_MONGODB_URL: ${BEACON_MONGODB_URL:-mongodb://umbrel:umbrel@bitsperity-mongodb:27017/beacon}
      BEACON_LOG_LEVEL: ${LOG_LEVEL:-INFO}
      BEACON_TTL_CLEANUP_INTERVAL: ${TTL_CLEANUP_INTERVAL:-30}
      BEACON_DEFAULT_TTL: ${DEFAULT_TTL:-300}
      
      # mDNS Configuration
      MDNS_DOMAIN: ${MDNS_DOMAIN:-local}
      MDNS_INTERFACE: ${MDNS_INTERFACE:-}
      
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
        reservations:
          memory: 128M
          cpus: '0.25'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  beacon-web:
    image: bitsperity/beacon:latest
    restart: unless-stopped
    ports:
      - "8080:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8080
      REACT_APP_WS_URL: ws://localhost:8080
    command: ["npm", "start"]
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.3'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Umbrel Best Practices (aus bestehenden Apps gelernt)

#### **1. Resource Management**
- **Memory Limits**: 256M für Backend, 128M für Frontend
- **CPU Limits**: 0.5 cores für Backend, 0.3 für Frontend
- **Graceful Shutdown**: `stop_grace_period: 30s`

#### **2. Health Checks**
- **Interval**: 30s (Standard bei Bitsperity Apps)
- **Timeout**: 10s
- **Retries**: 3
- **Start Period**: 30s für Backend-Services

#### **3. Networking**
- **network_mode: host** für mDNS (Multicast erforderlich)
- **Port Mapping**: Explizite Ports für Web-Interface
- **Service Communication**: Über Docker service names

#### **4. Data Persistence**
- **Volume Mapping**: `${APP_DATA_DIR:-./data}` Pattern
- **Separate Volumes**: `/data` und `/logs`
- **MongoDB Database**: Verbindung zu bitsperity-mongodb App

#### **5. Environment Configuration**
- **Configurable Defaults**: `${VAR:-default}` Pattern
- **Logical Grouping**: Beacon, mDNS, Logging sections
- **Security**: Keine hardcoded Credentials

#### **6. Deployment Scripts (aus bitsperity-mongodb-mcp)**
- **deploy-local.sh**: Lokales Testing und Development
- **deploy-github.sh**: GitHub Container Registry Deployment
- **deploy-dockerhub.sh**: Docker Hub Deployment
- **Automated CI/CD**: GitHub Actions für automatische Builds

#### **7. App Assets**
- **applogo.svg**: Vektorgrafik für Umbrel Store (wie bei mongodb-mcp)
- **applogo.png**: Fallback PNG Version
- **gallery/**: Screenshots für Umbrel Store (3 Bilder Standard)
- **Consistent Branding**: Bitsperity Design Language

#### **8. Dockerfile Best Practices**
```dockerfile
# Multi-stage Build (wie bei mongodb-mcp)
FROM python:3.11-slim as backend-builder
# ... Backend Build

FROM node:18-alpine as frontend-builder  
# ... Frontend Build

FROM python:3.11-slim as runtime
# ... Final Runtime Image
```

### Environment Variables
- `BEACON_PORT`: API Server Port (default: 8080)
- `BEACON_MONGODB_URL`: MongoDB Connection String (default: mongodb://umbrel:umbrel@bitsperity-mongodb:27017/beacon)
- `BEACON_LOG_LEVEL`: Logging Level (default: INFO)
- `BEACON_TTL_CLEANUP_INTERVAL`: TTL Cleanup Interval in Sekunden (default: 30)
- `BEACON_DEFAULT_TTL`: Default Service TTL in Sekunden (default: 300)
- `MDNS_DOMAIN`: mDNS Domain (default: local)
- `MDNS_INTERFACE`: Network Interface für mDNS (default: auto)

## 🔧 Integration Examples

### MongoDB Integration Example
```python
# MongoDB Service Model (using Motor async driver)
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import uuid

class ServiceRepository:
    def __init__(self, mongodb_url: str):
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client.beacon
        self.services = self.db.services
    
    async def register_service(self, service_data: dict):
        service = {
            "_id": str(uuid.uuid4()),
            "service_id": str(uuid.uuid4()),
            "name": service_data["name"],
            "type": service_data["type"],
            "host": service_data["host"],
            "port": service_data["port"],
            "protocol": service_data.get("protocol", "http"),
            "tags": service_data.get("tags", []),
            "metadata": service_data.get("metadata", {}),
            "ttl": service_data.get("ttl", 300),
            "expires_at": datetime.utcnow() + timedelta(seconds=service_data.get("ttl", 300)),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_heartbeat": datetime.utcnow()
        }
        
        result = await self.services.insert_one(service)
        return service
    
    async def find_services_by_type(self, service_type: str):
        cursor = self.services.find({
            "type": service_type,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        return await cursor.to_list(length=100)
    
    async def extend_ttl(self, service_id: str, ttl: int = 300):
        await self.services.update_one(
            {"service_id": service_id},
            {
                "$set": {
                    "expires_at": datetime.utcnow() + timedelta(seconds=ttl),
                    "last_heartbeat": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def cleanup_expired_services(self):
        result = await self.services.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        return result.deleted_count
```

### HomegrowClient Registration
```python
import requests

def register_with_beacon():
    service_data = {
        "name": "homegrow-client",
        "type": "iot",
        "host": "192.168.1.100",
        "port": 8080,
        "protocol": "http",
        "tags": ["iot", "agriculture", "sensors"],
        "metadata": {
            "version": "1.0.0",
            "description": "HomegrowClient für Pflanzenüberwachung"
        },
        "ttl": 300  # 5 Minuten TTL
    }
    
    response = requests.post(
        "http://beacon.local/api/v1/services/register",
        json=service_data
    )
    
    service_info = response.json()
    service_id = service_info["service_id"]
    
    # Heartbeat alle 60 Sekunden senden
    def send_heartbeat():
        while True:
            time.sleep(60)
            requests.put(f"http://beacon.local/api/v1/services/{service_id}/heartbeat")
    
    threading.Thread(target=send_heartbeat, daemon=True).start()
    return service_info
```

### Arduino Service Discovery (mDNS)
```cpp
#include <WiFi.h>
#include <ESPmDNS.h>

String discoverMQTTBroker() {
    // mDNS Query für MQTT Service
    int n = MDNS.queryService("mqtt", "tcp");
    
    if (n > 0) {
        // Ersten verfügbaren MQTT Service nehmen
        String host = MDNS.hostname(0);
        int port = MDNS.port(0);
        
        // Optional: TXT Records für Metadaten lesen
        String version = MDNS.txt(0, "version");
        String description = MDNS.txt(0, "description");
        
        return host + ":" + String(port);
    }
    return "";
}

void setup() {
    WiFi.begin("SSID", "PASSWORD");
    while (WiFi.status() != WL_CONNECTED) delay(1000);
    
    // mDNS initialisieren
    if (!MDNS.begin("arduino-client")) {
        Serial.println("Error setting up MDNS responder!");
    }
}
```

## 📊 Monitoring & Observability

### Metrics
- Anzahl registrierter Services
- Service Health Status Distribution
- API Request Latency
- WebSocket Connection Count
- Health Check Success Rate

### Logging
- Strukturierte JSON Logs
- Service Registration/Deregistration Events
- Health Check Results
- API Access Logs
- Error Tracking

### Alerts
- Service Down Notifications
- High API Latency Warnings
- Database Connection Issues
- Memory/CPU Usage Alerts

---

**Bitsperity Beacon** macht Service Discovery im lokalen Netzwerk einfach und zuverlässig. Durch die Integration als Umbrel App wird es nahtlos in das Bitsperity-Ökosystem integriert und bietet eine zentrale Anlaufstelle für alle Services. 