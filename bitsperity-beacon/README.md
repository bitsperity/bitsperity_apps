# Bitsperity Beacon - Service Discovery Server

**Bitsperity Beacon** is a comprehensive service discovery server implemented as an Umbrel app. It provides automatic service registration and discovery for local network services using mDNS/Bonjour protocol, combined with a powerful REST API and real-time WebSocket updates.

## 🎯 Key Features

- **mDNS/Bonjour Service Discovery** - Automatic service announcement via Zeroconf
- **TTL-based Service Management** - Automatic cleanup of expired services with heartbeat system
- **Real-time Web Dashboard** - Live service monitoring with WebSocket updates
- **Comprehensive REST API** - Full CRUD operations for service management
- **MongoDB Integration** - Persistent storage using bitsperity-mongodb backend
- **Docker-native** - Containerized deployment as Umbrel app
- **Network Health Monitoring** - Service health checks and status tracking

## 🏗️ System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React Dashboard]
        WS[WebSocket Client]
    end
    
    subgraph "API Layer"
        API[FastAPI Server]
        WSM[WebSocket Manager]
        CORS[CORS Middleware]
    end
    
    subgraph "Core Services"
        SR[Service Registry]
        TM[TTL Manager]
        MS[mDNS Server]
        HC[Health Checker]
    end
    
    subgraph "Data Layer"
        DB[(MongoDB)]
        CACHE[Service Cache]
    end
    
    subgraph "Network Layer"
        MDNS[mDNS Broadcasts]
        CLIENTS[Service Clients]
    end
    
    UI --> API
    WS --> WSM
    API --> SR
    API --> MS
    WSM --> SR
    SR --> DB
    SR --> CACHE
    TM --> SR
    TM --> MS
    MS --> MDNS
    CLIENTS --> MDNS
    HC --> CLIENTS
```

### Service Registration Flow

```mermaid
sequenceDiagram
    participant Client as Service Client
    participant API as REST API
    participant SR as Service Registry
    participant DB as MongoDB
    participant mDNS as mDNS Server
    participant WSM as WebSocket Manager
    participant Network as Local Network
    
    Client->>API: POST /api/v1/services/register
    API->>SR: register_service(service_data)
    SR->>DB: store service document
    SR->>mDNS: register_service(service)
    mDNS->>Network: broadcast service via mDNS
    SR-->>API: return service object
    API->>WSM: broadcast_service_registered
    WSM->>Network: notify WebSocket clients
    API-->>Client: return service details
    
    loop Heartbeat Loop
        Client->>API: PUT /api/v1/services/{id}/heartbeat
        API->>SR: extend_service_ttl(service_id)
        SR->>DB: update expires_at timestamp
    end
```

### mDNS Discovery Process

```mermaid
sequenceDiagram
    participant Client as Client Device
    participant mDNS as mDNS Network
    participant Beacon as Beacon mDNS
    participant Registry as Service Registry
    
    Client->>mDNS: Query _mqtt._tcp.local
    mDNS->>Beacon: mDNS Query
    Beacon->>Registry: lookup registered services
    Registry-->>Beacon: service details
    Beacon->>mDNS: mDNS Response (SRV + TXT records)
    mDNS-->>Client: Service Info + Metadata
    Client->>Client: Connect to discovered service
