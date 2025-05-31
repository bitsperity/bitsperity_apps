# HomeGrow v3 - System Architecture

## Executive Summary

HomeGrow v3 ist eine professionelle Umbrel-App für hydroponische Systeme, die ESP32-basierte IoT-Clients über MQTT verwaltet. Die Architektur folgt dem SvelteKit Full-Stack Ansatz mit direkter MongoDB-Integration und nativen WebSockets für Echtzeit-Updates.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               Umbrel Environment                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────┐  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │     HomeGrow v3         │  │   Umbrel Services   │  │    ESP32 Clients     │ │
│  │     (SvelteKit)         │  │                     │  │                      │ │
│  │                         │  │                     │  │                      │ │
│  │ Frontend ┌─────────────┐ │  │ ┌─────────────────┐ │  │ ┌──────────────────┐ │ │
│  │ • Dashboard│  PWA       │ │◄─┤ │ bitsperity-     │ │◄─┤ │ pH & TDS Sensors │ │ │
│  │ • Device   │  Service   │ │  │ │ mongodb         │ │  │ │ 7 Pump Types     │ │ │
│  │ • Monitor  │  Worker    │ │  │ │                 │ │  │ │ ESP32-S3 MCU     │ │ │
│  │ • Programs │            │ │  │ └─────────────────┘ │  │ │ MQTT Client      │ │ │
│  │ • Manual   └─────────────┘ │  │                     │  │ └──────────────────┘ │ │
│  │                         │  │ ┌─────────────────┐ │  │                      │ │
│  │ Backend  ┌─────────────┐ │  │ │ mosquitto       │ │  │ ┌──────────────────┐ │ │
│  │ • API Routes│MQTT Bridge│ │◄─┤ │ MQTT Broker     │ │◄─┤ │ Multiple Units   │ │ │
│  │ • Automation│WebSocket  │ │  │ │                 │ │  │ │ Per User Setup   │ │ │
│  │ • Engine    │Server     │ │  │ └─────────────────┘ │  │ │ MQTT Registration│ │ │
│  │ • Scheduler │           │ │  │                     │  │ └──────────────────┘ │ │
│  │ • DB Client └─────────────┘ │  │ ┌─────────────────┐ │  │                      │ │
│  │                         │  │ │ bitsperity-     │ │  │                      │ │
│  └─────────────────────────┘  │ │ beacon          │ │  │                      │ │
│                                │ │ mDNS Service    │ │  │                      │ │
│                                │ │ Discovery       │ │  │                      │ │
│                                │ └─────────────────┘ │  │                      │ │
│                                └─────────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Frontend Layer (Svelte)
```
src/
├── routes/
│   ├── +layout.svelte                 # Root layout mit Navigation
│   ├── +page.svelte                   # Dashboard (F-001)
│   ├── devices/
│   │   ├── +page.svelte              # Device Discovery (F-002)
│   │   └── [id]/+page.svelte         # Device Details
│   ├── monitoring/
│   │   └── +page.svelte              # Real-time Monitoring (F-003)
│   ├── programs/
│   │   ├── +page.svelte              # Program Management (F-005)
│   │   ├── editor/+page.svelte       # Template Editor (F-004)
│   │   └── [id]/+page.svelte         # Program Instance View
│   ├── manual/
│   │   └── +page.svelte              # Manual Control (F-007)
│   └── settings/
│       └── +page.svelte              # System Settings (F-010)
├── lib/
│   ├── components/
│   │   ├── ui/                       # UI Components (Button, Card, Chart)
│   │   ├── DeviceCard.svelte         # Device Status Display
│   │   ├── SensorChart.svelte        # Real-time Charts
│   │   ├── PumpController.svelte     # Manual Pump Controls
│   │   ├── ProgramEditor.svelte      # Visual Program Editor
│   │   └── AlertNotification.svelte  # Alert System (F-009)
│   ├── stores/
│   │   ├── devices.js                # Device State Management
│   │   ├── sensors.js                # Sensor Data Store
│   │   ├── programs.js               # Program State
│   │   ├── websocket.js              # Real-time Connection
│   │   ├── theme.js                  # UI Theme Management
│   │   └── notifications.js          # Alert Management
│   └── utils/
│       ├── api.js                    # API Client
│       ├── mqtt.js                   # MQTT Utils
│       └── charts.js                 # Chart Helpers
```

