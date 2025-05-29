# HomeGrow v3 - Deployment Guide

## 📦 Docker Hub Deployment

HomeGrow v3 ist als Docker Image auf Docker Hub verfügbar: [bitsperity/homegrow](https://hub.docker.com/r/bitsperity/homegrow)

### Automatisches Deployment

Das `deploy-dockerhub.sh` Script automatisiert den gesamten Deployment-Prozess:

```bash
# Deploy latest version
./deploy-dockerhub.sh

# Deploy specific version
./deploy-dockerhub.sh 3.0.1
```

Das Script führt folgende Schritte aus:
1. 🎨 **Frontend Build** - Baut das SvelteKit Frontend
2. 🐳 **Docker Build** - Erstellt Multi-Platform Docker Image
3. 📤 **Docker Hub Push** - Lädt Image zu Docker Hub
4. 🏷️ **Git Tag** - Erstellt Version Tag (bei spezifischer Version)
5. 🚀 **Auto-Deploy** - Installiert App automatisch auf Umbrel Server

### Voraussetzungen

- Docker installiert und eingeloggt (`docker login`)
- SSH-Zugang zum Umbrel Server
- Umbrel Apps installiert:
  - `bitsperity-mongodb`
  - `bitsperity-beacon`
  - `mosquitto`

### Environment Variables

- `UMBREL_HOST` - SSH Host für Auto-Deploy (default: `umbrel@umbrel.local`)

```bash
# Deploy zu anderem Umbrel Server
UMBREL_HOST=admin@192.168.1.100 ./deploy-dockerhub.sh
```

## 🏠 Lokales Testing

Für lokale Entwicklung und Testing:

```bash
./deploy-local.sh
```

Das erstellt und startet einen lokalen Container mit:
- Port 3000 gemappt
- Verbindung zu lokalen Services via `host.docker.internal`
- Development Environment

### Nützliche Befehle

```bash
# Logs anzeigen
docker logs -f homegrow-dev

# Container stoppen
docker stop homegrow-dev

# Container neu starten
docker start homegrow-dev

# Shell im Container öffnen
docker exec -it homegrow-dev /bin/sh
```

## 🔧 Manuelle Installation

### Docker Run

```bash
docker run -d \
  --name homegrow \
  -p 3000:3000 \
  -e MONGODB_URL=mongodb://umbrel:umbrel@mongodb:27017/homegrow \
  -e MQTT_URL=mqtt://mosquitto:1883 \
  -e BEACON_URL=http://beacon:8097 \
  bitsperity/homegrow:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  homegrow:
    image: bitsperity/homegrow:latest
    ports:
      - "3000:3000"
    environment:
      - MONGODB_URL=mongodb://umbrel:umbrel@mongodb:27017/homegrow
      - MQTT_URL=mqtt://mosquitto:1883
      - BEACON_URL=http://beacon:8097
    depends_on:
      - mongodb
      - mosquitto
      - beacon
```

## 🏥 Health Checks

HomeGrow bietet mehrere Endpoints für Monitoring:

- `/api/health` - Basic Health Check
- `/api/v1/system/status` - Detaillierter System Status

```bash
# Health Check
curl http://localhost:3000/api/health

# System Status
curl http://localhost:3000/api/v1/system/status | jq
```

## 🐛 Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker logs bitsperity-homegrow

# Container Status
docker ps -a | grep homegrow
```

### Verbindungsprobleme

1. **MongoDB**: Prüfe ob `bitsperity-mongodb` läuft
2. **MQTT**: Prüfe ob `mosquitto` läuft
3. **Beacon**: Prüfe ob `bitsperity-beacon` läuft

```bash
# Services prüfen
docker ps | grep -E "(mongodb|mosquitto|beacon)"

# Netzwerk prüfen
docker network ls | grep umbrel
```

### ESP32 Client findet Server nicht

1. Beacon Service prüfen: `http://umbrel.local:8097/api/v1/health`
2. MQTT Broker prüfen: Port 1883 muss erreichbar sein
3. mDNS/Bonjour aktivieren

## 📊 Monitoring

### Logs

Logs werden in `/app/logs` gespeichert und via Docker Volume gemountet:

```bash
# Live Logs
docker exec -it bitsperity-homegrow tail -f /app/logs/app.log

# Oder via Docker
docker logs -f bitsperity-homegrow
```

### Metriken

System-Metriken via Status Endpoint:

```bash
watch -n 5 'curl -s http://localhost:3000/api/v1/system/status | jq .services'
```

## 🔐 Sicherheit

### Produktions-Deployment

Für Produktion sollten folgende Umgebungsvariablen gesetzt werden:

```bash
NODE_ENV=production
LOG_LEVEL=info
```

### Netzwerk-Isolation

HomeGrow nutzt das Umbrel Netzwerk für sichere Kommunikation zwischen Services.

## 🆘 Support

Bei Problemen:
1. [GitHub Issues](https://github.com/bitsperity/homegrow/issues)
2. [Umbrel Community](https://community.getumbrel.com)
3. [Discord Server](https://discord.gg/bitsperity) 