```

## 📊 Database Schema

### Service Document Structure

```mermaid
erDiagram
    SERVICE {
        string service_id PK
        string name
        string type
        string host
        int port
        string protocol
        array tags
        object metadata
        int ttl
        datetime expires_at
        datetime last_heartbeat
        enum status
        string health_check_url
        int health_check_interval
        string mdns_service_type
        object mdns_txt_records
        datetime created_at
        datetime updated_at
    }
    
    HEALTH_CHECK {
        string service_id FK
        datetime timestamp
        enum status
        int response_time_ms
        string error_message
    }
    
    SERVICE ||--o{ HEALTH_CHECK : monitors
```

## 🔧 Core Components

### Service Registry Class Architecture

```mermaid
classDiagram
    class ServiceRegistry {
        -Database database
        -MDNSServerBase mdns_server
        -Dict[str, Service] _services_cache
        -int _cache_ttl
        +register_service(ServiceCreate) Service
        +get_service_by_id(str) Optional[Service]
        +update_service(str, ServiceUpdate) Optional[Service]
        +extend_service_ttl(str, int) Optional[Service]
        +deregister_service(str) bool
        +discover_services(...) List[Service]
        +cleanup_expired_services() int
    }
    
    class Service {
        +str service_id
        +str name
        +str type
        +str host
        +int port
        +str protocol
        +List[str] tags
        +Dict[str, str] metadata
        +int ttl
        +datetime expires_at
        +ServiceStatus status
        +is_expired() bool
        +extend_ttl(int) None
        +get_mdns_txt_records() Dict[str, str]
    }
    
    class MDNSServer {
        -AsyncZeroconf zeroconf
        -Dict[str, ServiceInfo] registered_services
        +register_service(Service) bool
        +unregister_service(str) bool
        +update_service(Service) bool
        -_get_local_ip() str
    }
    
    class TTLManager {
        -ServiceRegistry registry
        -int cleanup_interval
        +start() None
        +stop() None
        -_cleanup_loop() None
    }
    
    ServiceRegistry --> Service
    ServiceRegistry --> MDNSServer
    ServiceRegistry --> TTLManager
```

## 🚀 API Documentation

### Service Management Endpoints

#### POST /api/v1/services/register
Register a new service with automatic mDNS announcement.

**Request Body:**
```json
{
  "name": "homegrow-client",
  "type": "iot",
  "host": "192.168.1.100",
  "port": 8080,
  "protocol": "http",
  "tags": ["iot", "agriculture", "sensors"],
  "metadata": {
    "version": "1.0.0",
    "description": "HomegrowClient for plant monitoring"
  },
  "ttl": 300,
  "health_check_url": "http://192.168.1.100:8080/health",
  "health_check_interval": 60
}
```

**Response:**
```json
{
  "service_id": "12345678-1234-1234-1234-123456789012",
  "name": "homegrow-client",
  "type": "iot",
  "host": "192.168.1.100",
  "port": 8080,
  "protocol": "http",
  "tags": ["iot", "agriculture", "sensors"],
  "metadata": {
    "version": "1.0.0",
    "description": "HomegrowClient for plant monitoring"
  },
  "status": "active",
  "ttl": 300,
  "expires_at": "2024-01-01T12:05:00Z",
  "last_heartbeat": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "mdns_service_type": "_iot._tcp"
}
```

#### PUT /api/v1/services/{service_id}/heartbeat
Extend service TTL (keep-alive mechanism).

**Query Parameters:**
- `ttl` (optional): Custom TTL in seconds

**Response:**
```json
{
  "service_id": "12345678-1234-1234-1234-123456789012",
  "status": "active",
  "expires_at": "2024-01-01T12:10:00Z",
  "last_heartbeat": "2024-01-01T12:05:00Z",
  "message": "Heartbeat received successfully"
}
```

#### GET /api/v1/services
List and filter registered services.

**Query Parameters:**
- `type`: Filter by service type
- `tags`: Filter by tags (array)
- `protocol`: Filter by protocol
- `status`: Filter by status (active, inactive, expired, unhealthy)
- `limit`: Results limit (1-100, default: 50)
- `skip`: Results offset (default: 0)

#### GET /api/v1/services/{service_id}
Get detailed service information.

#### PUT /api/v1/services/{service_id}
Update service configuration.

#### DELETE /api/v1/services/{service_id}
Deregister service (removes from mDNS and database).

### Discovery Endpoints

#### GET /api/v1/services/discover
Legacy HTTP-based service discovery (backup to mDNS).

#### GET /api/v1/services/types
Get all available service types.

#### GET /api/v1/services/tags  
Get all available service tags.

#### GET /api/v1/services/expired
Get list of expired services.

### Health & Monitoring

#### GET /api/v1/health
Beacon health status and system metrics.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "services": {
    "total": 15,
    "active": 12,
    "expired": 2,
    "unhealthy": 1
  },
  "mdns": {
    "running": true,
    "registered_services": 12
  },
  "database": {
    "connected": true,
    "ping_ms": 2
  }
}
```

#### WebSocket: /api/v1/ws
Real-time service updates via WebSocket.

**Message Types:**
- `service_registered`: New service registered
- `service_updated`: Service configuration changed  
- `service_deregistered`: Service removed
- `service_expired`: Service TTL expired
- `health_status_changed`: Service health status changed

## 📡 mDNS Integration Deep Dive

### Service Type Mappings

Beacon automatically maps service types to standard mDNS service types:

| Service Type | mDNS Type | Description |
|--------------|-----------|-------------|
| `mqtt` | `_mqtt._tcp.local` | MQTT Brokers |
| `http` | `_http._tcp.local` | HTTP Services |
| `https` | `_https._tcp.local` | HTTPS Services |
| `iot` | `_iot._tcp.local` | IoT Devices |
| `api` | `_http._tcp.local` | REST APIs |
| `database` | `_db._tcp.local` | Database Services |
| `cache` | `_cache._tcp.local` | Cache Services |
| `message_queue` | `_mq._tcp.local` | Message Queues |

### TXT Record Structure

Each mDNS service includes comprehensive TXT records:

```
service_id=12345678-1234-1234-1234-123456789012
name=homegrow-client
type=iot
protocol=http
version=1.0.0
tags=iot,agriculture,sensors
description=HomegrowClient for plant monitoring
```

### mDNS Query Examples

**Query MQTT Brokers:**
```bash
# Using avahi-browse
avahi-browse -r _mqtt._tcp

# Using dns-sd
dns-sd -B _mqtt._tcp

# Using Python zeroconf
import zeroconf
browser = zeroconf.ServiceBrowser(zc, "_mqtt._tcp.local.", handlers=[handler])
```

**Query IoT Devices:**
```bash
avahi-browse -r _iot._tcp
```

## 💾 Data Models

### Service Model Definition

```python
class Service(BaseModel):
    # Identity
    service_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    
    # Network Configuration
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    protocol: str = Field(default="http", max_length=20)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    # TTL Management
    ttl: int = Field(default=300, ge=10, le=86400)  # 10s to 24h
    expires_at: datetime = Field(default=None)
    last_heartbeat: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Status & Health
    status: ServiceStatus = Field(default=ServiceStatus.ACTIVE)
    health_check_url: Optional[str] = None
    health_check_interval: Optional[int] = Field(default=60, ge=30, le=3600)
    
    # mDNS Configuration
    mdns_service_type: Optional[str] = None
    mdns_txt_records: Dict[str, str] = Field(default_factory=dict)
```

### Service Status Enum

```python
class ServiceStatus(str, Enum):
    ACTIVE = "active"         # Service is running and healthy
    INACTIVE = "inactive"     # Service is registered but not responding
    EXPIRED = "expired"       # Service TTL has expired
    UNHEALTHY = "unhealthy"   # Service health check is failing
```

## 🔄 TTL & Heartbeat System

### TTL Management Flow

```mermaid
stateDiagram-v2
    [*] --> Registered
    Registered --> Active : TTL valid
    Active --> Active : Heartbeat received
    Active --> Expired : TTL expires
    Expired --> [*] : Cleanup
    Active --> Unhealthy : Health check fails
    Unhealthy --> Active : Health restored
    Unhealthy --> Expired : TTL expires
```

### Heartbeat Implementation

**Client-side Example:**
```python
import asyncio
import aiohttp

class BeaconClient:
    def __init__(self, beacon_url: str):
        self.beacon_url = beacon_url
        self.service_id = None
        self.heartbeat_task = None
    
    async def register(self, service_data: dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.beacon_url}/api/v1/services/register",
                json=service_data
            ) as response:
                result = await response.json()
                self.service_id = result["service_id"]
                return result
    
    async def start_heartbeat(self, interval: int = 60):
        """Start automatic heartbeat every interval seconds"""
        self.heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(interval)
        )
    
    async def _heartbeat_loop(self, interval: int):
        while True:
            try:
                await asyncio.sleep(interval)
                await self.send_heartbeat()
            except Exception as e:
                print(f"Heartbeat failed: {e}")
    
    async def send_heartbeat(self):
        if not self.service_id:
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{self.beacon_url}/api/v1/services/{self.service_id}/heartbeat"
            ) as response:
                return await response.json()
```

## 🧪 Integration Examples

### Arduino/ESP32 mDNS Discovery

```cpp
#include <WiFi.h>
#include <ESPmDNS.h>
#include <HTTPClient.h>

class BeaconClient {
private:
    String beacon_host = "";
    int beacon_port = 8080;
    String service_id = "";
    unsigned long last_heartbeat = 0;
    const unsigned long heartbeat_interval = 60000; // 60 seconds

public:
    void begin() {
        // Discover Beacon via mDNS
        discoverBeacon();
        
        // Register this device
        registerService();
    }
    
    void loop() {
        // Send heartbeat if needed
        if (millis() - last_heartbeat > heartbeat_interval) {
            sendHeartbeat();
            last_heartbeat = millis();
        }
    }
    
private:
    void discoverBeacon() {
        Serial.println("Discovering Beacon via mDNS...");
        
        int n = MDNS.queryService("beacon", "tcp");
        if (n > 0) {
            beacon_host = MDNS.hostname(0);
            beacon_port = MDNS.port(0);
            Serial.printf("Found Beacon: %s:%d\n", beacon_host.c_str(), beacon_port);
        }
    }
    
    void registerService() {
        if (beacon_host.length() == 0) return;
        
        HTTPClient http;
        http.begin("http://" + beacon_host + ":" + beacon_port + "/api/v1/services/register");
        http.addHeader("Content-Type", "application/json");
        
        String json = R"({
            "name": "esp32-sensor",
            "type": "iot",
            "host": ")" + WiFi.localIP().toString() + R"(",
            "port": 80,
            "protocol": "http",
            "tags": ["sensor", "temperature", "humidity"],
            "metadata": {
                "device": "ESP32",
                "firmware": "1.0.0"
            },
            "ttl": 300
        })";
        
        int httpCode = http.POST(json);
        if (httpCode == 201) {
            String response = http.getString();
            // Parse service_id from response
            Serial.println("Service registered successfully");
        }
        
        http.end();
    }
    
    void sendHeartbeat() {
        if (service_id.length() == 0 || beacon_host.length() == 0) return;
        
        HTTPClient http;
        http.begin("http://" + beacon_host + ":" + beacon_port + "/api/v1/services/" + service_id + "/heartbeat");
        
        int httpCode = http.PUT("");
        if (httpCode == 200) {
            Serial.println("Heartbeat sent successfully");
        }
        
        http.end();
    }
};
```

### Python Service Integration

```python
import asyncio
import aiohttp
from contextlib import asynccontextmanager

class ServiceWithBeacon:
    def __init__(self, service_config: dict, beacon_url: str = "http://beacon.local:8080"):
        self.config = service_config
        self.beacon_url = beacon_url
        self.beacon_client = BeaconClient(beacon_url)
        self.service_id = None
    
    @asynccontextmanager
    async def lifespan(self):
        """Service lifespan manager with automatic Beacon integration"""
        try:
            # Register with Beacon
            result = await self.beacon_client.register(self.config)
            self.service_id = result["service_id"]
            
            # Start heartbeat
            await self.beacon_client.start_heartbeat()
            
            print(f"Service registered with Beacon: {self.service_id}")
            yield
            
        finally:
            # Cleanup on shutdown
            if self.service_id:
                await self.beacon_client.deregister(self.service_id)
                print("Service deregistered from Beacon")

# Usage
async def main():
    service_config = {
        "name": "my-microservice",
        "type": "api",
        "host": "192.168.1.50",
        "port": 8000,
        "protocol": "http",
        "tags": ["microservice", "api", "backend"],
        "metadata": {
            "version": "2.1.0",
            "environment": "production"
        },
        "ttl": 300,
        "health_check_url": "http://192.168.1.50:8000/health"
    }
    
    service = ServiceWithBeacon(service_config)
    
    async with service.lifespan():
        # Your service logic here
        await asyncio.sleep(3600)  # Run for 1 hour

if __name__ == "__main__":
    asyncio.run(main())
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BEACON_PORT` | `8080` | API server port |
| `BEACON_MONGODB_URL` | `mongodb://umbrel:umbrel@bitsperity-mongodb:27017/beacon` | MongoDB connection string |
| `BEACON_TTL_CLEANUP_INTERVAL` | `30` | TTL cleanup interval (seconds) |
| `BEACON_DEFAULT_TTL` | `300` | Default service TTL (seconds) |
| `MDNS_DOMAIN` | `local` | mDNS domain suffix |
| `MDNS_INTERFACE` | auto | Network interface for mDNS |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `LOG_LEVEL` | `INFO` | Logging level |

### Docker Compose Configuration

```yaml
version: '3.8'
services:
  bitsperity-beacon:
    image: bitsperity/beacon:latest
    container_name: bitsperity-beacon
    network_mode: host  # Required for mDNS
    environment:
      - BEACON_MONGODB_URL=mongodb://umbrel:umbrel@bitsperity-mongodb:27017/beacon
      - BEACON_PORT=8080
      - MDNS_DOMAIN=local
    depends_on:
      - bitsperity-mongodb
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

## 🔍 Monitoring & Observability

### System Metrics

The health endpoint provides comprehensive system metrics:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "total": 25,
    "active": 20,
    "inactive": 2,
    "expired": 2,
    "unhealthy": 1
  },
  "mdns": {
    "running": true,
    "registered_services": 20,
    "domain": "local"
  },
  "database": {
    "connected": true,
    "ping_ms": 3,
    "collections": {
      "services": 25,
      "health_checks": 150
    }
  },
  "memory": {
    "used_mb": 128,
    "cache_size": 25
  },
  "network": {
    "local_ip": "192.168.1.10",
    "interface": "eth0"
  }
}
```

### Structured Logging

Beacon uses structured JSON logging for easy parsing:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "app.core.service_registry",
  "message": "Service registered",
  "service_id": "12345678-1234-1234-1234-123456789012",
  "name": "homegrow-client",
  "type": "iot",
  "host": "192.168.1.100",
  "port": 8080,
  "expires_at": "2024-01-01T12:05:00Z"
}
```

## 🐛 Troubleshooting

### Common Issues

**1. mDNS not working**
```bash
# Check network mode
docker inspect bitsperity-beacon | grep NetworkMode
# Should be "host"

