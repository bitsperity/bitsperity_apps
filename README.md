# HomeGrow v3 - Professional Hydroponic Management

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/bitsperity/homegrow)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Umbrel](https://img.shields.io/badge/umbrel-compatible-purple.svg)](https://umbrel.com)
[![PWA](https://img.shields.io/badge/PWA-enabled-orange.svg)](https://web.dev/progressive-web-apps/)

HomeGrow v3 ist eine professionelle Umbrel-App für die Verwaltung hydroponischer Systeme mit Arduino/ESP32-basierten Clients. Die App bietet eine moderne, mobile-first Benutzeroberfläche für Device-Management, Sensor-Monitoring, automatisierte Wachstumsprogramme und manuelle Steuerung.

## 🌟 Features

### 🔧 Device Management
- **Automatische Erkennung** neuer HomeGrow Clients über Bitsperity Beacon
- **Service Discovery Integration** für Zero-Configuration Networking
- **Remote Configuration** für alle Client-Parameter
- **Real-time Status Monitoring** (online/offline, uptime, connectivity)

### 📊 Live Monitoring
- **Real-time Sensor Data** (pH, TDS) mit Raw, Calibrated und Filtered Values
- **Historical Data Visualization** mit konfigurierbaren Zeiträumen
- **Multi-Device Comparison** für mehrere Clients gleichzeitig
- **Mobile-optimized Charts** mit Touch-Gesten

### 🎛️ Manual Control
- **Individual Pump Control** für alle 7 Pumpen pro Client
- **Advanced Dosing Controls** mit Volumen- und pH/TDS-Zielwerten
- **Emergency Stop** Funktionalität
- **Pump Scheduling** mit Intervall und Dauer

### 🌱 Program Management
- **Growth Program Templates** mit mehrstufigen Wachstumsphasen
- **Automated Program Execution** mit Phasen-Progression
- **Real-time Program Monitoring** mit detailliertem Logging
- **Custom Templates** für benutzerdefinierte Programme

### 🤖 Automation Engine
- **Rule-based Automation** für pH/TDS-Korrekturen
- **Intelligent Dosing Algorithms** basierend auf historischen Daten
- **Safety Rules** mit Emergency-Stop-Conditions
- **Predictive Maintenance** basierend auf Pump-Laufzeiten

### 📱 Progressive Web App
- **Mobile-first Design** mit responsivem Layout
- **Offline Capability** für kritische Funktionen
- **Push Notifications** für Alerts und Status-Updates
- **Dark/Light Mode** Support

## 🏗️ Architektur

```mermaid
graph TB
    subgraph "Umbrel Infrastructure"
        UMB_MQTT[Umbrel MQTT Broker]
        UMB_MONGO[Umbrel MongoDB]
        BEACON[Bitsperity Beacon]
    end
    
    subgraph "HomeGrow v3 App"
        FRONTEND[SvelteKit Frontend]
        BACKEND[Node.js Backend]
        API[REST API]
        WS[WebSocket Service]
    end
    
    subgraph "HomeGrow Clients"
        ESP32_1[ESP32 Client 1]
        ESP32_2[ESP32 Client 2]
        ESP32_N[ESP32 Client N]
    end
    
    ESP32_1 <-->|MQTT v3| UMB_MQTT
    ESP32_2 <-->|MQTT v3| UMB_MQTT
    ESP32_N <-->|MQTT v3| UMB_MQTT
    
    ESP32_1 -->|Service Registration| BEACON
    ESP32_2 -->|Service Registration| BEACON
    ESP32_N -->|Service Registration| BEACON
    
    BACKEND <--> UMB_MQTT
    BACKEND <--> UMB_MONGO
    BACKEND <--> BEACON
    
    FRONTEND <--> API
    FRONTEND <--> WS
```

## 🚀 Installation

### Voraussetzungen

- **Umbrel OS** (neueste Version)
- **Bitsperity MongoDB** App installiert
- **Bitsperity Beacon** App installiert
- **HomeGrow ESP32 Clients** mit v3 Firmware

### Über Umbrel App Store

1. Öffnen Sie den Umbrel App Store
2. Suchen Sie nach "HomeGrow v3"
3. Klicken Sie auf "Installieren"
4. Warten Sie auf die automatische Installation aller Dependencies

### Manuelle Installation

```bash
# Clone Repository
git clone https://github.com/bitsperity/homegrow.git
cd homegrow

# Build Docker Image
docker build -t homegrow:v3 .

# Deploy mit Docker Compose
docker-compose up -d
```

### Erste Einrichtung

1. **App öffnen**: Navigieren Sie zu `http://umbrel.local:3000`
2. **Geräte suchen**: Klicken Sie auf "Geräte suchen" im Dashboard
3. **ESP32 Clients**: Stellen Sie sicher, dass Ihre ESP32 Clients online sind
4. **Automatische Erkennung**: HomeGrow erkennt Clients automatisch über Beacon

## 📖 Benutzerhandbuch

### Dashboard

Das Dashboard bietet eine Übersicht über alle Ihre hydroponischen Systeme:

- **System Status Cards**: Zeigen Geräte-Status, Alerts, Programme und Uptime
- **Geräte-Übersicht**: Grid mit allen registrierten Clients und aktuellen Sensordaten
- **Schnellaktionen**: Buttons für häufige Aktionen wie Geräte-Suche und Notfall-Stop
- **Letzte Aktivitäten**: Feed mit den neuesten Systemereignissen

### Device Management

Verwalten Sie Ihre ESP32 Clients:

```javascript
// Beispiel: Gerät hinzufügen
const device = {
  device_id: "homegrow-client-001",
  name: "Salat System 1",
  location: "Gewächshaus A",
  description: "Hauptsystem für Salat-Anbau"
};
```

### Live Monitoring

Überwachen Sie Sensordaten in Echtzeit:

- **pH-Werte**: Kontinuierliche Überwachung mit Trend-Anzeige
- **TDS-Werte**: Nährstoff-Konzentration in ppm
- **Historische Daten**: Diagramme für verschiedene Zeiträume
- **Multi-Device View**: Vergleich mehrerer Systeme

### Manual Control

Steuern Sie Pumpen manuell:

```javascript
// Beispiel: Pumpe aktivieren
const command = {
  command: "activate_pump",
  params: {
    pump: "ph_down",
    duration_sec: 30,
    volume_ml: 10
  }
};
```

### Program Management

Erstellen und verwalten Sie Wachstumsprogramme:

```javascript
// Beispiel: Salat-Programm
const program = {
  name: "Salat Standard",
  phases: [
    {
      name: "Setzling",
      duration_days: 14,
      ph_target: { min: 5.5, max: 6.5 },
      tds_target: { min: 200, max: 350 }
    },
    {
      name: "Wachstum",
      duration_days: 21,
      ph_target: { min: 5.5, max: 6.0 },
      tds_target: { min: 450, max: 600 }
    }
  ]
};
```

## 🔌 API Dokumentation

### REST API Endpoints

#### Devices

```http
GET /api/v1/devices
POST /api/v1/devices
GET /api/v1/devices/{deviceId}
PUT /api/v1/devices/{deviceId}
DELETE /api/v1/devices/{deviceId}
POST /api/v1/devices/discover
```

#### Sensor Data

```http
GET /api/v1/sensors/{deviceId}/latest
GET /api/v1/sensors/{deviceId}/{sensorType}/history
GET /api/v1/sensors/{deviceId}/{sensorType}/aggregated
```

#### Commands

```http
POST /api/v1/commands/{deviceId}
GET /api/v1/commands/{deviceId}/history
GET /api/v1/commands/{commandId}/status
```

#### Programs

```http
GET /api/v1/programs/templates
POST /api/v1/programs/templates
GET /api/v1/programs/instances
POST /api/v1/programs/instances
PUT /api/v1/programs/instances/{instanceId}
DELETE /api/v1/programs/instances/{instanceId}
```

### WebSocket Events

```javascript
// Client -> Server
socket.emit('subscribe_device', deviceId);
socket.emit('send_command', { deviceId, command });

// Server -> Client
socket.on('sensor_data', (data) => {
  console.log('New sensor data:', data);
});

socket.on('device_status', (data) => {
  console.log('Device status changed:', data);
});

socket.on('command_response', (data) => {
  console.log('Command response:', data);
});
```

### MQTT Topics

```
# Sensor Data
homegrow/devices/{device_id}/sensors/ph
homegrow/devices/{device_id}/sensors/tds

# Commands
homegrow/devices/{device_id}/commands
homegrow/devices/{device_id}/commands/response

# System Status
homegrow/devices/{device_id}/heartbeat
homegrow/devices/{device_id}/status
```

## 🔧 Entwicklung

### Tech Stack

- **Frontend**: SvelteKit 2.0, Tailwind CSS, PWA
- **Backend**: Node.js, Fastify, Socket.io
- **Database**: MongoDB
- **Message Broker**: MQTT
- **Service Discovery**: Bitsperity Beacon
- **Container**: Docker Alpine

### Development Setup

```bash
# Clone Repository
git clone https://github.com/bitsperity/homegrow.git
cd homegrow

# Install Dependencies
npm install

# Setup Environment
cp .env.example .env
# Edit .env with your configuration

# Start Development Server
npm run dev

# Start Backend Services
npm run dev:server

# Run Tests
npm test
npm run test:e2e
```

### Environment Variables

```bash
# Database
MONGODB_URL=mongodb://localhost:27017/homegrow

# MQTT
MQTT_URL=mqtt://localhost:1883

# Beacon Service Discovery
BEACON_URL=http://localhost:8080

# App Configuration
NODE_ENV=development
PORT=3000
JWT_SECRET=your-secret-key

# Frontend
PUBLIC_API_URL=http://localhost:3000/api/v1
PUBLIC_WS_URL=ws://localhost:3000
```

### Build & Deployment

```bash
# Build for Production
npm run build

# Build Docker Image
docker build -t homegrow:v3 .

# Deploy to Umbrel
./scripts/deploy.sh
```

## 🧪 Testing

### Unit Tests

```bash
# Run Unit Tests
npm test

# Run with Coverage
npm run test:coverage

# Watch Mode
npm run test:watch
```

### Integration Tests

```bash
# Run Integration Tests
npm run test:integration

# Test API Endpoints
npm run test:api

# Test MQTT Communication
npm run test:mqtt
```

### End-to-End Tests

```bash
# Run E2E Tests
npm run test:e2e

# Run in Headed Mode
npm run test:e2e:headed

# Test Mobile
npm run test:e2e:mobile
```

## 🐛 Troubleshooting

### Häufige Probleme

#### 1. Geräte werden nicht erkannt

**Problem**: ESP32 Clients erscheinen nicht in der Geräteliste

**Lösung**:
```bash
# Prüfen Sie Beacon Service
curl http://bitsperity-beacon:8080/api/v1/services

# Prüfen Sie MQTT Verbindung
mosquitto_sub -h umbrel-mqtt -t "homegrow/devices/+/heartbeat"

# Prüfen Sie ESP32 Logs
# Auf ESP32: Serial Monitor öffnen
```

#### 2. Sensordaten werden nicht angezeigt

**Problem**: Dashboard zeigt keine aktuellen Sensordaten

**Lösung**:
```bash
# Prüfen Sie MQTT Topics
mosquitto_sub -h umbrel-mqtt -t "homegrow/devices/+/sensors/+"

# Prüfen Sie Database
mongo homegrow --eval "db.sensor_data.find().limit(5)"

# Prüfen Sie WebSocket Verbindung
# Browser DevTools -> Network -> WS
```

#### 3. Pumpen reagieren nicht

**Problem**: Manuelle Pump-Befehle werden nicht ausgeführt

**Lösung**:
```bash
# Prüfen Sie Command Topics
mosquitto_pub -h umbrel-mqtt -t "homegrow/devices/test-001/commands" -m '{"command":"test_pump","params":{"pump":"water","duration_sec":5}}'

# Prüfen Sie ESP32 Command Processing
# Serial Monitor: Command received/executed logs

# Prüfen Sie Safety Limits
# Dashboard -> Device -> Configuration
```

#### 4. App lädt nicht

**Problem**: HomeGrow App ist nicht erreichbar

**Lösung**:
```bash
# Prüfen Sie Container Status
docker ps | grep homegrow

# Prüfen Sie Logs
docker logs homegrow-app

# Prüfen Sie Dependencies
docker ps | grep -E "(mongodb|beacon)"

# Restart Services
docker-compose restart
```

### Debug Modus

```bash
# Enable Debug Logging
export DEBUG=homegrow:*
npm run dev

# MQTT Debug
export DEBUG=mqtt*
npm run dev:server

# Database Debug
export DEBUG=mongodb:*
npm run dev:server
```

### Log Files

```bash
# Application Logs
tail -f /app/logs/homegrow.log

# MQTT Logs
tail -f /app/logs/mqtt.log

# Error Logs
tail -f /app/logs/error.log

# Access Logs
tail -f /app/logs/access.log
```

## 📊 Performance

### Benchmarks

- **Dashboard Load Time**: < 2s
- **Real-time Updates**: < 500ms latency
- **API Response Time**: < 1s
- **Mobile Performance**: 60fps animations
- **Concurrent Users**: 5+ simultaneous sessions

### Monitoring

```bash
# System Resources
docker stats homegrow-app

# Database Performance
mongo homegrow --eval "db.runCommand({serverStatus: 1})"

# MQTT Message Rate
mosquitto_sub -h umbrel-mqtt -t '$SYS/broker/messages/received'
```

## 🔒 Security

### Authentication

- **JWT Tokens** für API Access
- **Role-based Access Control** (Admin, User, Viewer)
- **Session Management** mit automatischem Logout

### Data Protection

- **Encrypted Configuration** Storage
- **Secure MQTT** Communication
- **Input Validation** mit Joi
- **Rate Limiting** für API Endpoints

### Safety Features

- **Emergency Stop** bei kritischen Werten
- **Pump Protection** gegen Überlastung
- **Sensor Validation** mit Plausibilitätsprüfungen
- **Automatic Failsafe** bei Kommunikationsverlust

## 🤝 Contributing

Wir freuen uns über Beiträge zur HomeGrow v3 Entwicklung!

### Development Workflow

1. **Fork** das Repository
2. **Create** einen Feature Branch (`git checkout -b feature/amazing-feature`)
3. **Commit** Ihre Änderungen (`git commit -m 'Add amazing feature'`)
4. **Push** zum Branch (`git push origin feature/amazing-feature`)
5. **Open** einen Pull Request

### Code Standards

- **ESLint** für JavaScript/TypeScript Linting
- **Prettier** für Code Formatting
- **Conventional Commits** für Commit Messages
- **JSDoc** für API Documentation

### Testing Requirements

- **Unit Tests** für neue Features (>80% Coverage)
- **Integration Tests** für API Changes
- **E2E Tests** für UI Changes
- **Performance Tests** für Critical Paths

## 📄 License

Dieses Projekt ist unter der MIT License lizenziert - siehe [LICENSE](LICENSE) für Details.

## 🙏 Acknowledgments

- **Umbrel Team** für die großartige Plattform
- **SvelteKit Community** für das fantastische Framework
- **Arduino Community** für ESP32 Support
- **Open Source Contributors** für verwendete Libraries

## 📞 Support

- **GitHub Issues**: [https://github.com/bitsperity/homegrow/issues](https://github.com/bitsperity/homegrow/issues)
- **Documentation**: [https://docs.bitsperity.com/homegrow](https://docs.bitsperity.com/homegrow)
- **Community Forum**: [https://community.bitsperity.com](https://community.bitsperity.com)
- **Email Support**: support@bitsperity.com

---

**HomeGrow v3** - Professionelle hydroponische Systemverwaltung für das moderne Smart Home.

Made with ❤️ by [Bitsperity](https://bitsperity.com)
