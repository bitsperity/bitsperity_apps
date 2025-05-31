# HomeGrow v3 - Implementation Roadmap

## Gesamte Zeitplanung

```
Entwicklungszeit: 6 Wochen (42 Arbeitstage)
├── Phase 1: Core Foundation (14 Tage / 2 Wochen)
├── Phase 2: Historical Data (5 Tage / 1 Woche)
├── Phase 3: Device Management (5 Tage / 1 Woche) 
└── Phase 4: Automation & Alerts (14 Tage / 2 Wochen)

Daily Effort: 8 Stunden
Weekly Effort: 40 Stunden
Total Effort: 240 Stunden
```

## Phase 1: Core Foundation (14 Tage)

### Woche 1: Infrastructure & Basic Setup

#### Tag 1-2: Projekt Foundation
**Ziel**: Vollständige SvelteKit-Projektstruktur mit TypeScript

**Aufgaben:**
- [ ] **SvelteKit Projekt initialisieren**
  ```bash
  npm create svelte@latest homegrow-v3
  cd homegrow-v3
  npm install
  ```
- [ ] **TypeScript + Tailwind CSS Setup**
  ```bash
  npm install -D typescript @sveltejs/adapter-node
  npm install -D tailwindcss postcss autoprefixer
  npm install -D @types/node
  ```
- [ ] **Ordnerstruktur erstellen**
  ```
  src/
  ├── routes/
  ├── lib/
  │   ├── components/
  │   ├── stores/
  │   ├── server/
  │   └── utils/
  ├── app.html
  └── app.css
  ```
- [ ] **Docker Container Setup**
  ```dockerfile
  FROM node:18-alpine
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci
  COPY . .
  RUN npm run build
  EXPOSE 3000
  CMD ["node", "build"]
  ```
- [ ] **Development Environment konfigurieren**
  - MCP MongoDB Connection (192.168.178.57:27017)
  - Environment Variables (.env file)
  - Basic dev server startup

**Deliverables:**
- ✅ Funktionsfähiger SvelteKit-Server
- ✅ TypeScript-Konfiguration
- ✅ Tailwind CSS setup
- ✅ Docker-Container buildbar

**Acceptance Tests:**
```bash
# Test 1: Dev server starts successfully
npm run dev
curl http://localhost:5173/ # Should return 200

# Test 2: Build process works
npm run build
node build/index.js # Should start production server

# Test 3: Docker container builds
docker build -t homegrow-v3 .
docker run -p 3000:3000 homegrow-v3 # Should be accessible
```

#### Tag 3-4: Database Foundation
**Ziel**: MongoDB-Integration mit Device Collection und grundlegende API

**Aufgaben:**
- [ ] **MongoDB Client installieren und konfigurieren**
  ```bash
  npm install mongodb
  npm install -D @types/mongodb
  ```
- [ ] **Database Connection Service**
  ```typescript
  // src/lib/server/database/connection.js
  import { MongoClient } from 'mongodb';
  
  class DatabaseConnection {
    constructor() {
      this.connectionString = process.env.NODE_ENV === 'production' 
        ? 'mongodb://bitsperity-mongodb:27017/homegrow'
        : 'mongodb://192.168.178.57:27017/homegrow';
    }
    // ... implementation
  }
  ```
- [ ] **Device Collection Schema implementieren**
  ```typescript
  // Device interface + validation
  // Collection setup with indexes
  // Basic CRUD operations
  ```
- [ ] **API Routes erstellen**
  ```
  /api/v1/devices → GET (list all devices)
  /api/v1/devices → POST (create device) 
  /api/v1/devices/[id] → GET (device details)
  /api/v1/health → GET (health check)
  ```
- [ ] **Error Handling Setup**
  - Database connection errors
  - API error responses (standardized format)
  - Retry logic für connection failures

**Deliverables:**
- ✅ MongoDB-Verbindung funktional (MCP Development)
- ✅ Device Collection mit Indexes
- ✅ Grundlegende REST API
- ✅ Health Check Endpoint

