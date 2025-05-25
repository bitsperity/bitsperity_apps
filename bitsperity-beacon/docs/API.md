# Bitsperity Beacon API Documentation

## Überblick

Die Bitsperity Beacon API bietet vollständige REST-Endpoints für Service Discovery und Management. Zusätzlich zur REST API unterstützt Beacon mDNS/Bonjour für automatische Service-Ankündigung und WebSocket für Real-time Updates.

**Base URL:** `http://beacon.local:8080/api/v1`

## Authentication

Aktuell ist keine Authentifizierung erforderlich. Die API ist für den Einsatz in vertrauenswürdigen lokalen Netzwerken konzipiert.

## Service Management

### Service registrieren

**POST** `/services/register`

Registriert einen neuen Service im Beacon.

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
    "description": "HomegrowClient für Pflanzenüberwachung"
  },
  "ttl": 300,
  "health_check_url": "http://192.168.1.100:8080/health",
  "health_check_interval": 60
}
```

**Response (201 Created):**
```json
{
  "service_id": "123e4567-e89b-12d3-a456-426614174000",
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
  "status": "active",
  "ttl": 300,
  "expires_at": "2024-01-01T12:05:00Z",
  "last_heartbeat": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "health_check_url": "http://192.168.1.100:8080/health",
  "health_check_interval": 60,
  "mdns_service_type": "_iot._tcp"
}
```

### Service Details abrufen

**GET** `/services/{service_id}`

```bash
curl http://beacon.local:8080/api/v1/services/123e4567-e89b-12d3-a456-426614174000
```

### Service aktualisieren

**PUT** `/services/{service_id}`

```json
{
  "name": "homegrow-client-v2",
  "metadata": {
    "version": "2.0.0"
  }
}
```

### Service Heartbeat (TTL verlängern)

**PUT** `/services/{service_id}/heartbeat`

Optional mit TTL Parameter:
```bash
curl -X PUT http://beacon.local:8080/api/v1/services/123e4567-e89b-12d3-a456-426614174000/heartbeat?ttl=600
```

**Response:**
```json
{
  "service_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "expires_at": "2024-01-01T12:10:00Z",
  "last_heartbeat": "2024-01-01T12:05:00Z",
  "message": "Heartbeat received successfully"
}
```

### Service deregistrieren

**DELETE** `/services/{service_id}`

```bash
curl -X DELETE http://beacon.local:8080/api/v1/services/123e4567-e89b-12d3-a456-426614174000
```

## Service Discovery

### Services auflisten

**GET** `/services`

Query Parameter:
- `type` - Filter by service type
- `tags` - Filter by tags (multiple)
- `protocol` - Filter by protocol
- `status` - Filter by status
- `limit` - Limit results (default: 50)
- `skip` - Skip results (default: 0)

```bash
curl "http://beacon.local:8080/api/v1/services?type=iot&status=active&limit=10"
```

**Response:**
```json
{
  "services": [...],
  "total": 5,
  "page": 1,
  "page_size": 10
}
```

### Services entdecken (Legacy API)

**GET** `/services/discover`

Gleiche Parameter wie `/services`, aber mit Discovery-spezifischer Response:

```json
{
  "services": [...],
  "total": 5,
  "filters_applied": {
    "type": "iot",
    "status": "active"
  },
  "discovery_method": "api"
}
```

### Services mit POST Filter entdecken

**POST** `/services/discover`

```json
{
  "type": "iot",
  "tags": ["sensors", "agriculture"],
  "protocol": "http",
  "status": "active"
}
```

## Metadata Endpoints

### Service Types abrufen

**GET** `/services/types`

```json
["iot", "mqtt", "http", "api", "database"]
```

### Service Tags abrufen

**GET** `/services/tags`

```json
["iot", "agriculture", "sensors", "mqtt", "api"]
```

### Abgelaufene Services abrufen

**GET** `/services/expired`

```json
{
  "services": [...],
  "total": 2
}
```

## Health & Monitoring

### Beacon Health Check

**GET** `/health`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "message": "Bitsperity Beacon ist gesund und bereit"
}
```

### Readiness Check

**GET** `/ready`

```json
{
  "status": "ready"
}
```

### Liveness Check

**GET** `/live`

```json
{
  "status": "alive"
}
```

## WebSocket API

### Verbindung herstellen

**WebSocket** `/ws`

Optional mit Client ID:
```javascript
const ws = new WebSocket('ws://beacon.local:8080/api/v1/ws?client_id=my-client')
```

### WebSocket Messages

#### Service Registered
```json
{
  "type": "service_registered",
  "event": "service_registered",
  "data": {
    "service_id": "...",
    "name": "...",
    ...
  },
  "timestamp": 1704110400
}
```