### Backend Layer (SvelteKit API + Services)
```
src/
├── routes/api/
│   ├── devices/
│   │   ├── +server.js               # Device CRUD API
│   │   ├── discovery/+server.js     # Device Discovery (Beacon Integration)
│   │   └── [id]/+server.js          # Individual Device API
│   ├── sensors/
│   │   ├── current/+server.js       # Live Sensor Data
│   │   ├── history/+server.js       # Historical Data Export
│   │   └── [deviceId]/+server.js    # Device-specific Sensor API
│   ├── programs/
│   │   ├── templates/+server.js     # Program Templates CRUD
│   │   ├── instances/+server.js     # Program Instance Management
│   │   └── actions/+server.js       # Manual Program Control
│   ├── commands/
│   │   └── +server.js               # Manual Pump Commands
│   ├── alerts/
│   │   └── +server.js               # Alert Management API
│   ├── settings/
│   │   └── +server.js               # System Configuration
│   └── ws/+server.js                # WebSocket Endpoint
├── lib/server/
│   ├── database/
│   │   ├── connection.js            # MongoDB Connection
│   │   ├── devices.js               # Device Data Access
│   │   ├── sensors.js               # Sensor Data Access
│   │   └── programs.js              # Program Data Access
│   ├── services/
│   │   ├── mqtt-bridge.js           # MQTT Client & Message Routing
│   │   ├── automation-engine.js     # Core Automation Logic (F-006)
│   │   ├── beacon-client.js         # Service Discovery Integration
│   │   ├── websocket-server.js      # Real-time Updates
│   │   └── scheduler.js             # Cron Jobs & Background Tasks
│   ├── controllers/
│   │   ├── device-controller.js     # Device Business Logic
│   │   ├── sensor-controller.js     # Sensor Processing
│   │   ├── program-controller.js    # Program Execution Logic
│   │   └── alert-controller.js      # Alert Generation & Management
│   └── utils/
│       ├── validation.js            # Input Validation
│       ├── logger.js                # Structured Logging
│       └── config.js                # Environment Configuration
```

## Data Flow Architecture

### 1. Device Registration & Configuration Flow
```
ESP32 Startup → mDNS Discovery → MQTT Connect → 
Config Request → HomeGrow DB Check → 
Config Response (new device auto-created) → 
ESP32 Config Apply → Normal Operation Start
```

### 2. Sensor Data Pipeline
```
ESP32 Sensor → MQTT Publish → Mosquitto Broker → HomeGrow MQTT Bridge → 
MongoDB Storage → WebSocket Broadcast → Svelte UI Update → 
Automation Rule Check → Pump Command (if needed)
```

### 3. Manual Control Flow
```
Svelte UI → API POST /commands → Validation → MQTT Command → 
ESP32 Execution → MQTT Response → Database Log → 
WebSocket Update → UI Feedback
```

### 4. Program Automation Flow
```
Scheduler Trigger → Active Programs Check → Current Phase Evaluation → 
Target vs Actual Comparison → Decision Engine → Pump Commands → 
Action Logging → Program Progress Update → WebSocket Notification
```

## Real-time Communication

### WebSocket Events
```typescript
interface WebSocketMessage {
  type: 'sensor_data' | 'device_status' | 'program_update' | 'alert' | 'command_result';
  device_id?: string;
  data: any;
  timestamp: string;
}

// Client Subscriptions
/ws/devices           // All device status changes
/ws/sensors           // All sensor data updates  
/ws/programs          // Program execution updates
/ws/alerts            // Real-time alert notifications
```

### MQTT Topics
```
homegrow/devices/{device_id}/sensors/ph            # pH sensor readings
homegrow/devices/{device_id}/sensors/tds           # TDS sensor readings
homegrow/devices/{device_id}/commands              # Commands to device
homegrow/devices/{device_id}/commands/response     # Command acknowledgments
homegrow/devices/{device_id}/config/request        # Config requests from device
homegrow/devices/{device_id}/config/response       # Config responses to device
homegrow/devices/{device_id}/heartbeat             # System heartbeat & status
homegrow/devices/{device_id}/status                # Device status updates
homegrow/devices/{device_id}/logs                  # System logs
```