**Acceptance Tests:**
```bash
# Test 1: Database connection works
curl http://localhost:5173/api/v1/health
# Should return {"status": "healthy", "components": {"database": "connected"}}

# Test 2: Device API functional
curl -X POST http://localhost:5173/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": "test-001", "name": "Test Device"}'
# Should return 201 Created

curl http://localhost:5173/api/v1/devices
# Should return device list

# Test 3: Error handling works
# Stop MongoDB service, requests should return proper errors
```

#### Tag 5-7: MQTT Integration & WebSocket Bridge
**Ziel**: MQTT-Client für ESP32-Kommunikation und WebSocket für Real-time Updates

**Aufgaben:**
- [ ] **MQTT Client Setup**
  ```bash
  npm install mqtt
  npm install -D @types/mqtt
  ```
- [ ] **MQTT Bridge Service implementieren**
  ```typescript
  // src/lib/server/mqtt-bridge.js
  class MQTTBridge {
    constructor() {
      this.client = mqtt.connect({
        host: process.env.NODE_ENV === 'production' ? 'mosquitto' : '192.168.178.57',
        port: 1883
      });
    }
    // Message handling, sensor data processing
  }
  ```
- [ ] **WebSocket Server Setup**
  ```typescript
  // Native WebSocket server
  // Message broadcasting to connected clients
  // Connection management (connect/disconnect/reconnect)
  ```
- [ ] **MQTT Topic Structure definieren**
  ```
  homegrow/devices/{device_id}/sensors/ph
  homegrow/devices/{device_id}/sensors/tds  
  homegrow/devices/{device_id}/status
  homegrow/devices/{device_id}/commands
  ```
- [ ] **Device Auto-Registration via MQTT**
  - ESP32 sends registration request
  - Server creates device automatically
  - Configuration response sent back
- [ ] **Sensor Data Pipeline**
  - MQTT sensor data → MongoDB storage
  - Real-time broadcast via WebSocket
  - Data validation and quality assessment

**Deliverables:**
- ✅ MQTT Client connected to broker
- ✅ WebSocket Server funktional
- ✅ Sensor data pipeline (MQTT → DB → WebSocket)
- ✅ Device auto-registration

**Acceptance Tests:**
```bash
# Test 1: MQTT connection works
mosquitto_pub -h 192.168.178.57 -t "homegrow/devices/test-001/sensors/ph" \
  -m '{"value": 6.5, "timestamp": "2024-01-15T10:00:00Z"}'
# Should appear in database and WebSocket

# Test 2: WebSocket real-time updates
# Open browser dev tools, connect to WebSocket
# Publish MQTT message, should receive WebSocket message

# Test 3: Device auto-registration
mosquitto_pub -h 192.168.178.57 -t "homegrow/devices/new-device/config/request" \
  -m '{"device_id": "new-device", "firmware_version": "v3.0.0"}'
# Should create device and send config response
```

### Woche 2: Frontend Development & Deployment

#### Tag 8-10: Dashboard UI Development
**Ziel**: Responsive Dashboard mit Device Cards und Live-Updates

**Aufgaben:**
- [ ] **UI Component Library Setup**
  ```typescript
  // src/lib/components/ui/
  // Button, Card, Badge, Spinner, etc.
  // Consistent design system mit Tailwind
  ```
- [ ] **Svelte Stores für State Management**
  ```typescript
  // src/lib/stores/devices.js
  export const devicesStore = writable({
    devices: [],
    loading: false,
    error: null
  });
  
  // src/lib/stores/websocket.js
  export const websocketStore = writable({
    connected: false,
    messages: []
  });
  ```
- [ ] **Device Card Component**
  ```svelte
  <!-- src/lib/components/DeviceCard.svelte -->
  <script>
    export let device;
    export let sensors = [];
  </script>
  
  <div class="device-card">
    <header>
      <h3>{device.name}</h3>
      <StatusBadge status={device.status} />
    </header>
    <div class="sensors">
      {#each sensors as sensor}
        <SensorDisplay {sensor} />
      {/each}
    </div>
  </div>
  ```
