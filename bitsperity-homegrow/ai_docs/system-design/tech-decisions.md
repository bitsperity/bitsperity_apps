# HomeGrow v3 - Technical Decisions

## Architecture Decision Records (ADRs)

Diese Dokumentation erfasst alle wichtigen technischen Entscheidungen für HomeGrow v3 mit deren Begründung, Alternativen und Konsequenzen.

## ADR-001: SvelteKit Full-Stack Framework

### Status: Accepted
### Datum: 2024-01-15
### Entscheider: System Architect

### Kontext
HomeGrow v3 benötigt eine moderne Web-Architektur mit Frontend, Backend-API und Real-time Updates. Die Wahl des Frameworks beeinflusst Entwicklungsgeschwindigkeit, Performance und Deployment-Komplexität.

### Entscheidung
Wir verwenden **SvelteKit** als Full-Stack Framework für Frontend und Backend.

### Alternativen Betrachtet
1. **Next.js + Express.js**: Separate Frontend/Backend
2. **Vue.js + Fastify**: Component-orientiert
3. **React + Node.js**: Bewährter Stack
4. **Astro + Express**: Static-Site Generator

### Begründung
- **Single Codebase**: Frontend und Backend in einem Projekt
- **Performance**: Svelte kompiliert zu vanillaJS, kleinere Bundle-Größen
- **Development Experience**: Hervorragende DX mit TypeScript-Integration
- **SSR/SPA**: Flexibles Rendering für optimale Performance
- **File-based Routing**: Intuitive Struktur für API und Pages
- **Umbrel Compatibility**: Single Container Deployment möglich

### Konsequenzen
✅ **Positiv**:
- Reduzierte Komplexität (ein Framework statt zwei)
- Schnellere Entwicklung durch shared State
- Kleinere Bundle-Größe für mobile PWA
- Excellent TypeScript support

❌ **Negativ**:
- Weniger Flexibilität bei separater Skalierung
- Team muss Svelte lernen (weniger verbreitet als React)
- Tighter coupling zwischen Frontend/Backend

### Umsetzung
```typescript
// SvelteKit project structure
src/
├── routes/           # Pages + API routes
├── lib/              # Shared utilities
├── app.html          # Root template
└── hooks.server.js   # Server-side hooks
```

## ADR-002: Direct MongoDB Driver (No ORM)

### Status: Accepted
### Datum: 2024-01-15
### Entscheider: System Architect

### Kontext
HomeGrow v3 benötigt eine Datenbank-Lösung für IoT Time-Series Daten, Device-Konfiguration und Program-Templates. Die Wahl zwischen direktem Database-Driver vs. ORM beeinflusst Performance und Komplexität.

### Entscheidung
Wir verwenden den **nativen MongoDB-Driver** ohne ORM/ODM.

### Alternativen Betrachtet
1. **Mongoose ODM**: Object Document Mapping
2. **Prisma**: Type-safe ORM mit Schema
3. **TypeORM**: Multi-database ORM
4. **Slonik**: PostgreSQL-focused

### Begründung
- **Performance**: Direkter Zugriff ohne ORM-Overhead
- **Bundle Size**: Keine zusätzlichen Dependencies
- **Flexibility**: Vollständige Kontrolle über Queries
- **MongoDB-optimiert**: Aggregation Pipelines nutzen
- **Umbrel Integration**: Einfachere Dependency-Verwaltung
- **Time-Series**: Optimierte Queries für Sensor-Daten

### Konsequenzen
✅ **Positiv**:
- Höhere Performance bei Time-Series Queries
- Kleinere Bundle-Größe
- Direkter Zugang zu MongoDB-Features
- Weniger abstrakte Komplexität

❌ **Negativ**:
- Mehr Boilerplate-Code
- Keine automatische Type-Safety
- Manuelle Schema-Validierung nötig
- Requires MongoDB expertise

### Umsetzung
```typescript
// Direct MongoDB driver usage
import { MongoClient } from 'mongodb';

const client = new MongoClient(connectionString);
const db = client.db('homegrow');

// Optimized sensor data query
const sensorData = await db.collection('sensor_data').aggregate([
  { $match: { device_id: 'HG-001', timestamp: { $gte: yesterday } } },
  { $group: { _id: '$sensor_type', latest: { $last: '$values.calibrated' } } }
]).toArray();
```

## ADR-003: Native WebSocket (No Socket.io)

### Status: Accepted
### Datum: 2024-01-15
### Entscheider: System Architect

### Kontext
Real-time Updates sind kritisch für HomeGrow v3 (Live Sensor-Daten, Alert-Notifications). Die Wahl der WebSocket-Implementierung beeinflusst Latenz, Bundle-Größe und Browser-Kompatibilität.