## Security & Safety Architecture

### Input Validation
- **API Layer**: Zod schemas für alle Endpoints
- **MQTT Layer**: Message format validation
- **Database**: Schema validation bei Inserts
- **Frontend**: Form validation mit Svelte stores

### Safety Controls
- **Emergency Stop**: Immediate MQTT broadcast zu allen Geräten
- **Value Limits**: pH 4.0-8.5, TDS max 2000ppm als Hard Limits
- **Pump Protection**: Max 5min Laufzeit, Cooldown zwischen Aktionen
- **Heartbeat Monitoring**: Device offline nach 5min ohne Signal

### Error Handling
- **Graceful Degradation**: UI funktioniert auch bei WebSocket/MQTT Ausfall
- **Retry Logic**: Exponential backoff für MQTT/DB connections
- **Circuit Breaker**: Automation pausiert bei anhaltenden Sensor-Fehlern
- **Audit Trail**: Alle kritischen Aktionen werden geloggt

## Performance Architecture

### Database Optimization
```javascript
// Strategic Indexes for Performance
db.sensorData.createIndex({ device_id: 1, timestamp: -1 });  // Time series queries
db.sensorData.createIndex({ timestamp: -1 });                // Recent data queries
db.devices.createIndex({ device_id: 1 }, { unique: true });  // Device lookup
db.programs.createIndex({ status: 1, device_id: 1 });        // Active program queries
```

### Caching Strategy
- **In-Memory**: Device status cache (Redis-style Map)
- **Browser**: HTTP cache headers für statische API responses  
- **Database**: Connection pooling für MongoDB
- **MQTT**: Message deduplication über Message IDs

### Resource Management
- **Memory Target**: <256MB für gesamte App
- **CPU Target**: <10% on Raspberry Pi 4
- **Network**: Batched sensor updates (5 readings/message)
- **Storage**: Auto-cleanup von sensor_data älter als 30 Tage

## Deployment Architecture

### Single Container Design
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["node", "build"]
```

### Environment Configuration
```typescript
// config/environments.js
export const config = {
  development: {
    mongodb: 'mongodb://192.168.178.57:27017/homegrow',  // External via MCP
    mqtt: { host: '192.168.178.57', port: 1883 },
    beacon: 'http://192.168.178.57:8097',
    websocket: { port: 3001 }
  },
  production: {
    mongodb: 'mongodb://bitsperity-mongodb:27017/homegrow',  // Container network
    mqtt: { host: 'mosquitto', port: 1883 },
    beacon: 'http://bitsperity-beacon:8097',
    websocket: { port: 3000 }
  }
};
```

## Integration Points

### Umbrel Services
1. **bitsperity-mongodb**: Persistente Datenspeicherung
2. **mosquitto**: MQTT Broker für ESP32 Kommunikation  
3. **bitsperity-beacon**: Service Discovery für automatische ESP32 Erkennung

### ESP32 Client Protocol
```json
// Config Request (device registration)
{
  "device_id": "HG-001",
  "timestamp": 123456789,
  "request_type": "full_config",
  "firmware_version": "v3.0.0",
  "capabilities": ["ph_sensor", "tds_sensor", "pumps_7x"]
}

// Config Response (from server)
{
  "device_id": "HG-001",
  "timestamp": 123456790,
  "config": {
    "sensors": {
      "ph": {
        "enabled": true,
        "pin": 34,
        "calibration": {"slope": 3.5, "offset": 0.0},
        "update_interval": 60
      },
      "tds": {
        "enabled": true,
        "pin": 35,
        "calibration": {"factor": 0.5},
        "update_interval": 60
      }
    },
    "pumps": {
      "water": {"enabled": true, "pin": 16, "max_duration": 300},
      "ph_down": {"enabled": true, "pin": 18, "max_duration": 60}
    },
    "safety": {
      "ph_min": 4.0,
      "ph_max": 8.5,
      "tds_max": 2000
    }
  }
}

// Sensor Data Message (after config received)
{
  "timestamp": 123456800,
  "sensor_id": "ph",
  "values": {
    "raw": 1721,
    "calibrated": 7.0,
    "filtered": 6.98
  },
  "unit": "pH",
  "quality": "good",
  "calibration_valid": true
}