- [ ] **Dashboard Layout**
  ```svelte
  <!-- src/routes/+page.svelte -->
  <script>
    import DeviceGrid from '$lib/components/DeviceGrid.svelte';
    import { devicesStore } from '$lib/stores/devices.js';
  </script>
  
  <main class="dashboard">
    <header>
      <h1>HomeGrow Dashboard</h1>
    </header>
    <DeviceGrid devices={$devicesStore.devices} />
  </main>
  ```
- [ ] **Real-time Data Integration**
  - WebSocket store verbindet mit Server
  - Live sensor updates in Device Cards
  - Connection status indicator
  - Auto-reconnection logic

**Deliverables:**
- ✅ Responsive Dashboard Layout
- ✅ Device Card Component mit Live-Updates
- ✅ WebSocket Store für Real-time Data
- ✅ Mobile-optimierte UI

**Acceptance Tests:**
```bash
# Test 1: Dashboard loads quickly
# Navigate to http://localhost:5173/
# Page should load within 2 seconds

# Test 2: Real-time updates work
# Publish MQTT sensor data
# Should see updates in dashboard without refresh

# Test 3: Mobile responsiveness
# Test on various screen sizes
# All elements should be accessible and usable
```

#### Tag 11-12: Umbrel Integration
**Ziel**: Vollständige Umbrel-Deployment-Konfiguration

**Aufgaben:**
- [ ] **umbrel-app.yml erstellen**
  ```yaml
  manifestVersion: 1
  id: homegrow-v3
  name: HomeGrow v3
  version: "3.0.0"
  category: automation
  tagline: Professional hydroponic automation
  dependencies:
    - bitsperity-mongodb
    - mosquitto
    - bitsperity-beacon
  port: 3420
  ```
- [ ] **docker-compose.yml für Umbrel**
  ```yaml
  version: "3.8"
  services:
    app:
      image: homegrow-v3:${APP_VERSION}
      container_name: homegrow-v3_app_1
      restart: unless-stopped
      ports:
        - "${APP_PORT:-3420}:3000"
      environment:
        - NODE_ENV=production
        - MONGODB_URL=mongodb://bitsperity-mongodb:27017/homegrow
        - MQTT_HOST=mosquitto
      depends_on:
        bitsperity-mongodb:
          condition: service_healthy
        mosquitto:
          condition: service_started
      networks:
        - default
        - bitsperity-mongodb_default
        - mosquitto_default
  ```
- [ ] **Environment Configuration**
  - Production vs Development configs
  - Service discovery integration
  - Health check configuration
- [ ] **Beacon Service Registration**
  ```typescript
  // ESP32 devices discover HomeGrow via beacon
  // Register service for mDNS discovery
  // Service announcement and capabilities
  ```

**Deliverables:**
- ✅ Umbrel App Manifest
- ✅ Docker Compose Configuration
- ✅ Service Dependencies configured
- ✅ Beacon Integration für Device Discovery

**Acceptance Tests:**
```bash
# Test 1: Umbrel deployment works
docker-compose up -d
# Should start all services successfully

# Test 2: Service dependencies work
# All dependent services should be accessible
# Health check should report all components healthy

# Test 3: Beacon registration works
# Service should be discoverable via mDNS
# ESP32 devices should be able to find service
```

#### Tag 13-14: Testing, Polish & Documentation
**Ziel**: Robuste Phase 1 Anwendung mit vollständiger Dokumentation

**Aufgaben:**
- [ ] **End-to-End Testing**
  ```bash
  # Full deployment test
  # Device registration test
  # Real-time data flow test
  # Error scenarios test
  ```
- [ ] **Performance Optimization**
  - Bundle size analysis
  - WebSocket connection optimization
  - Database query optimization
  - Memory leak checks
- [ ] **Error Handling vervollständigen**
  - MQTT disconnection scenarios
  - Database unavailable scenarios
  - WebSocket connection failures
  - Graceful degradation
- [ ] **User Documentation**
  - Installation guide
  - ESP32 setup instructions
  - Troubleshooting guide
  - API documentation

**Deliverables:**
- ✅ Vollständige End-to-End Tests
- ✅ Performance-optimierte Anwendung
- ✅ Robuste Error Handling
- ✅ User Documentation