### Entscheidung
Wir verwenden **native WebSocket API** ohne Socket.io.

### Alternativen Betrachtet
1. **Socket.io**: Full-featured WebSocket library
2. **ws + reconnecting-websocket**: Minimaler Wrapper
3. **Pusher**: Hosted WebSocket service
4. **SvelteKit WebSocket**: Framework-integriert

### Begründung
- **Bundle Size**: Native API ohne zusätzliche Dependencies
- **Performance**: Geringerer Overhead, direkte Kontrolle
- **Simplicity**: Weniger Abstraktions-Layer
- **Browser Support**: Native WebSocket ist universell unterstützt
- **Control**: Vollständige Kontrolle über Reconnection-Logic

### Konsequenzen
✅ **Positiv**:
- Kleinste mögliche Bundle-Größe
- Niedrigste Latenz
- Volle Kontrolle über Connection-Management
- Keine vendor lock-in

❌ **Negativ**:
- Mehr manueller Code für Reconnection
- Keine built-in Fallbacks
- Requires WebSocket expertise
- Manual message queuing nötig

### Umsetzung
```typescript
// Native WebSocket with auto-reconnect
class WebSocketClient {
  connect() {
    this.ws = new WebSocket('ws://localhost:3000/api/v1/ws');
    this.ws.onmessage = this.handleMessage.bind(this);
    this.ws.onclose = () => setTimeout(() => this.connect(), 5000);
  }
  
  send(message) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}
```

## ADR-004: Single Container Deployment

### Status: Accepted
### Datum: 2024-01-15
### Entscheider: System Architect

### Kontext
HomeGrow v3 muss auf Umbrel deployed werden. Die Wahl zwischen Monolith vs. Microservices beeinflusst Deployment-Komplexität, Resource-Usage und Development-Experience.

### Entscheidung
Wir deployen als **Single Container** mit allen Services in einem Node.js-Prozess.

### Alternativen Betrachtet
1. **Microservices**: Separate Container für Frontend, API, Background-Jobs
2. **Docker Compose**: Multi-Container mit service-dependencies
3. **Kubernetes**: Orchestrated microservices
4. **Serverless**: Function-based architecture

### Begründung
- **Umbrel Standards**: Umbrel bevorzugt Single-Container Apps
- **Resource Efficiency**: Weniger Memory/CPU overhead
- **Deployment Simplicity**: Eine Docker-Image, einfachere CI/CD
- **Development Experience**: Lokales Development einfacher
- **Shared State**: In-Memory State zwischen Services möglich

### Konsequenzen
✅ **Positiv**:
- Einfacheres Deployment und Monitoring
- Geringerer Resource-Verbrauch
- Faster inter-service communication
- Easier debugging und logging

❌ **Negativ**:
- Weniger flexible Skalierung
- Single point of failure
- Tighter coupling zwischen Services
- Schwieriger zu horizontally skalieren

### Umsetzung
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

## ADR-005: Tailwind CSS für Styling

### Status: Accepted
### Datum: 2024-01-15
### Entscheider: System Architect

### Kontext
HomeGrow v3 benötigt ein modernes, responsive Design-System. Die Wahl des CSS-Frameworks beeinflusst Development-Speed, Bundle-Size und Design-Konsistenz.

### Entscheidung
Wir verwenden **Tailwind CSS** als Utility-First CSS Framework.

### Alternativen Betrachtet
1. **Styled Components**: CSS-in-JS
2. **SCSS/SASS**: Preprocessor
3. **Bootstrap**: Component Framework
4. **Vanilla CSS**: Custom CSS

### Begründung
- **Utility-First**: Schnelle UI-Entwicklung
- **Bundle Optimization**: Unused CSS wird automatisch entfernt
- **Responsive Design**: Mobile-first Breakpoint-System
- **Customization**: Vollständig konfigurierbar
- **Svelte Integration**: Excellent Svelte support

### Konsequenzen
✅ **Positiv**:
- Sehr schnelle UI-Entwicklung
- Konsistentes Design-System
- Optimale Bundle-Größe (purged CSS)
- Excellent mobile support

❌ **Negativ**:
- Lernkurve für Team
- HTML classes können verbose werden
- Requires build-time optimization

### Umsetzung
```svelte
<!-- Tailwind utility classes -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-4">
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md">
    <!-- Component content -->
  </div>
</div>
```

## ADR-006: MQTT für IoT-Kommunikation

### Status: Accepted
### Datum: 2024-01-15
### Entscheider: System Architect

