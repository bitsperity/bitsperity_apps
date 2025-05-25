# Bitsperity Beacon - Service Discovery Server

**Bitsperity Beacon** ist ein zentraler Service Discovery Server, der als Umbrel App implementiert wird. Er ermöglicht es Services im lokalen Netzwerk, sich zu registrieren und von anderen Geräten gefunden zu werden. Die App fungiert als "Leuchtfeuer" (Beacon) für alle Services im Bitsperity-Ökosystem.

## 🎯 Features

- **mDNS/Bonjour Service Discovery** - Automatische Service-Ankündigung im lokalen Netzwerk
- **TTL-basierte Service-Verwaltung** - Automatische Cleanup abgelaufener Services
- **Real-time Web Dashboard** - Live-Updates über WebSocket
- **REST API + WebSocket** - Vollständige API für Service-Management
- **MongoDB Integration** - Nutzt bitsperity-mongodb als Backend
- **Docker-basiert** - Einfache Deployment als Umbrel App

## 🏗️ Architektur

### Backend (FastAPI + Python 3.11)
- **Service Registry** - Zentrale Verwaltung aller Services
- **mDNS Server** - Zeroconf/Bonjour Service Discovery
- **TTL Manager** - Automatische Cleanup-Prozesse
- **WebSocket Manager** - Real-time Updates
- **MongoDB Integration** - Persistente Datenspeicherung

### Frontend (React 18 + TypeScript)
- **Service Dashboard** - Übersicht aller registrierten Services
- **Real-time Updates** - Live-Status über WebSocket
- **Service Registration** - UI für manuelle Service-Registrierung
- **Network Topology** - Visualisierung der Service-Landschaft

## 🚀 Quick Start

### Als Umbrel App

1. **Abhängigkeiten installieren**
   ```bash
   # Installiere zuerst bitsperity-mongodb
   umbrel app install bitsperity-mongodb
   ```

2. **Bitsperity Beacon installieren**
   ```bash
   umbrel app install bitsperity-beacon
   ```

3. **Zugriff auf das Dashboard**
   - Öffne `http://umbrel.local:8080` in deinem Browser
   - API Dokumentation: `http://umbrel.local:8080/api/docs`

### Lokale Entwicklung

1. **Repository klonen**
   ```bash
   git clone https://github.com/bitsperity/bitsperity_apps.git
   cd bitsperity_apps/bitsperity-beacon
   ```

2. **Environment konfigurieren**
   ```bash
   cp env.example .env
   # Bearbeite .env nach Bedarf
   ```

3. **Mit Docker Compose starten**
   ```bash
   docker-compose up -d
   ```

4. **Zugriff**
   - Dashboard: `http://localhost:8080`
   - API: `http://localhost:8080/api/v1`
   - Docs: `http://localhost:8080/api/docs`

## 📡 Service Registration

### REST API

```bash
# Service registrieren
curl -X POST http://localhost:8080/api/v1/services/register \
  -H "Content-Type: application/json" \
  -d '{
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
    "ttl": 300
  }'

# Heartbeat senden (TTL verlängern)
curl -X PUT http://localhost:8080/api/v1/services/{service_id}/heartbeat

# Services entdecken
curl http://localhost:8080/api/v1/services/discover?type=iot
```

### Python Client

```python
import requests
import time
import threading

def register_with_beacon():
    service_data = {
        "name": "my-service",
        "type": "iot",
        "host": "192.168.1.100",
        "port": 8080,
        "ttl": 300
    }
    
    response = requests.post(
        "http://beacon.local:8080/api/v1/services/register",
        json=service_data
    )
    
    service_info = response.json()
    service_id = service_info["service_id"]
    
    # Heartbeat alle 60 Sekunden
    def send_heartbeat():
        while True:
            time.sleep(60)
            requests.put(f"http://beacon.local:8080/api/v1/services/{service_id}/heartbeat")
    
    threading.Thread(target=send_heartbeat, daemon=True).start()
    return service_info
```

### Arduino/ESP32 (mDNS Discovery)

```cpp
#include <WiFi.h>
#include <ESPmDNS.h>

String discoverMQTTBroker() {
    // mDNS Query für MQTT Service
    int n = MDNS.queryService("mqtt", "tcp");
    
    if (n > 0) {
        String host = MDNS.hostname(0);
        int port = MDNS.port(0);
        return host + ":" + String(port);
    }
    return "";
}
```

## 🔧 API Endpoints

### Service Management
- `POST /api/v1/services/register` - Service registrieren
- `PUT /api/v1/services/{id}/heartbeat` - TTL verlängern
- `PUT /api/v1/services/{id}` - Service aktualisieren
- `DELETE /api/v1/services/{id}` - Service deregistrieren
- `GET /api/v1/services/{id}` - Service Details

### Discovery
- **mDNS/Bonjour** - Automatische Service-Ankündigung (Hauptmethode)
- `GET /api/v1/services/discover` - Services entdecken (Legacy/Backup)
- `GET /api/v1/services/types` - Verfügbare Service-Typen
- `GET /api/v1/services/tags` - Verfügbare Tags

### Monitoring
- `GET /api/v1/health` - Beacon Health Status
- `WS /api/v1/ws` - WebSocket für Real-time Updates

## 🌐 mDNS Service Types

Beacon mappt automatisch Service-Typen zu mDNS Service Types:

| Service Type | mDNS Type | Beschreibung |
|--------------|-----------|--------------|
| `mqtt` | `_mqtt._tcp.local` | MQTT Broker |
| `http` | `_http._tcp.local` | HTTP Services |
| `iot` | `_iot._tcp.local` | IoT Devices |
| `api` | `_http._tcp.local` | REST APIs |
| `database` | `_db._tcp.local` | Datenbanken |