# Test mDNS manually
avahi-browse -a
```

**2. MongoDB connection failed**
```bash
# Check MongoDB status
umbrel app logs bitsperity-mongodb

# Test connection
docker exec bitsperity-beacon python -c "
import asyncio
from app.database import database
asyncio.run(database.test_connection())
"
```

**3. Services not discovered**
```bash
# Check service TTL status
curl http://localhost:8080/api/v1/services/expired

# Check mDNS registration
curl http://localhost:8080/api/v1/health
```

**4. High memory usage**
```bash
# Check service cache size
curl http://localhost:8080/api/v1/health | jq '.memory'

# Clear expired services manually
curl -X DELETE http://localhost:8080/api/v1/services/cleanup
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
docker run -e LOG_LEVEL=DEBUG bitsperity/beacon:latest
```

### Log Analysis

```bash
# Follow live logs
docker logs -f bitsperity-beacon

# Filter service registration events
docker logs bitsperity-beacon | grep "Service registered"

# Check mDNS events
docker logs bitsperity-beacon | grep "mDNS"
```

## 🚧 Development Roadmap

### Phase 1: Core Features ✅
- [x] Basic service registration and discovery
- [x] mDNS/Bonjour integration
- [x] TTL-based lifecycle management
- [x] REST API with OpenAPI documentation
- [x] Real-time WebSocket updates
- [x] MongoDB persistence

### Phase 2: Enhanced Monitoring 🔄
- [ ] **Service Health Checks** - Automated health monitoring
- [ ] **Performance Metrics** - Service response time tracking
- [ ] **Alert System** - Notifications for service failures
- [ ] **Dashboard Analytics** - Usage statistics and trends

### Phase 3: Advanced Features 🔮
- [ ] **Service Groups** - Logical service grouping and dependencies
- [ ] **Load Balancing** - Service load distribution information
- [ ] **API Gateway Integration** - Automatic service routing
- [ ] **Service Mesh** - Advanced networking features

### Phase 4: Enterprise Features 🏢
- [ ] **Authentication & Authorization** - Multi-tenant support
- [ ] **Rate Limiting** - API quota management  
- [ ] **Audit Logging** - Compliance and security logging
- [ ] **High Availability** - Clustering and failover

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/bitsperity/bitsperity_apps.git
cd bitsperity_apps/bitsperity-beacon

# Setup environment
cp env.example .env
# Edit .env with your configuration

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Run tests
docker-compose exec backend python -m pytest
docker-compose exec frontend npm test
```

### Code Style

- **Backend**: Follow PEP 8, use Black formatter
- **Frontend**: Use Prettier, follow React best practices
- **Documentation**: Use clear, concise language with examples

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Umbrel** - For the excellent self-hosting platform
- **FastAPI** - For the modern Python web framework
- **Zeroconf** - For the mDNS/Bonjour implementation
- **React** - For the frontend framework
- **MongoDB** - For the document database

---

**Bitsperity Beacon** - Making service discovery in local networks simple and reliable! 🚀

For more information, visit our [documentation](https://docs.bitsperity.com/beacon) or join our [community](https://community.bitsperity.com). 