#### Service Updated
```json
{
  "type": "service_updated",
  "event": "service_updated",
  "data": {
    "service_id": "...",
    ...
  },
  "timestamp": 1704110400
}
```

#### Service Deregistered
```json
{
  "type": "service_deregistered",
  "event": "service_deregistered",
  "data": {
    "service_id": "...",
    "service_name": "..."
  },
  "timestamp": 1704110400
}
```

#### Service Heartbeat
```json
{
  "type": "service_heartbeat",
  "event": "service_heartbeat",
  "data": {
    "service_id": "...",
    "expires_at": "2024-01-01T12:10:00Z"
  },
  "timestamp": 1704110400
}
```

#### Services Cleanup
```json
{
  "type": "services_cleanup",
  "event": "services_cleanup",
  "data": {
    "removed_count": 3
  },
  "timestamp": 1704110400
}
```

## mDNS/Bonjour Integration

Beacon kündigt automatisch alle registrierten Services via mDNS an. Services sind dann über Standard mDNS-Queries auffindbar:

### Service Type Mappings

| Service Type | mDNS Type | Beschreibung |
|--------------|-----------|--------------|
| `mqtt` | `_mqtt._tcp.local` | MQTT Broker |
| `http` | `_http._tcp.local` | HTTP Services |
| `https` | `_https._tcp.local` | HTTPS Services |
| `iot` | `_iot._tcp.local` | IoT Devices |
| `api` | `_http._tcp.local` | REST APIs |
| `database` | `_db._tcp.local` | Datenbanken |

### mDNS Discovery (Arduino/ESP32)

```cpp
#include <ESPmDNS.h>

// Suche nach MQTT Services
int n = MDNS.queryService("mqtt", "tcp");
if (n > 0) {
    String host = MDNS.hostname(0);
    int port = MDNS.port(0);
    // TXT Records lesen
    String version = MDNS.txt(0, "version");
}
```

### mDNS Discovery (Python)

```python
from zeroconf import ServiceBrowser, Zeroconf

class ServiceListener:
    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print(f"Service: {info.server}:{info.port}")

zeroconf = Zeroconf()
listener = ServiceListener()
browser = ServiceBrowser(zeroconf, "_iot._tcp.local.", listener)
```

## Error Handling

### Standard Error Response

```json
{
  "detail": "Service nicht gefunden"
}
```

### HTTP Status Codes

- `200` - OK
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error
- `503` - Service Unavailable

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "port"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": {"limit_value": 0}
    }
  ]
}
```

## Rate Limiting

Aktuell ist kein Rate Limiting implementiert. Für Produktionsumgebungen sollte ein Reverse Proxy mit Rate Limiting vorgeschaltet werden.

## Examples

### Python Client

```python
import requests
import time
import threading

class BeaconClient:
    def __init__(self, base_url):
        self.base_url = base_url
        
    def register_service(self, service_data):
        response = requests.post(f"{self.base_url}/services/register", json=service_data)
        return response.json()
        
    def send_heartbeat(self, service_id, ttl=None):
        params = f"?ttl={ttl}" if ttl else ""
        response = requests.put(f"{self.base_url}/services/{service_id}/heartbeat{params}")
        return response.json()
        
    def discover_services(self, **filters):
        response = requests.get(f"{self.base_url}/services/discover", params=filters)
        return response.json()

# Verwendung
beacon = BeaconClient("http://beacon.local:8080/api/v1")
service = beacon.register_service({
    "name": "my-service",
    "type": "iot",
    "host": "192.168.1.100",
    "port": 8080
})

# Automatische Heartbeats
def heartbeat_loop(service_id):
    while True:
        time.sleep(60)
        beacon.send_heartbeat(service_id)

threading.Thread(target=heartbeat_loop, args=[service["service_id"]], daemon=True).start()
```

### JavaScript Client

```javascript
class BeaconClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl
    }
    
    async registerService(serviceData) {
        const response = await fetch(`${this.baseUrl}/services/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(serviceData)
        })
        return response.json()
    }
    
    async sendHeartbeat(serviceId, ttl) {
        const params = ttl ? `?ttl=${ttl}` : ''
        const response = await fetch(`${this.baseUrl}/services/${serviceId}/heartbeat${params}`, {
            method: 'PUT'
        })
        return response.json()
    }
    
    connectWebSocket(onMessage) {
        const ws = new WebSocket(`ws://beacon.local:8080/api/v1/ws`)
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data)
            onMessage(message)
        }
        return ws
    }
}

// Verwendung
const beacon = new BeaconClient('http://beacon.local:8080/api/v1')
const service = await beacon.registerService({
    name: 'my-web-service',
    type: 'http',
    host: '192.168.1.200',
    port: 3000
})

// WebSocket für Live-Updates
const ws = beacon.connectWebSocket((message) => {
    console.log('Service Update:', message)
})
``` 