# HomeGrow v3 - Professional Hydroponic System Management

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/bitsperity/homegrow)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Umbrel](https://img.shields.io/badge/umbrel-compatible-purple.svg)](https://umbrel.com)

HomeGrow v3 ist eine professionelle Umbrel-App für die Verwaltung hydroponischer Systeme mit Arduino/ESP32-basierten Clients. Die App bietet automatische Service Discovery, Real-time Monitoring und intelligente Automation für optimale Pflanzenerträge.

## 🌱 Features

### Automatische Service Discovery
- **Bitsperity Beacon Integration**: ESP32 Clients werden automatisch erkannt und registriert
- **Zero-Configuration Setup**: Neue Geräte werden automatisch konfiguriert
- **Network Resilience**: Robuste Verbindungswiederherstellung

### Mobile-First PWA
- **Responsive Design**: Optimiert für Smartphone, Tablet und Desktop
- **Offline-Funktionalität**: Funktioniert auch ohne Internetverbindung
- **Push-Benachrichtigungen**: Sofortige Alerts bei kritischen Ereignissen
- **App-Installation**: Installierbar als native App auf allen Geräten

### Real-time Monitoring
- **Live Sensordaten**: pH, TDS, Temperatur und Luftfeuchtigkeit
- **Historische Charts**: Detaillierte Datenanalyse und Trends
- **WebSocket Updates**: Echtzeit-Updates ohne Seitenneuladen
- **Datenexport**: CSV/JSON Export für weitere Analyse

### Intelligente Automation
- **Wachstumsprogramme**: Phasenspezifische Automatisierung
- **Adaptive Algorithmen**: Selbstlernende Optimierung
- **Safety Limits**: Automatische Notabschaltung bei kritischen Werten
- **Scheduling**: Zeitbasierte Aktionen und Zyklen

### Manuelle Steuerung
- **7 Pumpen pro Client**: Wasser, Luft, pH+/-, Nährstoffe A/B, Cal-Mag
- **Präzise Dosierung**: Milliliter-genaue Steuerung
- **Sicherheitslimits**: Maximale Laufzeiten und Mengen
- **Emergency Stop**: Sofortige Abschaltung aller Pumpen

## 🏗️ Architektur

### Technology Stack
- **Frontend**: SvelteKit 2.0 + Tailwind CSS 3.3
- **Backend**: Fastify 4.24 + Node.js 20
- **Database**: MongoDB (via bitsperity-mongodb)
- **Communication**: MQTT v3 + WebSockets
- **Service Discovery**: Bitsperity Beacon
- **Deployment**: Docker + Umbrel

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ESP32 Client  │    │   ESP32 Client  │    │   ESP32 Client  │
│   (Device 001)  │    │   (Device 002)  │    │   (Device 003)  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │    Bitsperity Beacon      │
                    │   (Service Discovery)     │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │      MQTT Broker          │
                    │    (umbrel-mqtt)          │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     HomeGrow v3 App       │
                    │  ┌─────────────────────┐  │
                    │  │   SvelteKit PWA     │  │
                    │  │   (Frontend)        │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │   Fastify Server    │  │
                    │  │   (Backend API)     │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │   MongoDB           │  │
                    │  │   (Data Storage)    │  │
                    │  └─────────────────────┘  │
                    └───────────────────────────┘
```

## 🚀 Installation

### Umbrel Installation
1. Öffne den Umbrel App Store
2. Suche nach "HomeGrow v3"
3. Klicke auf "Install"
4. Warte auf die automatische Installation aller Dependencies

### Manuelle Installation
```bash
# Clone Repository
git clone https://github.com/bitsperity/homegrow.git
cd homegrow

# Install Dependencies
npm install

# Build Application
npm run build

# Start Production Server
npm start
```

### Docker Installation
```bash
# Build Image
docker build -t homegrow-v3 .

# Run Container
docker run -d \
  --name homegrow-v3 \
  -p 3000:3000 \
  -e MONGODB_URL=mongodb://localhost:27017/homegrow \
  -e MQTT_URL=mqtt://localhost:1883 \
  homegrow-v3
```

## 📱 Usage

### Initial Setup
1. Öffne HomeGrow v3 in deinem Browser: `http://your-umbrel-ip:3000`
2. Die App erkennt automatisch verfügbare ESP32 Clients
3. Konfiguriere deine Geräte über das Device Management
4. Erstelle Automation Rules oder Growth Programs

### Device Management
- **Auto-Discovery**: Neue Geräte werden automatisch erkannt
- **Manual Registration**: Manuelle Geräteregistrierung möglich
- **Configuration**: Sensor-Kalibrierung und Pumpen-Einstellungen
- **Monitoring**: Live-Status und Statistiken

### Monitoring Dashboard
- **System Overview**: Gesamtstatus aller Geräte
- **Real-time Data**: Live Sensordaten mit Charts
- **Alerts**: Kritische Benachrichtigungen
- **History**: Historische Datenanalyse

### Automation
- **Growth Programs**: Vordefinierte Wachstumsphasen
- **Custom Rules**: Eigene Automatisierungsregeln
- **Scheduling**: Zeitbasierte Aktionen
- **Safety Limits**: Automatische Sicherheitsabschaltung

## 🔧 Configuration

### Environment Variables
```bash
# Server Configuration
NODE_ENV=production
PORT=3000
HOST=0.0.0.0

# Database
MONGODB_URL=mongodb://bitsperity-mongodb:27017/homegrow

# MQTT
MQTT_URL=mqtt://umbrel-mqtt:1883

# Beacon Service Discovery
BEACON_URL=http://bitsperity-beacon:8080

# Security
JWT_SECRET=your-super-secret-key
```

### Device Configuration
```json
{
  "device_id": "001",
  "name": "Growbox Alpha",
  "sensors": {
    "ph": { "enabled": true, "calibration": {...} },
    "tds": { "enabled": true, "calibration": {...} }
  },
  "actuators": {
    "pumps": {
      "water": { "flow_rate_ml_per_sec": 10 },
      "ph_down": { "flow_rate_ml_per_sec": 1 },
      "nutrient_a": { "flow_rate_ml_per_sec": 2 }
    }
  }
}
```

## 🛠️ Development

### Prerequisites
- Node.js 20+
- MongoDB 6+
- MQTT Broker (Mosquitto)
- Bitsperity Beacon (optional)

### Development Setup
```bash
# Install Dependencies
npm install

# Start Development Server
npm run dev

# Run Tests
npm test

# Lint Code
npm run lint

# Format Code
npm run format
```

### Project Structure
```
bitsperity-homegrow/
├── src/                    # SvelteKit Frontend
│   ├── lib/               # Shared Libraries
│   │   ├── components/    # Svelte Components
│   │   ├── stores/        # State Management
│   │   └── utils/         # Utility Functions
│   └── routes/            # Page Routes
├── server/                # Backend Services
│   ├── services/          # Business Logic
│   ├── models/            # Data Models
│   ├── routes/            # API Routes
│   └── middleware/        # Express Middleware
├── static/                # Static Assets
├── tests/                 # Test Files
└── docs/                  # Documentation
```

## 📊 API Documentation

### REST API Endpoints
```
GET    /api/v1/devices              # List all devices
POST   /api/v1/devices              # Register new device
GET    /api/v1/devices/:id          # Get device details
PUT    /api/v1/devices/:id          # Update device
DELETE /api/v1/devices/:id          # Remove device

GET    /api/v1/sensors/:device_id   # Get sensor data
POST   /api/v1/commands/:device_id  # Send command
GET    /api/v1/programs             # List programs
POST   /api/v1/programs             # Create program
```

### WebSocket Events
```javascript
// Client -> Server
{
  "type": "subscribe_device",
  "device_id": "001"
}

// Server -> Client
{
  "type": "sensor_data",
  "device_id": "001",
  "data": {
    "ph": 6.5,
    "tds": 1200,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### MQTT Topics
```
homegrow/devices/{device_id}/sensors    # Sensor data from device
homegrow/devices/{device_id}/commands   # Commands to device
homegrow/devices/{device_id}/heartbeat  # Device status
homegrow/devices/{device_id}/config     # Configuration updates
```

## 🔒 Security

### Authentication
- JWT-based API authentication
- Secure session management
- CORS protection

### Data Protection
- Encrypted data transmission
- Secure credential storage
- Input validation and sanitization

### Network Security
- MQTT over TLS (optional)
- WebSocket security headers
- Rate limiting

## 🚨 Troubleshooting

### Common Issues

**Device not discovered**
- Check Bitsperity Beacon status
- Verify network connectivity
- Ensure device is broadcasting correctly

**MQTT connection failed**
- Verify MQTT broker is running
- Check connection credentials
- Confirm network accessibility

**Database connection error**
- Ensure MongoDB is running
- Check connection string
- Verify database permissions

**WebSocket disconnections**
- Check network stability
- Verify firewall settings
- Monitor server resources

### Logs and Debugging
```bash
# View application logs
docker logs homegrow_v3

# Enable debug logging
NODE_ENV=development LOG_LEVEL=debug npm start

# Check service status
curl http://localhost:3000/health
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Code Standards
- ESLint configuration for JavaScript/TypeScript
- Prettier for code formatting
- Conventional Commits for commit messages
- Jest for unit testing

### Testing
```bash
# Run all tests
npm test

# Run specific test suite
npm test -- --grep "Device Management"

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Umbrel](https://umbrel.com) - Self-hosted app platform
- [SvelteKit](https://kit.svelte.dev) - Web application framework
- [Fastify](https://fastify.io) - Fast web framework
- [MongoDB](https://mongodb.com) - Document database
- [Tailwind CSS](https://tailwindcss.com) - Utility-first CSS framework

## 📞 Support

- **Documentation**: [docs.bitsperity.com/homegrow](https://docs.bitsperity.com/homegrow)
- **Issues**: [GitHub Issues](https://github.com/bitsperity/homegrow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bitsperity/homegrow/discussions)
- **Email**: support@bitsperity.com

---

**HomeGrow v3** - Revolutionizing hydroponic automation with modern web technologies 🌱 