## 🔄 TTL & Heartbeat System

Services werden automatisch nach Ablauf ihrer TTL (Time-To-Live) entfernt:

1. **Service registriert sich** mit TTL (z.B. 300 Sekunden)
2. **Beacon setzt Ablaufzeit** für Service
3. **Service sendet Heartbeats** alle 60 Sekunden (optional)
4. **Beacon verlängert TTL** bei jedem Heartbeat
5. **Bei TTL-Ablauf**: Service wird automatisch deregistriert

## 📊 Monitoring & Observability

### Metriken
- Anzahl registrierter Services
- Service Health Status Distribution
- API Request Latency
- WebSocket Connection Count

### Logging
- Strukturierte JSON Logs
- Service Registration/Deregistration Events
- Health Check Results
- API Access Logs

## 🔧 Konfiguration

### Environment Variables

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `BEACON_PORT` | `8080` | API Server Port |
| `BEACON_MONGODB_URL` | `mongodb://umbrel:umbrel@bitsperity-mongodb:27017/beacon` | MongoDB Connection |
| `BEACON_TTL_CLEANUP_INTERVAL` | `30` | TTL Cleanup Interval (Sekunden) |
| `BEACON_DEFAULT_TTL` | `300` | Default Service TTL (Sekunden) |
| `MDNS_DOMAIN` | `local` | mDNS Domain |
| `MDNS_INTERFACE` | auto | Network Interface für mDNS |

## 🧪 Testing

```bash
# Backend Tests
cd backend
python -m pytest

# Frontend Tests
cd frontend
npm test

# Integration Tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📦 Deployment

### Umbrel App Store

Die App wird automatisch über den Umbrel App Store deployed:

```yaml
# umbrel-app.yml
manifestVersion: 1
id: "bitsperity-beacon"
name: "Bitsperity Beacon"
dependencies: ["bitsperity-mongodb"]
```

### Manual Docker Deployment

```bash
# Build Image
docker build -t bitsperity/beacon:latest .

# Run Container
docker run -d \
  --name bitsperity-beacon \
  --network host \
  -e BEACON_MONGODB_URL=mongodb://localhost:27017/beacon \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  bitsperity/beacon:latest
```

## 🤝 Integration Examples

### HomegrowClient Integration

```python
# HomegrowClient registriert sich automatisch
from bitsperity_beacon_client import BeaconClient

beacon = BeaconClient("http://beacon.local:8080")
service_id = beacon.register({
    "name": "homegrow-client",
    "type": "iot",
    "host": "192.168.1.100",
    "port": 8080,
    "tags": ["agriculture", "sensors"]
})

# Automatische Heartbeats
beacon.start_heartbeat(service_id)
```

### MQTT Broker Discovery

```python
# Andere Services finden MQTT Broker automatisch
services = beacon.discover(type="mqtt")
mqtt_broker = services[0]
mqtt_client.connect(mqtt_broker["host"], mqtt_broker["port"])
```

## 🔒 Security

- **Network Isolation**: Läuft im Docker Host Network für mDNS
- **Input Validation**: Alle API Inputs werden validiert
- **Rate Limiting**: Schutz vor API Missbrauch
- **Health Checks**: Kontinuierliche Überwachung

## 📚 Documentation

- **API Docs**: `/api/docs` (Swagger UI)
- **Requirements**: `REQUIREMENTS.md`
- **Examples**: `docs/EXAMPLES.md`
- **Deployment**: `docs/DEPLOYMENT.md`

## 🐛 Troubleshooting

### Häufige Probleme

1. **mDNS funktioniert nicht**
   ```bash
   # Prüfe Network Mode
   docker inspect bitsperity-beacon | grep NetworkMode
   # Sollte "host" sein
   ```

2. **MongoDB Verbindung fehlgeschlagen**
   ```bash
   # Prüfe bitsperity-mongodb Status
   umbrel app logs bitsperity-mongodb
   ```

3. **Services werden nicht gefunden**
   ```bash
   # Prüfe TTL Status
   curl http://localhost:8080/api/v1/services/expired
   ```

### Logs

```bash
# Beacon Logs
umbrel app logs bitsperity-beacon

# Detaillierte Logs
docker exec bitsperity-beacon tail -f /app/logs/beacon.log
```

## 🚧 Roadmap

- [ ] **Health Check System** - Automatische Service Health Checks
- [ ] **Service Groups** - Logische Gruppierung von Services
- [ ] **Load Balancing** - Service Load Balancing Informationen
- [ ] **API Gateway Integration** - Service Routing
- [ ] **Metrics Export** - Prometheus/Grafana Integration
- [ ] **Service Dependencies** - Dependency Management

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature Branch (`git checkout -b feature/amazing-feature`)
3. Commit deine Änderungen (`git commit -m 'Add amazing feature'`)
4. Push zum Branch (`git push origin feature/amazing-feature`)
5. Öffne einen Pull Request

## 📄 License

Dieses Projekt ist unter der MIT License lizenziert - siehe [LICENSE](LICENSE) für Details.

## 🙏 Acknowledgments

- **Umbrel** - Für die großartige Self-Hosting Platform
- **FastAPI** - Für das moderne Python Web Framework
- **Zeroconf** - Für die mDNS/Bonjour Implementation
- **React** - Für das Frontend Framework

---

**Bitsperity Beacon** - Macht Service Discovery im lokalen Netzwerk einfach und zuverlässig! 🚀 