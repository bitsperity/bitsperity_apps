# HomeGrow Client v3

## Übersicht

HomeGrow Client v3 ist eine komplette Neuentwicklung des ESP32-basierten Clients für das HomeGrow System. Der Client bietet eine modulare Architektur mit erweiterter MQTT-Kommunikation und fortschrittlichen Automatisierungsfunktionen.

## Aktueller Implementierungsstatus

### ✅ Implementiert

#### Core-System
- **Logger**: Vollständiges Logging-System mit verschiedenen Log-Levels
  - Serial-Ausgabe mit Timestamps
  - MQTT-Logging-Vorbereitung
  - Strukturierte Log-Einträge
  
- **Types**: Alle grundlegenden Datentypen definiert
  - System-States
  - Sensor-Types
  - Actuator-Types und States
  - Command-Status
  - Safety-Levels

#### Konfigurationssystem
- **Config**: Vollständige Konfigurationsstruktur
  - WiFi-Konfiguration
  - MQTT-Konfiguration
  - Sensor-Konfigurationen (pH, TDS)
  - Aktor-Konfigurationen (7 Pumpen)
  - Safety-Konfiguration
  - System-Konfiguration
  
- **Default Config**: Komplette Default-Konfiguration als JSON

#### Netzwerk
- **WiFiManager**: Vollständige WiFi-Verwaltung
  - Automatische Verbindung
  - Event-basierte Status-Updates
  - Reconnection-Logic
  - Static IP Support
  - Status-Monitoring (RSSI, IP, MAC)

- **MQTTClient**: Vollständig implementiert
  - Connection-Management mit Auto-Reconnect
  - Topic-Schema v3 implementiert
  - Publishing für Sensoren, Commands, Heartbeat, Status, Logs
  - Subscription für Commands und Config
  - Message-Callback-System
  - Statistiken für Monitoring

- **MDNSDiscovery**: mDNS Broker-Discovery
  - Automatische MQTT-Broker-Suche
  - Fallback zu konfiguriertem Host
  - Service-Discovery für "_mqtt._tcp"

#### State Machine
- **BaseState**: Abstrakte Basis-Klasse für States
  - State-Lifecycle (enter, exit, update)
  - Event-Handling
  - Timeout-Management
  - Status-Reporting

#### Sensoren
- **BaseSensor**: Abstrakte Sensor-Basisklasse implementiert
  - Kalibrierungs-Support (Interface definiert)
  - Filter-Support (Interface definiert)
  - Qualitäts-Bewertung
  - Status-Reporting
  
- **PHSensor**: Vollständig implementiert
  - Multi-Sample-Reading (10 Samples)
  - Kalibrierungs-Support
  - Noise-Filter-Support
  - pH-Validierung (0-14)
  
- **TDSSensor**: Vollständig implementiert
  - Multi-Sample-Reading (10 Samples)
  - Kalibrierungs-Support
  - Noise-Filter-Support
  - Temperatur-Kompensation
  - TDS-Validierung (0-5000 ppm)

#### Aktoren
- **BaseActuator**: Abstrakte Aktor-Basisklasse implementiert
  - State-Management (IDLE, ACTIVE, COOLDOWN, ERROR, DISABLED)
  - Cooldown-Verwaltung
  - Runtime-Tracking
  - Safety-Checks
  - Status-Reporting
  
- **Pump**: Basis-Pumpenklasse implementiert
  - Flow-Rate-basierte Dosierung
  - Auto-Deaktivierung nach Zeit
  - Hardware-Control (GPIO)
  - Volumen-zu-Zeit-Berechnung
  - Überlaufschutz

### 🚧 In Arbeit / Nächste Schritte

1. **Kalibrierungs-System**
   - LinearCalibration
   - MultiPointCalibration
   - Factory-Methode

2. **Filter-System**
   - MovingAverageFilter
   - ExponentialFilter
   - Factory-Methode

3. **Konkrete Pumpen-Implementierungen**
   - WaterPump
   - AirPump
   - DosingPump

4. **Manager-Klassen**
   - SensorManager
   - ActuatorManager
   - CommandProcessor
   - SafetyManager

5. **State Machine Implementation**
   - StateMachine Klasse
   - Konkrete States (Init, WiFi, MQTT, Running, etc.)

6. **Command-System**
   - BaseCommand Implementation
   - Konkrete Command-Klassen
   - Command-Processing

7. **Application-Klasse**
   - Haupt-Orchestrierung
   - Manager-Integration
   - State Machine Integration

## Test-Features in main.cpp