### Kontext
HomeGrow v3 muss mit ESP32-basierten IoT-Devices kommunizieren. Das Kommunikations-Protokoll beeinflusst Reliability, Performance und Integration-Complexity.

### Entscheidung
Wir verwenden **MQTT v3.1.1** als primäres IoT-Kommunikationsprotokoll.

### Alternativen Betrachtet
1. **HTTP REST API**: Request/Response-based
2. **WebSocket**: Direct WebSocket zu Devices
3. **CoAP**: Constrained Application Protocol
4. **LoRaWAN**: Long-range, low-power
5. **Zigbee**: Mesh networking

### Begründung
- **IoT Standard**: MQTT ist der de-facto Standard für IoT
- **Publish/Subscribe**: Efficient für Sensor-Daten
- **QoS Levels**: Garantierte Message-Delivery möglich
- **Broker-based**: Entkoppelte Device-Kommunikation
- **Umbrel Integration**: Mosquitto als Service verfügbar

### Konsequenzen
✅ **Positiv**:
- Proven IoT communication standard
- Efficient für Time-Series data
- Built-in reliability features
- Good ESP32 support

❌ **Negativ**:
- Requires MQTT broker dependency
- Additional layer of complexity
- Network overhead für kleine Messages

### Umsetzung
```typescript
// MQTT topics structure
const topics = {
  sensorData: 'homegrow/devices/{device_id}/sensors/{sensor_type}',
  commands: 'homegrow/devices/{device_id}/commands',
  status: 'homegrow/devices/{device_id}/status'
};

// ESP32 sensor data message
{
  "device_id": "HG-001",
  "sensor_type": "ph",
  "value": 6.2,
  "raw_value": 2048,
  "quality": "good",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## ADR-007: TypeScript für Type Safety

### Status: Accepted
### Datum: 2024-01-15
### Entscheider: System Architect

### Kontext
HomeGrow v3 ist eine komplexe Anwendung mit APIs, Real-time Data und komplexer Business-Logic. Type Safety reduziert Bugs und verbessert Developer Experience.

### Entscheidung
Wir verwenden **TypeScript** für das gesamte Projekt (Frontend + Backend).

### Alternativen Betrachtet
1. **JavaScript + JSDoc**: Type hints via comments
2. **Flow**: Facebook's type checker
3. **ReScript**: Functional programming language
4. **Vanilla JavaScript**: No type checking

### Begründung
- **Type Safety**: Compile-time error detection
- **Developer Experience**: Excellent IDE support
- **API Contracts**: Shared interfaces zwischen Frontend/Backend
- **Refactoring**: Safe refactoring mit type checking
- **Svelte Support**: Native TypeScript support

### Konsequenzen
✅ **Positiv**:
- Weniger runtime errors
- Better developer experience
- Self-documenting code
- Easier refactoring

❌ **Negativ**:
- Build-time overhead
- Learning curve for team
- More verbose code

### Umsetzung
```typescript
// Shared type definitions
interface Device {
  device_id: string;
  name: string;
  status: 'online' | 'offline' | 'error';
  config: DeviceConfig;
  last_seen?: Date;
}

interface SensorData {
  device_id: string;
  sensor_type: 'ph' | 'tds' | 'temperature';
  values: {
    raw: number;
    calibrated: number;
    filtered: number;
  };
  timestamp: Date;
}
```

## ADR-008: Bitsperity Service Dependencies

### Status: Accepted
### Datum: 2024-01-15
### Entscheider: System Architect

### Kontext
HomeGrow v3 benötigt Database, MQTT und Service Discovery. Die Wahl zwischen eigene Services vs. externe Dependencies beeinflusst Deployment und Wartung.

### Entscheidung
Wir nutzen **Bitsperity Services** als Dependencies (MongoDB, Beacon, Mosquitto).

### Alternativen Betrachtet
1. **Embedded Services**: SQLite, embedded MQTT
2. **Cloud Services**: MongoDB Atlas, AWS IoT
3. **Self-hosted**: Separate Docker containers
4. **Mixed Approach**: Teilweise embedded, teilweise external

### Begründung
- **Shared Infrastructure**: Andere Bitsperity Apps nutzen gleiche Services
- **Resource Efficiency**: Shared containers sparen Resources
- **Maintenance**: Zentrale Wartung der Base-Services
- **Umbrel Integration**: Services sind bereits Umbrel-kompatibel
- **Development Efficiency**: MCP-Integration für Development

### Konsequenzen
✅ **Positiv**:
- Shared infrastructure costs
- Professional service management
- Easier development mit MCP
- Consistent service versions

❌ **Negativ**:
- Dependency auf Bitsperity Services
- Less control über service configuration
- Potential conflicts mit anderen Apps

### Umsetzung
```yaml
# docker-compose.yml dependencies
depends_on:
  bitsperity-mongodb:
    condition: service_healthy
  mosquitto:
    condition: service_started  
  bitsperity-beacon:
    condition: service_started