**Phase 1 Final Acceptance Tests:**
```bash
# Test Scenario 1: Fresh Umbrel Installation
1. Deploy HomeGrow v3 on Umbrel
2. Connect ESP32 device to network
3. Verify automatic device discovery
4. Confirm real-time sensor data display
5. Test app restart (data persistence)

# Test Scenario 2: Multiple Devices
1. Connect 3 ESP32 devices
2. Verify all devices appear in dashboard
3. Confirm real-time updates from all devices
4. Test simultaneous data streams

# Test Scenario 3: Network Interruption
1. Start with working system
2. Disconnect network for 2 minutes
3. Reconnect network
4. Verify automatic reconnection and data flow

# Test Scenario 4: Mobile Experience
1. Access dashboard on smartphone
2. Verify responsive layout
3. Test real-time updates on mobile
4. Confirm PWA functionality works
```

## Phase 2: Historical Data & Charts (5 Tage)

### Tag 1-2: Backend Data Layer
**Ziel**: Historical data storage und optimierte Abfrage-API

**Aufgaben:**
- [ ] **SensorData Collection Setup**
  ```typescript
  // Sensor data schema implementation
  // Optimized indexes for time-series queries
  // TTL index for automatic 30-day cleanup
  ```
- [ ] **Historical API Endpoints**
  ```typescript
  // GET /api/v1/sensors/{deviceId}/history
  // Query parameters: from, to, aggregation, limit
  // Data aggregation pipelines (minute/hour/day)
  ```
- [ ] **Data Aggregation Pipelines**
  ```javascript
  // MongoDB aggregation for different time ranges
  // Performance optimization for large datasets
  // Memory-efficient data processing
  ```

**Deliverables:**
- ✅ SensorData Collection mit Indexes
- ✅ Historical Data API
- ✅ Aggregation Pipelines

### Tag 3-4: Frontend Charts
**Ziel**: Interactive Charts mit Chart.js

**Aufgaben:**
- [ ] **Chart.js Integration**
  ```bash
  npm install chart.js chartjs-adapter-date-fns
  ```
- [ ] **SensorChart Component**
  ```svelte
  <!-- Interactive line charts -->
  <!-- Multi-sensor overlay (pH + TDS) -->
  <!-- Zoom/Pan functionality -->
  ```
- [ ] **Time Range Selector**
  ```svelte
  <!-- 1h, 6h, 24h, 7d, 30d options -->
  <!-- Custom date range picker -->
  <!-- Loading states -->
  ```

**Deliverables:**
- ✅ Interactive Charts
- ✅ Time Range Selection
- ✅ Mobile-optimized Charts

### Tag 5: Testing & Export
**Ziel**: CSV Export und vollständige Phase 2 Tests

**Aufgaben:**
- [ ] **CSV Export Funktionalität**
- [ ] **Performance Testing** (10k+ data points)
- [ ] **Mobile Chart Testing**

**Phase 2 Acceptance Tests:**
```bash
# Test 1: Chart Performance
# Load 30-day chart with 10,000+ data points
# Should render within 3 seconds

# Test 2: Time Range Selection
# Test all time range options
# Verify data accuracy for each range

# Test 3: Export Functionality  
# Export 7-day data as CSV
# Verify data completeness and format
```

## Phase 3: Device Management (5 Tage)

### Tag 1-2: Device Discovery
**Ziel**: Auto-Discovery und Manual Device Addition

**Aufgaben:**
- [ ] **Beacon Integration für Auto-Discovery**
- [ ] **Network Scanning für Manual Discovery**
- [ ] **Device Registration Workflow**

### Tag 3-4: Configuration Management
**Ziel**: Device Configuration Interface

**Aufgaben:**
- [ ] **DeviceConfig Component mit Validierung**
- [ ] **Sensor Calibration Interface**
- [ ] **Safety Limits Configuration**

### Tag 5: Device Operations
**Ziel**: Complete Device Lifecycle Management

**Aufgaben:**
- [ ] **Device Deletion mit Confirmation**
- [ ] **Configuration Backup/Restore**
- [ ] **Batch Operations**

**Phase 3 Acceptance Tests:**
```bash
# Test 1: Device Addition Speed
# Add new device in under 2 minutes
# Verify automatic configuration

# Test 2: Configuration Validation
# Test invalid configurations
# Verify clear error messages

# Test 3: Device Management
# Test renaming, deletion, backup
# Verify no data corruption
```