// Command Message (via MQTT)
{
  "command_id": "cmd_001",
  "command": "activate_pump",
  "params": {
    "pump_id": "ph_down",
    "duration_sec": 5,
    "reason": "pH correction: 6.8 → 6.2"
  }
}

// Command Response (from ESP32)
{
  "command_id": "cmd_001",
  "status": "completed",
  "result": {
    "actual_duration_sec": 4.98,
    "volume_dispensed_ml": 2.5
  },
  "timestamp": 123456805,
  "execution_time_ms": 4980
}
```

## Scalability Considerations

### Horizontal Scaling (Future)
- **Load Balancer**: NGINX für multiple HomeGrow instances
- **Database Sharding**: Device-based partitioning
- **MQTT Clustering**: Mosquitto cluster setup
- **WebSocket Scaling**: Redis adapter für multi-instance

### Vertical Scaling (Current)
- **Memory Pool**: Optimierte MongoDB connection pooling
- **CPU Efficiency**: Event-driven architecture mit minimal threads
- **I/O Optimization**: Batch processing für sensor data
- **Network**: Connection multiplexing für MQTT

## Architecture Decision Records (ADRs)

### ADR-001: Direct MongoDB Driver
**Decision**: Verwende nativen MongoDB driver statt ORM
**Rationale**: Performance, kleinerer Bundle, direktere Kontrolle über Queries
**Consequences**: Mehr Boilerplate, aber bessere Performance und Umbrel-Kompatibilität

### ADR-002: Native WebSocket 
**Decision**: Nutze native WebSocket API statt Socket.io
**Rationale**: Kleinere Bundle-Größe, keine zusätzlichen Dependencies
**Consequences**: Mehr manueller Code für Reconnection, aber geringerer Overhead

### ADR-003: SvelteKit Full-Stack
**Decision**: Monolithische SvelteKit App statt separater Frontend/Backend
**Rationale**: Einfachere Deployment, shared state, weniger Container
**Consequences**: Tighter coupling, aber einfachere Entwicklung und Wartung

### ADR-004: Single Container Deployment
**Decision**: Eine Container für gesamte App statt Microservices
**Rationale**: Umbrel-Standards, einfachere Konfiguration, geringerer Ressourcenverbrauch
**Consequences**: Weniger flexible Skalierung, aber bessere Umbrel-Integration

## Quality Metrics

### Performance Targets
- **Dashboard Load**: <2 Sekunden
- **API Response**: <1 Sekunde (95th percentile)
- **WebSocket Latency**: <500ms
- **Memory Usage**: <256MB unter Last
- **CPU Usage**: <10% idle, <50% unter Last

### Reliability Targets  
- **Uptime**: 99.5% (4 Stunden Downtime/Monat)
- **Data Loss**: <0.1% sensor readings
- **Command Success**: >99% pump commands erfolgreich
- **Recovery Time**: <2 Minuten nach Umbrel restart

### User Experience Targets
- **Mobile Performance**: 60fps auf iPhone 12+
- **Offline Capability**: Emergency stop funktioniert ohne Internet
- **Load Time**: <3 Sekunden auf 3G Verbindung
- **Error Recovery**: Automatische reconnection nach Netzwerk-Unterbrechung

## Technology Stack Summary

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Frontend** | Svelte + TypeScript | Reactive, performant, type-safe |
| **Backend** | SvelteKit API Routes | Full-stack, same codebase |
| **Database** | MongoDB (direct driver) | Document store, IoT-optimiert |
| **Real-time** | Native WebSocket | Low latency, simple |
| **IoT Communication** | MQTT v3.1.1 | Standard für IoT, reliable |
| **Styling** | Tailwind CSS | Utility-first, mobile-optimized |
| **Build Tool** | Vite (SvelteKit) | Fast builds, modern |
| **Container** | Node.18 Alpine | Small footprint, secure |
| **Process Manager** | PM2 (optional) | Process restart, monitoring |

Diese Architektur bietet eine solide Grundlage für die HomeGrow v3 Implementierung mit klarer Trennung der Verantwortlichkeiten, optimaler Performance und einfacher Wartbarkeit im Umbrel-Ökosystem. 