```

## ADR-009: Progressive Web App (PWA)

### Status: Accepted
### Datum: 2024-01-15
### Entscheider: System Architect

### Kontext
HomeGrow v3 muss auf Mobile-Devices optimal funktionieren. Die Wahl zwischen Native App, Hybrid App oder PWA beeinflusst Development-Effort und User Experience.

### Entscheidung
Wir implementieren eine **Progressive Web App (PWA)** mit Service Workers.

### Alternativen Betrachtet
1. **Native Apps**: iOS/Android apps
2. **React Native**: Cross-platform framework
3. **Capacitor**: Web-to-native wrapper
4. **Responsive Web**: Nur responsive design

### Begründung
- **Single Codebase**: Web-App funktioniert als Mobile-App
- **Automatic Updates**: Keine App-Store Updates nötig
- **Offline Functionality**: Service Workers für offline support
- **Push Notifications**: Native-like notifications
- **Installation**: Add-to-homescreen functionality

### Konsequenzen
✅ **Positiv**:
- Kein App-Store approval process
- Automatic updates für alle Benutzer
- Plattform-übergreifend (iOS/Android)
- Lower development overhead

❌ **Negativ**:
- Limitierte native features
- iOS PWA limitations
- Requires service worker complexity

### Umsetzung
```typescript
// PWA manifest
{
  "name": "HomeGrow v3",
  "short_name": "HomeGrow",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1f2937",
  "theme_color": "#10b981",
  "icons": [
    {
      "src": "/icons/192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

## ADR-010: Minimal Database Schema (3 Collections)

### Status: Accepted
### Datum: 2024-01-15
### Entscheider: System Architect

### Kontext
HomeGrow v3 benötigt eine Database-Schema für Devices, Sensor-Daten und Programs. Die Wahl zwischen normalisierten vs. denormalisierten Schema beeinflusst Performance und Komplexität.

### Entscheidung
Wir verwenden eine **minimalistische Schema** mit nur 3 MongoDB Collections.

### Alternativen Betrachtet
1. **Normalized Schema**: Viele kleine Collections
2. **Single Collection**: Alles in einer Collection
3. **SQL Database**: Relationale Struktur
4. **Time-Series DB**: Spezialisierte DB für Sensor-Daten

### Begründung
- **Simplicity**: Weniger Collections = einfachere Queries
- **Performance**: Denormalized structure für IoT-Performance
- **MongoDB Strengths**: Nutzt Document-Store Vorteile
- **Embedded Documents**: Related data in same document
- **Aggregation Pipelines**: Powerful query capabilities

### Konsequenzen
✅ **Positiv**:
- Einfachere queries und joins
- Better performance für IoT-workloads
- Weniger database round-trips
- Natural document structure

❌ **Negativ**:
- Potentielle data duplication
- Larger documents
- More complex updates

### Umsetzung
```typescript
// 3-collection schema
collections = {
  devices: "Device registration & configuration",
  sensor_data: "Time-series sensor readings", 
  program_templates: "Growth programs & instances"
};
```

## Zusammenfassung Technischer Entscheidungen

### Gewählter Tech Stack
```typescript
const techStack = {
  framework: "SvelteKit",
  language: "TypeScript", 
  styling: "Tailwind CSS",
  database: "MongoDB (direct driver)",
  realtime: "Native WebSocket",
  iot: "MQTT v3.1.1",
  mobile: "Progressive Web App",
  deployment: "Single Container",
  dependencies: ["bitsperity-mongodb", "mosquitto", "bitsperity-beacon"]
};
```

### Architektur-Prinzipien
1. **Simplicity over Complexity**: Minimaler Tech Stack
2. **Performance over Features**: Optimiert für IoT-Workloads  
3. **Developer Experience**: Excellent DX mit TypeScript/Svelte
4. **Mobile-First**: PWA mit offline capabilities
5. **Umbrel-Native**: Designed for Umbrel ecosystem

### Quality Gates
- [ ] Alle ADRs sind dokumentiert und akzeptiert
- [ ] Tech Stack ist in Implementation Guide übertragen
- [ ] Performance Targets sind mit gewähltem Stack erreichbar
- [ ] Umbrel Integration ist vollständig geplant
- [ ] Mobile PWA Requirements sind erfüllbar

Diese technischen Entscheidungen bilden das Foundation für eine performante, wartbare und benutzerfreundliche HomeGrow v3 Implementierung. 