## Phase 4: Automation & Alerts (14 Tage)

### Woche 1: Automation Engine (7 Tage)

#### Tag 1-3: Core Automation
**Ziel**: Automation Engine mit pH/TDS-Korrektur

**Aufgaben:**
- [ ] **Program Templates Collection**
- [ ] **Automation Decision Engine**
- [ ] **pH Correction Algorithm**
- [ ] **TDS Adjustment Logic**

#### Tag 4-5: Command System
**Ziel**: Pump Control mit Safety Features

**Aufgaben:**
- [ ] **Command API Implementation**
- [ ] **Safety Validation Logic**
- [ ] **Command Queue Processing**

#### Tag 6-7: Program Management
**Ziel**: Growth Program Templates und Execution

**Aufgaben:**
- [ ] **Program Template Editor**
- [ ] **Program Instance Tracking**
- [ ] **Phase Transition Logic**

### Woche 2: Alerts & Advanced Features (7 Tage)

#### Tag 8-10: Alert System
**Ziel**: Comprehensive Alert Management

**Aufgaben:**
- [ ] **Alert Rule Configuration**
- [ ] **Alert Processing Engine**
- [ ] **In-App Notifications**
- [ ] **PWA Push Notifications**

#### Tag 11-12: Manual Control
**Ziel**: Manual Override Interface

**Aufgaben:**
- [ ] **Manual Pump Control Interface**
- [ ] **Emergency Stop System**
- [ ] **Command History Tracking**

#### Tag 13-14: Final Integration & Testing
**Ziel**: Complete System Integration

**Aufgaben:**
- [ ] **End-to-End Automation Testing**
- [ ] **Performance Testing under Load**
- [ ] **User Acceptance Testing**
- [ ] **Documentation finalization**

**Phase 4 Final Acceptance Tests:**
```bash
# Test Scenario 1: Full Automation
1. Set up growth program for lettuce
2. Let system run for 48 hours
3. Verify automated pH/TDS corrections
4. Confirm alert notifications work
5. Test emergency stop functionality

# Test Scenario 2: Multi-Device Automation
1. Configure 3 devices with different programs
2. Run simultaneous automation
3. Verify no interference between devices
4. Test system performance under load

# Test Scenario 3: User Experience
1. Complete user workflow from device setup to automation
2. Verify intuitive interface for non-technical users
3. Test mobile PWA functionality
4. Confirm 7-day autonomous operation
```

## Release Milestones

### Phase 1 Release (MVP)
**Target**: End of Week 2
- ✅ Basic monitoring dashboard
- ✅ Real-time sensor tracking
- ✅ Mobile PWA functionality
- ✅ Umbrel deployment ready

### Phase 2 Release (Analytics)
**Target**: End of Week 3  
- ✅ Historical data analysis
- ✅ Interactive charts
- ✅ Data export capabilities
- ✅ Trend analysis features

### Phase 3 Release (Management)
**Target**: End of Week 4
- ✅ Complete device management
- ✅ Configuration interface
- ✅ Multi-device scaling
- ✅ Professional setup tools

### Phase 4 Release (Full Automation)
**Target**: End of Week 6
- ✅ Full automation capabilities
- ✅ Intelligent alert system
- ✅ Growth program templates
- ✅ Production-ready system

## Quality Gates & Release Criteria

### Each Phase Must Meet:
- [ ] All planned features implemented and tested
- [ ] Performance targets achieved
- [ ] Mobile experience optimized
- [ ] Error handling robust
- [ ] Documentation complete
- [ ] Umbrel deployment successful

### Final Release Criteria:
- [ ] 99% uptime over 7-day test period
- [ ] All automation features working correctly
- [ ] Mobile PWA passes all tests
- [ ] Memory usage under 512MB
- [ ] Response times under specified limits
- [ ] User documentation complete

Diese Roadmap bietet einen detaillierten, testbaren Entwicklungsplan für HomeGrow v3 mit klaren Milestones und Qualitätskriterien für jede Phase. 