Die aktuelle main.cpp enthält Test-Features:
- Automatische WiFi-Verbindung
- mDNS Broker-Discovery
- MQTT-Verbindung mit Auto-Reconnect
- Heartbeat alle 30 Sekunden mit System-Info
- Simulierte Sensor-Daten (pH und TDS) alle 5 Sekunden
- MQTT-Message-Handling vorbereitet

## Pin-Belegung

| Komponente | Pin | Typ |
|------------|-----|-----|
| pH-Sensor | 34 | Analog Input |
| TDS-Sensor | 35 | Analog Input |
| Wasserpumpe | 16 | Digital Output |
| Luftpumpe | 17 | Digital Output |
| pH-Down Pumpe | 18 | Digital Output |
| pH-Up Pumpe | 19 | Digital Output |
| Nutrient A Pumpe | 20 | Digital Output |
| Nutrient B Pumpe | 21 | Digital Output |
| Cal-Mag Pumpe | 22 | Digital Output |

## Kompilierung

```bash
# Projekt kompilieren
pio run

# Auf ESP32 hochladen
pio run --target upload

# Serial Monitor öffnen
pio device monitor
```

## Konfiguration

Die WiFi-Credentials müssen in `src/main.cpp` angepasst werden:

```cpp
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
```

## Memory-Usage

Aktueller Stand nach Sensor/Aktor-Implementierung:
- RAM: 14.9% (48KB von 320KB)
- Flash: 63.2% (828KB von 1280KB)

## MQTT Topics (v3 Schema)

### Sensor-Daten
- `homegrow/devices/{device_id}/sensors/ph`
- `homegrow/devices/{device_id}/sensors/tds`

Payload-Format:
```json
{
  "timestamp": 123456789,
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
```

### Commands
- `homegrow/devices/{device_id}/commands` (Subscribe)
- `homegrow/devices/{device_id}/commands/response` (Publish)

### System
- `homegrow/devices/{device_id}/heartbeat`
- `homegrow/devices/{device_id}/status`
- `homegrow/devices/{device_id}/logs`

### Konfiguration
- `homegrow/devices/{device_id}/config/request`
- `homegrow/devices/{device_id}/config/response`

## Architektur

```
Application
├── ConfigManager
├── StateMachine
│   └── States (Init, WiFi, MQTT, Running, etc.)
├── SensorManager
│   ├── PHSensor (✓)
│   └── TDSSensor (✓)
├── ActuatorManager
│   ├── WaterPump
│   ├── AirPump
│   └── DosingPumps[5]
├── CommandProcessor
├── SafetyManager
├── WiFiManager (✓)
├── MQTTClient (✓)
├── MDNSDiscovery (✓)
└── Logger (✓)
```

## Implementierte Klassen-Details

### Sensoren
- **PHSensor**: 
  - Liest analoge Werte von Pin 34
  - Mittelt über 10 Samples
  - Unterstützt Multi-Point-Kalibrierung
  - Validiert pH-Werte (0-14)
  
- **TDSSensor**:
  - Liest analoge Werte von Pin 35
  - Mittelt über 10 Samples
  - Temperatur-Kompensation (25°C Standard)
  - Validiert TDS-Werte (0-5000 ppm)

### Aktoren
- **Pump**:
  - GPIO-basierte Steuerung
  - Flow-Rate in ml/s konfigurierbar
  - Automatische Deaktivierung nach Zeit
  - Cooldown-Periode zwischen Aktivierungen
  - Runtime-Tracking für Wartung

## Entwicklungshinweise

- Der Code folgt einer modularen Architektur
- Jede Komponente hat ihre eigene Header/Implementation
- Extensive Logging für Remote-Debugging
- Defensive Programmierung mit Safety-Checks
- Memory-effiziente Implementierung mit DynamicJsonDocument
- Event-driven Design mit Callbacks
- Interfaces für Erweiterbarkeit (Calibration, NoiseFilter)

## Nächste Entwicklungsschritte

1. Kalibrierungs-Klassen implementieren
2. Filter-Klassen implementieren  
3. Manager-Klassen erstellen
4. State Machine vervollständigen
5. Command-System implementieren
6. Application-Klasse für Orchestrierung
7. OTA-Updates aktivieren
8. Erweiterte Safety-Features

## Testing

Das System kann bereits getestet werden:
1. WiFi-Credentials in main.cpp eintragen
2. Code auf ESP32 flashen
3. Serial Monitor beobachten
4. MQTT-Broker sollte Heartbeats und simulierte Sensor-Daten empfangen
5. Topics: `homegrow/devices/homegrow_client_001/heartbeat` und `.../sensors/ph|tds` 