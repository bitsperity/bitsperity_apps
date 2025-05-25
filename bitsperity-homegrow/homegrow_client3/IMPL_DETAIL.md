# HomeGrow Client v3 - Detaillierte Implementierungsstrategie

## Übersicht

Diese Implementierungsstrategie beschreibt den effizientesten Weg zur Umsetzung des HomeGrow Client v3 ohne Hardware-Tests. Der Fokus liegt auf strukturierter Entwicklung, Validierung durch Code-Review und Simulation, sowie einer reibungslosen Migration am Sonntag.

## Implementierungsphilosophie

### Grundprinzipien
1. **Bottom-Up Development**: Basis-Klassen zuerst, dann Integration
2. **Interface-First**: Abstrakte Interfaces definieren, dann implementieren
3. **Clean Architecture**: Komplett neue v3-Architektur ohne Legacy-Code
4. **Fail-Safe Design**: Defensive Programmierung mit umfangreichen Checks
5. **Logging-First**: Jede Aktion wird geloggt für Remote-Debugging

### Validierungsstrategie ohne Hardware
1. **Statische Code-Analyse**: Compiler-Checks und Linting
2. **JSON-Schema-Validierung**: MQTT-Payloads gegen Schema prüfen
3. **Simulation durch Serial-Output**: Alle Hardware-Aktionen loggen
4. **Memory-Profiling**: Heap-Usage simulieren und überwachen
5. **Timing-Simulation**: Delays und Timeouts in Logs dokumentieren

## Phase 1: Projekt-Setup und Basis-Infrastruktur (Tag 1)

### 1.1 PlatformIO Projekt initialisieren
```bash
# Projekt-Struktur erstellen
mkdir -p homegrow_client3/{src,lib,test,docs}
cd homegrow_client3
pio init --board esp32dev
```

### 1.2 platformio.ini konfigurieren
```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
lib_deps = 
    bblanchon/ArduinoJson@^6.21.3
    knolleary/PubSubClient@^2.8
    arduino-libraries/WiFi@^1.2.7
    ESP32 Arduino Core
build_flags = 
    -DCORE_DEBUG_LEVEL=4
    -DLOG_LOCAL_LEVEL=ESP_LOG_DEBUG
```

### 1.3 Basis-Header erstellen
**Priorität: KRITISCH** - Alle anderen Klassen hängen davon ab

#### src/core/Types.h
```cpp
#ifndef TYPES_H
#define TYPES_H

#include <Arduino.h>
#include <ArduinoJson.h>

// Basis-Typen für das gesamte System
enum class SystemState {
    INIT,
    CONNECTING_WIFI,
    DISCOVERING_BROKER,
    CONNECTING_MQTT,
    CONFIG_REQUEST,
    RUNNING,
    ERROR,
    EMERGENCY_STOP
};

enum class SensorType {
    PH,
    TDS
};

enum class ActuatorType {
    WATER_PUMP,
    AIR_PUMP,
    DOSING_PUMP
};

enum class CommandStatus {
    PENDING,
    EXECUTING,
    COMPLETED,
    FAILED,
    TIMEOUT
};

struct SensorReading {
    float raw;
    float calibrated;
    float filtered;
    unsigned long timestamp;
    String quality;
    bool calibration_valid;
};

struct CommandResult {
    String command_id;
    CommandStatus status;
    String error_message;
    JsonObject result_data;
    unsigned long execution_time_ms;
};

#endif
```

#### src/core/Logger.h
```cpp
#ifndef LOGGER_H
#define LOGGER_H

#include <Arduino.h>
#include <ArduinoJson.h>

enum class LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3
};

class Logger {
private:
    static LogLevel current_level;
    static bool mqtt_enabled;
    static String device_id;
    
public:
    static void init(const String& device_id, LogLevel level = LogLevel::INFO);
    static void setMQTTEnabled(bool enabled);
    
    static void debug(const String& message, const String& component = "");
    static void info(const String& message, const String& component = "");
    static void warn(const String& message, const String& component = "");
    static void error(const String& message, const String& component = "");
    
    static void logCommand(const String& command_id, const String& command, const JsonObject& params);
    static void logSensorReading(SensorType type, const SensorReading& reading);
    static void logSystemEvent(const String& event, const JsonObject& data = JsonObject());
    
private:
    static void log(LogLevel level, const String& message, const String& component);
    static String levelToString(LogLevel level);
    static JsonDocument createLogEntry(LogLevel level, const String& message, const String& component);
};

#endif
```

### 1.4 Validierung Phase 1
- [ ] Projekt kompiliert ohne Fehler
- [ ] Logger-Tests über Serial funktionieren
- [ ] Basis-Typen sind vollständig definiert
- [ ] Memory-Usage ist unter 10% (ca. 50KB)

## Phase 2: Konfigurationssystem (Tag 1-2)

### 2.1 Konfigurationsklassen implementieren
**Priorität: HOCH** - Alle Module benötigen Konfiguration

#### src/config/Config.h
```cpp
#ifndef CONFIG_H
#define CONFIG_H

#include <ArduinoJson.h>
#include "core/Types.h"

struct WiFiConfig {
    String ssid;
    String password;
    String hostname;
    String static_ip;  // Optional
    String dns_servers[2];
};

struct MQTTConfig {
    bool broker_discovery_enabled;
    String service_name;
    String fallback_host;
    int fallback_port;
    String username;
    String password;
    int qos;
    bool retain;
    int keepalive;
    bool clean_session;
};

struct SensorConfig {
    bool enabled;
    int pin;
    JsonObject calibration;
    JsonObject noise_filter;
    JsonObject publishing;
};

struct ActuatorConfig {
    bool enabled;
    int pin;
    String type;
    float flow_rate_ml_per_sec;
    int max_runtime_sec;
    int cooldown_sec;
    JsonObject scheduled;
    String substance;  // Für Dosierpumpen
    String concentration;
};

struct SafetyConfig {
    float ph_min;
    float ph_max;
    float tds_max;
    int pump_max_runtime_sec;
    int pump_cooldown_sec;
    float outlier_threshold;
    bool plausibility_checks;
};

class Config {
private:
    JsonDocument config_doc;
    bool loaded;
    
public:
    Config();
    
    // Basis-Konfiguration
    String device_id;
    String device_name;
    String location;
    String firmware_version;
    String hardware_version;
    
    // Modul-Konfigurationen
    WiFiConfig wifi;
    MQTTConfig mqtt;
    SafetyConfig safety;
    
    // Sensor-Konfigurationen
    SensorConfig ph_sensor;
    SensorConfig tds_sensor;
    
    // Aktor-Konfigurationen
    ActuatorConfig water_pump;
    ActuatorConfig air_pump;
    ActuatorConfig dosing_pumps[5];  // ph_down, ph_up, nutrient_a, nutrient_b, cal_mag
    
    // Methoden
    bool loadFromJson(const String& json);
    bool loadDefaults();
    String toJson() const;
    bool validate() const;
    
    // Getter für spezifische Konfigurationen
    ActuatorConfig* getDosingPump(const String& pump_id);
    SensorConfig* getSensor(SensorType type);
};

#endif
```

#### src/config/ConfigManager.h
```cpp
#ifndef CONFIG_MANAGER_H
#define CONFIG_MANAGER_H

#include "Config.h"
#include "core/Logger.h"

class ConfigManager {
private:
    Config config;
    bool config_loaded;
    unsigned long last_config_request;
    static const unsigned long CONFIG_REQUEST_INTERVAL = 30000; // 30 Sekunden
    
public:
    ConfigManager();
    
    bool loadConfig();
    bool saveConfig();
    bool requestConfigFromServer();
    bool updateConfig(const String& json);
    
    const Config& getConfig() const { return config; }
    bool isConfigLoaded() const { return config_loaded; }
    
    // Spezifische Konfiguration-Updates
    bool updateSensorConfig(SensorType type, const JsonObject& sensor_config);
    bool updateActuatorConfig(const String& actuator_id, const JsonObject& actuator_config);
    bool updateSafetyConfig(const JsonObject& safety_config);
    
    // Validierung
    bool validateConfig() const;
    String getConfigErrors() const;
};

#endif
```

### 2.2 Default-Konfiguration definieren
#### src/config/default_config.h
```cpp
#ifndef DEFAULT_CONFIG_H
#define DEFAULT_CONFIG_H

// HomeGrow Client v3 Default-Konfiguration
const char* DEFAULT_CONFIG_JSON = R"({
  "device": {
    "id": "homegrow_client_001",
    "name": "HomeGrow Client v3",
    "location": "Gewächshaus",
    "firmware_version": "3.0.0",
    "hardware_version": "1.0"
  },
  "wifi": {
    "ssid": "",
    "password": "",
    "hostname": "homegrow-client-001",
    "static_ip": null,
    "dns_servers": ["8.8.8.8", "8.8.4.4"]
  },
  "mqtt": {
    "broker_discovery": {
      "enabled": true,
      "service_name": "_mqtt._tcp",
      "fallback_host": "192.168.1.100",
      "fallback_port": 1883
    },
    "auth": {
      "username": "homegrow_client",
      "password": ""
    },
    "qos": 1,
    "retain": false,
    "keepalive": 60,
    "clean_session": true
  },
  "sensors": {
    "ph": {
      "enabled": true,
      "pin": 34,
      "calibration": {
        "type": "multi_point",
        "points": [
          {"raw": 2252, "ph": 4.0},
          {"raw": 1721, "ph": 7.0}
        ]
      },
      "noise_filter": {
        "enabled": true,
        "type": "moving_average",
        "window_size": 10,
        "outlier_threshold": 2.0
      },
      "publishing": {
        "rate_hz": 1.0,
        "publish_raw": true,
        "publish_calibrated": true,
        "publish_filtered": true
      }
    },
    "tds": {
      "enabled": true,
      "pin": 35,
      "calibration": {
        "type": "single_point",
        "reference_point": {"raw": 1156, "tds": 342}
      },
      "noise_filter": {
        "enabled": true,
        "type": "exponential",
        "alpha": 0.1,
        "outlier_threshold": 100.0
      },
      "publishing": {
        "rate_hz": 0.5,
        "publish_raw": true,
        "publish_calibrated": true,
        "publish_filtered": true
      }
    }
  },
  "actuators": {
    "water_pump": {
      "enabled": true,
      "pin": 16,
      "type": "relay",
      "flow_rate_ml_per_sec": 50.0,
      "max_runtime_sec": 300,
      "cooldown_sec": 60
    },
    "air_pump": {
      "enabled": true,
      "pin": 17,
      "type": "relay",
      "max_runtime_sec": 1800,
      "cooldown_sec": 30
    },
    "dosing_pumps": [
      {
        "id": "ph_down",
        "enabled": true,
        "pin": 18,
        "type": "peristaltic",
        "flow_rate_ml_per_sec": 0.5,
        "max_runtime_sec": 60,
        "cooldown_sec": 300,
        "substance": "pH Down"
      },
      {
        "id": "ph_up",
        "enabled": true,
        "pin": 19,
        "type": "peristaltic",
        "flow_rate_ml_per_sec": 0.5,
        "max_runtime_sec": 60,
        "cooldown_sec": 300,
        "substance": "pH Up"
      },
      {
        "id": "nutrient_a",
        "enabled": true,
        "pin": 20,
        "type": "peristaltic",
        "flow_rate_ml_per_sec": 1.0,
        "max_runtime_sec": 120,
        "cooldown_sec": 60,
        "substance": "Nutrient A"
      },
      {
        "id": "nutrient_b",
        "enabled": true,
        "pin": 21,
        "type": "peristaltic",
        "flow_rate_ml_per_sec": 1.0,
        "max_runtime_sec": 120,
        "cooldown_sec": 60,
        "substance": "Nutrient B"
      },
      {
        "id": "cal_mag",
        "enabled": true,
        "pin": 22,
        "type": "peristaltic",
        "flow_rate_ml_per_sec": 0.8,
        "max_runtime_sec": 90,
        "cooldown_sec": 120,
        "substance": "Cal-Mag"
      }
    ]
  },
  "safety": {
    "emergency_stop_conditions": {
      "ph_min": 4.0,
      "ph_max": 8.5,
      "tds_max": 2000
    },
    "pump_protection": {
      "max_runtime_sec": 300,
      "cooldown_sec": 60
    },
    "sensor_validation": {
      "outlier_threshold": 2.0,
      "plausibility_checks": true
    }
  }
})";

#endif
```

### 2.3 Validierung Phase 2
- [ ] Konfiguration lädt korrekt aus JSON
- [ ] Default-Konfiguration ist vollständig und valide
- [ ] Validierung erkennt fehlerhafte Konfigurationen
- [ ] Memory-Usage bleibt unter 20% (ca. 100KB)

## Phase 3: Netzwerk-Layer (Tag 2-3)

### 3.1 WiFi-Manager implementieren
**Priorität: HOCH** - Basis für alle Kommunikation

#### src/network/WiFiManager.h
```cpp
#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>
#include "config/Config.h"
#include "core/Logger.h"

enum class WiFiStatus {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    FAILED
};

class WiFiManager {
private:
    WiFiConfig config;
    WiFiStatus status;
    unsigned long last_connection_attempt;
    int connection_attempts;
    static const int MAX_CONNECTION_ATTEMPTS = 5;
    static const unsigned long CONNECTION_TIMEOUT = 10000; // 10 Sekunden
    
public:
    WiFiManager();
    
    bool init(const WiFiConfig& wifi_config);
    bool connect();
    bool isConnected() const;
    WiFiStatus getStatus() const { return status; }
    
    // Monitoring
    int getRSSI() const;
    String getIP() const;
    String getMAC() const;
    String getSSID() const;
    
    // Reconnection
    void handleDisconnection();
    bool shouldReconnect() const;
    
    // Status für Heartbeat
    JsonObject getStatusJson() const;
};

#endif
```

### 3.2 MQTT-Client implementieren
**Priorität: KRITISCH** - Zentrale Kommunikation

#### src/network/MQTTClient.h
```cpp
#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

#include <PubSubClient.h>
#include <WiFiClient.h>
#include "config/Config.h"
#include "core/Logger.h"
#include "core/Types.h"

class MQTTClient {
private:
    WiFiClient wifi_client;
    PubSubClient mqtt_client;
    MQTTConfig config;
    String device_id;
    
    bool connected;
    unsigned long last_connection_attempt;
    unsigned long last_heartbeat;
    unsigned long messages_sent;
    unsigned long messages_failed;
    
    // Topic-Templates
    String base_topic;
    String sensor_topic_template;
    String command_topic;
    String command_response_topic;
    String heartbeat_topic;
    String status_topic;
    String config_request_topic;
    String config_response_topic;
    
    // Callback-Funktionen
    std::function<void(String, String)> message_callback;
    
public:
    MQTTClient();
    
    bool init(const MQTTConfig& mqtt_config, const String& device_id);
    bool connect();
    bool isConnected() const { return connected; }
    void disconnect();
    
    // Publishing
    bool publishSensorData(SensorType type, const SensorReading& reading);
    bool publishCommandResponse(const CommandResult& result);
    bool publishHeartbeat(const JsonObject& heartbeat_data);
    bool publishStatus(const JsonObject& status_data);
    bool publishLog(const JsonObject& log_entry);
    bool requestConfig();
    
    // Subscription
    bool subscribeToCommands();
    bool subscribeToConfig();
    void setMessageCallback(std::function<void(String, String)> callback);
    
    // Maintenance
    void loop();
    bool shouldReconnect() const;
    void handleDisconnection();
    
    // Statistics für Heartbeat
    JsonObject getStatistics() const;
    
private:
    void onMessage(char* topic, byte* payload, unsigned int length);
    String buildTopic(const String& template_topic, const String& sensor_id = "") const;
    bool publish(const String& topic, const String& payload, bool retain = false);
};

#endif
```

### 3.3 mDNS Discovery implementieren
#### src/network/MDNSDiscovery.h
```cpp
#ifndef MDNS_DISCOVERY_H
#define MDNS_DISCOVERY_H

#include <ESPmDNS.h>
#include "core/Logger.h"

struct BrokerInfo {
    String host;
    int port;
    bool found;
};

class MDNSDiscovery {
private:
    String service_name;
    BrokerInfo discovered_broker;
    unsigned long last_discovery_attempt;
    static const unsigned long DISCOVERY_TIMEOUT = 5000; // 5 Sekunden
    
public:
    MDNSDiscovery();
    
    bool init(const String& service_name);
    BrokerInfo discoverBroker();
    bool isDiscoveryComplete() const { return discovered_broker.found; }
    
    const BrokerInfo& getBrokerInfo() const { return discovered_broker; }
};

#endif
```

### 3.4 Validierung Phase 3
- [ ] WiFi-Verbindung simuliert (Logs zeigen Verbindungsversuche)
- [ ] MQTT-Topics korrekt generiert (v3 Schema)
- [ ] mDNS-Discovery implementiert
- [ ] Reconnection-Logic funktioniert
- [ ] Memory-Usage unter 30% (ca. 150KB)

## Phase 4: Sensor-Framework (Tag 3-4)

### 4.1 Basis-Sensor-Klassen
**Priorität: HOCH** - Datenerfassung ist zentral

#### src/sensors/BaseSensor.h
```cpp
#ifndef BASE_SENSOR_H
#define BASE_SENSOR_H

#include "core/Types.h"
#include "config/Config.h"
#include "sensors/calibration/Calibration.h"
#include "sensors/filters/NoiseFilter.h"

class BaseSensor {
protected:
    SensorType type;
    SensorConfig config;
    std::unique_ptr<Calibration> calibration;
    std::unique_ptr<NoiseFilter> filter;
    
    SensorReading last_reading;
    unsigned long last_read_time;
    bool initialized;
    
public:
    BaseSensor(SensorType sensor_type);
    virtual ~BaseSensor() = default;
    
    virtual bool init(const SensorConfig& sensor_config) = 0;
    virtual SensorReading read() = 0;
    virtual bool calibrate(const JsonArray& calibration_points) = 0;
    
    // Getters
    SensorType getType() const { return type; }
    const SensorReading& getLastReading() const { return last_reading; }
    bool isInitialized() const { return initialized; }
    
    // Status für Monitoring
    virtual JsonObject getStatusJson() const;
    virtual bool isHealthy() const;
    
protected:
    virtual float readRaw() = 0;
    float applyCalibriation(float raw_value);
    float applyFilter(float calibrated_value);
    bool validateReading(float value) const;
    void updateReadingQuality(SensorReading& reading) const;
};

#endif
```

#### src/sensors/PHSensor.h
```cpp
#ifndef PH_SENSOR_H
#define PH_SENSOR_H

#include "BaseSensor.h"

class PHSensor : public BaseSensor {
private:
    int pin;
    static const int SAMPLE_COUNT = 10;
    static const float PH_MIN = 0.0;
    static const float PH_MAX = 14.0;
    
public:
    PHSensor();
    
    bool init(const SensorConfig& sensor_config) override;
    SensorReading read() override;
    bool calibrate(const JsonArray& calibration_points) override;
    
protected:
    float readRaw() override;
    
private:
    float readAverageRaw();
    bool isValidPH(float ph_value) const;
};

#endif
```

#### src/sensors/TDSSensor.h
```cpp
#ifndef TDS_SENSOR_H
#define TDS_SENSOR_H

#include "BaseSensor.h"

class TDSSensor : public BaseSensor {
private:
    int pin;
    static const int SAMPLE_COUNT = 10;
    static const float TDS_MIN = 0.0;
    static const float TDS_MAX = 5000.0;
    static const float TEMPERATURE_COMPENSATION = 25.0; // Standard-Temperatur
    
public:
    TDSSensor();
    
    bool init(const SensorConfig& sensor_config) override;
    SensorReading read() override;
    bool calibrate(const JsonArray& calibration_points) override;
    
protected:
    float readRaw() override;
    
private:
    float readAverageRaw();
    float compensateTemperature(float tds_value) const;
    bool isValidTDS(float tds_value) const;
};

#endif
```

### 4.2 Kalibrierungs-System
#### src/sensors/calibration/Calibration.h
```cpp
#ifndef CALIBRATION_H
#define CALIBRATION_H

#include <ArduinoJson.h>

class Calibration {
public:
    virtual ~Calibration() = default;
    virtual float calibrate(float raw_value) const = 0;
    virtual bool loadFromJson(const JsonObject& calibration_data) = 0;
    virtual JsonObject toJson() const = 0;
    virtual bool isValid() const = 0;
    
    static std::unique_ptr<Calibration> createFromConfig(const JsonObject& config);
};

class LinearCalibration : public Calibration {
private:
    float slope;
    float offset;
    bool valid;
    
public:
    LinearCalibration();
    
    float calibrate(float raw_value) const override;
    bool loadFromJson(const JsonObject& calibration_data) override;
    JsonObject toJson() const override;
    bool isValid() const override { return valid; }
    
    // Für 2-Punkt-Kalibrierung
    bool setTwoPoints(float raw1, float value1, float raw2, float value2);
};

class MultiPointCalibration : public Calibration {
private:
    struct CalibrationPoint {
        float raw;
        float value;
    };
    
    std::vector<CalibrationPoint> points;
    bool valid;
    
public:
    MultiPointCalibration();
    
    float calibrate(float raw_value) const override;
    bool loadFromJson(const JsonObject& calibration_data) override;
    JsonObject toJson() const override;
    bool isValid() const override { return valid; }
    
private:
    float interpolate(float raw_value) const;
};

#endif
```

### 4.3 Rauschfilter
#### src/sensors/filters/NoiseFilter.h
```cpp
#ifndef NOISE_FILTER_H
#define NOISE_FILTER_H

#include <ArduinoJson.h>
#include <vector>

class NoiseFilter {
public:
    virtual ~NoiseFilter() = default;
    virtual float filter(float value) = 0;
    virtual void reset() = 0;
    virtual bool loadFromJson(const JsonObject& filter_config) = 0;
    virtual JsonObject toJson() const = 0;
    
    static std::unique_ptr<NoiseFilter> createFromConfig(const JsonObject& config);
};

class MovingAverageFilter : public NoiseFilter {
private:
    std::vector<float> buffer;
    size_t window_size;
    size_t current_index;
    bool buffer_full;
    float outlier_threshold;
    
public:
    MovingAverageFilter(size_t window_size = 10, float outlier_threshold = 2.0);
    
    float filter(float value) override;
    void reset() override;
    bool loadFromJson(const JsonObject& filter_config) override;
    JsonObject toJson() const override;
    
private:
    bool isOutlier(float value) const;
    float calculateAverage() const;
    float calculateStandardDeviation() const;
};

class ExponentialFilter : public NoiseFilter {
private:
    float alpha;
    float filtered_value;
    bool initialized;
    float outlier_threshold;
    
public:
    ExponentialFilter(float alpha = 0.1, float outlier_threshold = 2.0);
    
    float filter(float value) override;
    void reset() override;
    bool loadFromJson(const JsonObject& filter_config) override;
    JsonObject toJson() const override;
    
private:
    bool isOutlier(float value) const;
};

#endif
```

### 4.4 Sensor-Manager
#### src/sensors/SensorManager.h
```cpp
#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include "BaseSensor.h"
#include "PHSensor.h"
#include "TDSSensor.h"
#include "core/Timer.h"
#include "network/MQTTClient.h"

class SensorManager {
private:
    std::vector<std::unique_ptr<BaseSensor>> sensors;
    Timer publish_timer;
    MQTTClient* mqtt_client;
    
    // Publishing-Konfiguration
    float ph_publish_rate_hz;
    float tds_publish_rate_hz;
    unsigned long last_ph_publish;
    unsigned long last_tds_publish;
    
public:
    SensorManager();
    
    bool init(const Config& config, MQTTClient* mqtt);
    void loop();
    
    // Sensor-Management
    bool addSensor(std::unique_ptr<BaseSensor> sensor);
    BaseSensor* getSensor(SensorType type);
    
    // Datenerfassung
    bool readAllSensors();
    bool publishSensorData();
    
    // Kalibrierung
    bool calibrateSensor(SensorType type, const JsonArray& calibration_points);
    
    // Status für Heartbeat
    JsonObject getStatusJson() const;
    bool areAllSensorsHealthy() const;
    
private:
    bool shouldPublishSensor(SensorType type) const;
    void updatePublishTimestamps(SensorType type);
};

#endif
```

### 4.5 Validierung Phase 4
- [ ] Sensoren lesen simulierte Werte (über Serial)
- [ ] Kalibrierung funktioniert mit Multi-Point und Linear-Kalibrierung
- [ ] Filter reduzieren Rauschen korrekt
- [ ] Publishing-Rate konfigurierbar
- [ ] Memory-Usage unter 40% (ca. 200KB)

## Phase 5: Aktor-Framework (Tag 4-5)

### 5.1 Basis-Aktor-Klassen
**Priorität: HOCH** - Pumpensteuerung ist zentral

#### src/actuators/BaseActuator.h
```cpp
#ifndef BASE_ACTUATOR_H
#define BASE_ACTUATOR_H

#include "core/Types.h"
#include "config/Config.h"
#include "core/Logger.h"

enum class ActuatorState {
    IDLE,
    ACTIVE,
    COOLDOWN,
    ERROR,
    DISABLED
};

class BaseActuator {
protected:
    String actuator_id;
    ActuatorType type;
    ActuatorConfig config;
    ActuatorState state;
    
    unsigned long activation_start_time;
    unsigned long last_activation_end;
    unsigned long total_runtime_ms;
    unsigned long activation_count;
    
    bool initialized;
    String last_error;
    
public:
    BaseActuator(const String& id, ActuatorType actuator_type);
    virtual ~BaseActuator() = default;
    
    virtual bool init(const ActuatorConfig& actuator_config) = 0;
    virtual bool activate(unsigned long duration_ms) = 0;
    virtual bool deactivate() = 0;
    virtual void loop() = 0;
    
    // Status-Abfragen
    bool isActive() const { return state == ActuatorState::ACTIVE; }
    bool canActivate() const;
    ActuatorState getState() const { return state; }
    String getId() const { return actuator_id; }
    ActuatorType getType() const { return type; }
    
    // Sicherheitsprüfungen
    bool isInCooldown() const;
    unsigned long getRemainingCooldown() const;
    bool hasExceededMaxRuntime() const;
    
    // Statistiken
    unsigned long getTotalRuntimeMs() const { return total_runtime_ms; }
    unsigned long getActivationCount() const { return activation_count; }
    float getRuntimeHours() const { return total_runtime_ms / 3600000.0; }
    
    // Status für Monitoring
    virtual JsonObject getStatusJson() const;
    virtual bool isHealthy() const;
    
protected:
    virtual bool hardwareActivate() = 0;
    virtual bool hardwareDeactivate() = 0;
    
    void setState(ActuatorState new_state);
    void logActivation(unsigned long duration_ms);
    void logDeactivation();
    bool validateActivationRequest(unsigned long duration_ms) const;
};

#endif
```

#### src/actuators/Pump.h
```cpp
#ifndef PUMP_H
#define PUMP_H

#include "BaseActuator.h"

class Pump : public BaseActuator {
protected:
    int pin;
    float flow_rate_ml_per_sec;
    unsigned long planned_duration_ms;
    
public:
    Pump(const String& id, ActuatorType pump_type);
    
    bool init(const ActuatorConfig& actuator_config) override;
    bool activate(unsigned long duration_ms) override;
    bool deactivate() override;
    void loop() override;
    
    // Pumpen-spezifische Methoden
    virtual bool dose(float volume_ml);
    float calculateDurationForVolume(float volume_ml) const;
    float calculateVolumeForDuration(unsigned long duration_ms) const;
    
    // Getters
    float getFlowRate() const { return flow_rate_ml_per_sec; }
    
protected:
    bool hardwareActivate() override;
    bool hardwareDeactivate() override;
    
private:
    void checkAutoDeactivation();
};

#endif
```

#### src/actuators/DosingPump.h
```cpp
#ifndef DOSING_PUMP_H
#define DOSING_PUMP_H

#include "Pump.h"

class DosingPump : public Pump {
private:
    String substance;
    String concentration;
    float max_dose_ml;
    unsigned long last_dose_time;
    float total_volume_dispensed_ml;
    
public:
    DosingPump(const String& id);
    
    bool init(const ActuatorConfig& actuator_config) override;
    
    // Dosier-spezifische Methoden
    bool dose(float volume_ml) override;
    bool canDose(float volume_ml) const;
    
    // Substanz-Information
    String getSubstance() const { return substance; }
    String getConcentration() const { return concentration; }
    float getTotalVolumeDispensed() const { return total_volume_dispensed_ml; }
    
    // Status für Monitoring
    JsonObject getStatusJson() const override;
    
private:
    bool validateDoseRequest(float volume_ml) const;
    void logDose(float volume_ml);
};

#endif
```

### 5.2 Spezifische Pumpen-Implementierungen
#### src/actuators/WaterPump.h
```cpp
#ifndef WATER_PUMP_H
#define WATER_PUMP_H

#include "Pump.h"

class WaterPump : public Pump {
private:
    bool scheduled_enabled;
    unsigned long schedule_interval_ms;
    unsigned long schedule_duration_ms;
    unsigned long last_scheduled_activation;
    
public:
    WaterPump();
    
    bool init(const ActuatorConfig& actuator_config) override;
    void loop() override;
    
    // Scheduling
    bool setSchedule(unsigned long interval_minutes, unsigned long duration_seconds);
    bool cancelSchedule();
    bool isScheduleEnabled() const { return scheduled_enabled; }
    
    // Status für Monitoring
    JsonObject getStatusJson() const override;
    
private:
    void checkScheduledActivation();
    bool shouldActivateScheduled() const;
};

#endif
```

#### src/actuators/AirPump.h
```cpp
#ifndef AIR_PUMP_H
#define AIR_PUMP_H

#include "Pump.h"

class AirPump : public Pump {
private:
    bool scheduled_enabled;
    unsigned long schedule_interval_ms;
    unsigned long schedule_duration_ms;
    unsigned long last_scheduled_activation;
    
public:
    AirPump();
    
    bool init(const ActuatorConfig& actuator_config) override;
    void loop() override;
    
    // Scheduling
    bool setSchedule(unsigned long interval_minutes, unsigned long duration_seconds);
    bool cancelSchedule();
    bool isScheduleEnabled() const { return scheduled_enabled; }
    
    // Status für Monitoring
    JsonObject getStatusJson() const override;
    
private:
    void checkScheduledActivation();
    bool shouldActivateScheduled() const;
};

#endif
```

### 5.3 Aktor-Manager
#### src/actuators/ActuatorManager.h
```cpp
#ifndef ACTUATOR_MANAGER_H
#define ACTUATOR_MANAGER_H

#include "BaseActuator.h"
#include "WaterPump.h"
#include "AirPump.h"
#include "DosingPump.h"
#include "core/Types.h"
#include "config/Config.h"

class ActuatorManager {
private:
    std::map<String, std::unique_ptr<BaseActuator>> actuators;
    bool emergency_stop_active;
    String emergency_stop_reason;
    
public:
    ActuatorManager();
    
    bool init(const Config& config);
    void loop();
    
    // Aktor-Management
    bool addActuator(std::unique_ptr<BaseActuator> actuator);
    BaseActuator* getActuator(const String& actuator_id);
    DosingPump* getDosingPump(const String& pump_id);
    
    // Basis-Operationen
    bool activateActuator(const String& actuator_id, unsigned long duration_ms);
    bool deactivateActuator(const String& actuator_id);
    bool stopAllActuators();
    
    // Dosier-Operationen
    bool dose(const String& pump_id, float volume_ml);
    bool canDose(const String& pump_id, float volume_ml) const;
    
    // Scheduling
    bool setSchedule(const String& actuator_id, unsigned long interval_minutes, unsigned long duration_seconds);
    bool cancelSchedule(const String& actuator_id);
    
    // Emergency Stop
    void emergencyStop(const String& reason);
    void clearEmergencyStop();
    bool isEmergencyStopActive() const { return emergency_stop_active; }
    String getEmergencyStopReason() const { return emergency_stop_reason; }
    
    // Status für Monitoring
    JsonObject getStatusJson() const;
    bool areAllActuatorsHealthy() const;
    
private:
    void initializeActuators(const Config& config);
    bool validateActuatorOperation(const String& actuator_id) const;
};

#endif
```

### 5.4 Validierung Phase 5
- [ ] Alle Pumpen-Typen implementiert
- [ ] Dosierung korrekt berechnet
- [ ] Safety-Checks funktionieren
- [ ] Scheduling-System arbeitet
- [ ] Emergency-Stop stoppt alle Pumpen
- [ ] Memory-Usage unter 50% (ca. 250KB)

## Phase 6: Command-System (Tag 5-6)

### 6.1 Command-Framework
**Priorität: KRITISCH** - Zentrale Steuerungsschnittstelle

#### src/commands/BaseCommand.h
```cpp
#ifndef BASE_COMMAND_H
#define BASE_COMMAND_H

#include "core/Types.h"
#include "core/Logger.h"
#include <ArduinoJson.h>

class BaseCommand {
protected:
    String command_id;
    String command_type;
    JsonObject params;
    CommandStatus status;
    String error_message;
    JsonDocument result_data;
    unsigned long start_time;
    unsigned long execution_time_ms;
    
public:
    BaseCommand(const String& cmd_id, const String& cmd_type);
    virtual ~BaseCommand() = default;
    
    virtual bool validate(const JsonObject& parameters) = 0;
    virtual bool execute() = 0;
    virtual void abort() = 0;
    
    // Getters
    String getCommandId() const { return command_id; }
    String getCommandType() const { return command_type; }
    CommandStatus getStatus() const { return status; }
    String getErrorMessage() const { return error_message; }
    
    // Result
    CommandResult getResult() const;
    JsonObject getResultData() const;
    
protected:
    void setStatus(CommandStatus new_status);
    void setError(const String& error);
    void setResultData(const JsonObject& data);
    void logCommandStart();
    void logCommandEnd();
    
    // Hilfsmethoden für Parameter-Validierung
    bool hasParam(const String& key) const;
    bool getStringParam(const String& key, String& value) const;
    bool getFloatParam(const String& key, float& value) const;
    bool getIntParam(const String& key, int& value) const;
    bool getBoolParam(const String& key, bool& value) const;
};

#endif
```

#### src/commands/PumpCommand.h
```cpp
#ifndef PUMP_COMMAND_H
#define PUMP_COMMAND_H

#include "BaseCommand.h"
#include "actuators/ActuatorManager.h"

class ActivatePumpCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String pump_id;
    unsigned long duration_sec;
    
public:
    ActivatePumpCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class StopPumpCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String pump_id;
    
public:
    StopPumpCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class StopAllPumpsCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    
public:
    StopAllPumpsCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

#endif
```

#### src/commands/DosingCommand.h
```cpp
#ifndef DOSING_COMMAND_H
#define DOSING_COMMAND_H

#include "BaseCommand.h"
#include "actuators/ActuatorManager.h"
#include "sensors/SensorManager.h"

class DoseVolumeCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String pump_id;
    float volume_ml;
    
public:
    DoseVolumeCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class AdjustPHByCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    SensorManager* sensor_manager;
    float delta_ph;
    float max_volume_ml;
    
public:
    AdjustPHByCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
    
private:
    float calculateRequiredVolume(float current_ph, float delta_ph) const;
    String selectPHPump(float delta_ph) const;
};

class SetPHTargetCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    SensorManager* sensor_manager;
    float target_ph;
    float tolerance;
    int max_attempts;
    
public:
    SetPHTargetCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
    
private:
    bool adjustPHToTarget();
    float getCurrentPH() const;
};

class AdjustTDSByCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    SensorManager* sensor_manager;
    float delta_tds;
    float max_volume_ml;
    
public:
    AdjustTDSByCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
    
private:
    float calculateRequiredVolume(float current_tds, float delta_tds) const;
    std::vector<String> selectNutrientPumps() const;
};

#endif
```

#### src/commands/ScheduleCommand.h
```cpp
#ifndef SCHEDULE_COMMAND_H
#define SCHEDULE_COMMAND_H

#include "BaseCommand.h"
#include "actuators/ActuatorManager.h"

class SchedulePumpCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String pump_id;
    unsigned long interval_minutes;
    unsigned long duration_seconds;
    
public:
    SchedulePumpCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class CancelScheduleCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String pump_id;
    
public:
    CancelScheduleCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

#endif
```

#### src/commands/SystemCommand.h
```cpp
#ifndef SYSTEM_COMMAND_H
#define SYSTEM_COMMAND_H

#include "BaseCommand.h"
#include "actuators/ActuatorManager.h"
#include "sensors/SensorManager.h"
#include "config/ConfigManager.h"

class EmergencyStopCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String reason;
    
public:
    EmergencyStopCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class ResetSystemCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    
public:
    ResetSystemCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class CalibrateSensorCommand : public BaseCommand {
private:
    SensorManager* sensor_manager;
    SensorType sensor_type;
    JsonArray calibration_points;
    
public:
    CalibrateSensorCommand(const String& cmd_id, SensorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
    
private:
    SensorType parseSensorType(const String& sensor_id) const;
};

class UpdateConfigCommand : public BaseCommand {
private:
    ConfigManager* config_manager;
    String config_section;
    JsonObject config_data;
    
public:
    UpdateConfigCommand(const String& cmd_id, ConfigManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

#endif
```

### 6.2 Command-Processor
#### src/commands/CommandProcessor.h
```cpp
#ifndef COMMAND_PROCESSOR_H
#define COMMAND_PROCESSOR_H

#include "BaseCommand.h"
#include "PumpCommand.h"
#include "DosingCommand.h"
#include "ScheduleCommand.h"
#include "SystemCommand.h"
#include "network/MQTTClient.h"
#include <map>
#include <queue>

class CommandProcessor {
private:
    std::map<String, std::unique_ptr<BaseCommand>> active_commands;
    std::queue<JsonDocument> command_queue;
    
    // Manager-Referenzen
    ActuatorManager* actuator_manager;
    SensorManager* sensor_manager;
    ConfigManager* config_manager;
    MQTTClient* mqtt_client;
    
    // Command-Statistiken
    unsigned long commands_processed;
    unsigned long commands_failed;
    unsigned long commands_timeout;
    
    static const unsigned long COMMAND_TIMEOUT_MS = 60000; // 1 Minute
    static const size_t MAX_QUEUE_SIZE = 10;
    
public:
    CommandProcessor();
    
    bool init(ActuatorManager* actuator_mgr, SensorManager* sensor_mgr, 
              ConfigManager* config_mgr, MQTTClient* mqtt);
    
    void loop();
    
    // Command-Verarbeitung
    bool processCommand(const String& command_json);
    bool queueCommand(const JsonDocument& command);
    void processCommandQueue();
    
    // Command-Management
    void abortCommand(const String& command_id);
    void abortAllCommands();
    void checkCommandTimeouts();
    
    // Status für Monitoring
    JsonObject getStatusJson() const;
    
private:
    std::unique_ptr<BaseCommand> createCommand(const String& command_type, const String& command_id);
    bool validateCommandJson(const JsonDocument& command_doc) const;
    void publishCommandResponse(const CommandResult& result);
    void cleanupCompletedCommands();
};

#endif
```

### 6.3 Validierung Phase 6
- [ ] Alle Command-Typen implementiert
- [ ] Command-Queue arbeitet korrekt
- [ ] Timeout-Handling funktioniert
- [ ] Command-Responses werden publiziert
- [ ] Advanced Commands (pH/TDS-Anpassung) funktionieren
- [ ] Memory-Usage unter 60% (ca. 300KB)

## Phase 7: State Machine & Integration (Tag 6-7)

### 7.1 State Machine implementieren
**Priorität: KRITISCH** - Orchestriert das gesamte System

#### src/state/StateMachine.h
```cpp
#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#include "BaseState.h"
#include "core/Types.h"
#include "core/Logger.h"

class Application; // Forward-Deklaration

class StateMachine {
private:
    std::unique_ptr<BaseState> current_state;
    SystemState current_state_type;
    Application* app;
    unsigned long state_start_time;
    unsigned long total_state_transitions;
    
public:
    StateMachine(Application* application);
    
    void init();
    void update();
    void transition(SystemState new_state);
    
    SystemState getCurrentStateType() const { return current_state_type; }
    BaseState* getCurrentState() const { return current_state.get(); }
    unsigned long getStateUptime() const;
    
    // Event-Handling
    void handleEvent(const String& event, const JsonObject& data = JsonObject());
    
    // Status für Monitoring
    JsonObject getStatusJson() const;
    
private:
    std::unique_ptr<BaseState> createState(SystemState state_type);
    void logStateTransition(SystemState from, SystemState to);
};

#endif
```

#### src/state/BaseState.h
```cpp
#ifndef BASE_STATE_H
#define BASE_STATE_H

#include "core/Types.h"
#include "core/Logger.h"
#include <ArduinoJson.h>

class Application; // Forward-Deklaration

class BaseState {
protected:
    Application* app;
    SystemState state_type;
    unsigned long enter_time;
    
public:
    BaseState(Application* application, SystemState type);
    virtual ~BaseState() = default;
    
    virtual void enter() = 0;
    virtual void exit() = 0;
    virtual void update() = 0;
    virtual void handleEvent(const String& event, const JsonObject& data) = 0;
    
    SystemState getType() const { return state_type; }
    unsigned long getUptime() const;
    
    // Status für Monitoring
    virtual JsonObject getStatusJson() const;
    
protected:
    void logStateEvent(const String& event, const String& message = "");
    bool shouldTimeout(unsigned long timeout_ms) const;
};

#endif
```

### 7.2 Spezifische States implementieren
#### src/state/InitState.h
```cpp
#ifndef INIT_STATE_H
#define INIT_STATE_H

#include "BaseState.h"

class InitState : public BaseState {
private:
    bool config_loaded;
    bool logger_initialized;
    bool components_initialized;
    
    static const unsigned long INIT_TIMEOUT_MS = 10000; // 10 Sekunden
    
public:
    InitState(Application* app);
    
    void enter() override;
    void exit() override;
    void update() override;
    void handleEvent(const String& event, const JsonObject& data) override;
    
private:
    bool initializeComponents();
    bool loadConfiguration();
    bool initializeLogger();
    bool initializeManagers();
};

#endif
```

#### src/state/ConnectingWiFiState.h
```cpp
#ifndef CONNECTING_WIFI_STATE_H
#define CONNECTING_WIFI_STATE_H

#include "BaseState.h"

class ConnectingWiFiState : public BaseState {
private:
    int connection_attempts;
    unsigned long last_attempt_time;
    
    static const int MAX_ATTEMPTS = 5;
    static const unsigned long ATTEMPT_INTERVAL_MS = 5000; // 5 Sekunden
    static const unsigned long CONNECTION_TIMEOUT_MS = 30000; // 30 Sekunden
    
public:
    ConnectingWiFiState(Application* app);
    
    void enter() override;
    void exit() override;
    void update() override;
    void handleEvent(const String& event, const JsonObject& data) override;
    
private:
    bool attemptConnection();
    bool shouldRetry() const;
    void handleConnectionFailure();
};

#endif
```

#### src/state/DiscoveringBrokerState.h
```cpp
#ifndef DISCOVERING_BROKER_STATE_H
#define DISCOVERING_BROKER_STATE_H

#include "BaseState.h"

class DiscoveringBrokerState : public BaseState {
private:
    bool discovery_started;
    unsigned long discovery_start_time;
    
    static const unsigned long DISCOVERY_TIMEOUT_MS = 10000; // 10 Sekunden
    
public:
    DiscoveringBrokerState(Application* app);
    
    void enter() override;
    void exit() override;
    void update() override;
    void handleEvent(const String& event, const JsonObject& data) override;
    
private:
    bool startDiscovery();
    void handleDiscoveryComplete();
    void handleDiscoveryTimeout();
};

#endif
```

#### src/state/ConnectingMQTTState.h
```cpp
#ifndef CONNECTING_MQTT_STATE_H
#define CONNECTING_MQTT_STATE_H

#include "BaseState.h"

class ConnectingMQTTState : public BaseState {
private:
    int connection_attempts;
    unsigned long last_attempt_time;
    
    static const int MAX_ATTEMPTS = 3;
    static const unsigned long ATTEMPT_INTERVAL_MS = 5000; // 5 Sekunden
    static const unsigned long CONNECTION_TIMEOUT_MS = 20000; // 20 Sekunden
    
public:
    ConnectingMQTTState(Application* app);
    
    void enter() override;
    void exit() override;
    void update() override;
    void handleEvent(const String& event, const JsonObject& data) override;
    
private:
    bool attemptConnection();
    bool shouldRetry() const;
    void handleConnectionFailure();
};

#endif
```

#### src/state/ConfigRequestState.h
```cpp
#ifndef CONFIG_REQUEST_STATE_H
#define CONFIG_REQUEST_STATE_H

#include "BaseState.h"

class ConfigRequestState : public BaseState {
private:
    bool config_requested;
    unsigned long request_time;
    int request_attempts;
    
    static const int MAX_ATTEMPTS = 3;
    static const unsigned long REQUEST_TIMEOUT_MS = 15000; // 15 Sekunden
    static const unsigned long RETRY_INTERVAL_MS = 5000; // 5 Sekunden
    
public:
    ConfigRequestState(Application* app);
    
    void enter() override;
    void exit() override;
    void update() override;
    void handleEvent(const String& event, const JsonObject& data) override;
    
private:
    bool requestConfig();
    bool shouldRetry() const;
    void handleConfigReceived(const JsonObject& config_data);
    void handleRequestTimeout();
};

#endif
```

#### src/state/RunningState.h
```cpp
#ifndef RUNNING_STATE_H
#define RUNNING_STATE_H

#include "BaseState.h"

class RunningState : public BaseState {
private:
    unsigned long last_heartbeat;
    unsigned long last_sensor_check;
    unsigned long last_safety_check;
    
    static const unsigned long HEARTBEAT_INTERVAL_MS = 30000; // 30 Sekunden
    static const unsigned long SENSOR_CHECK_INTERVAL_MS = 1000; // 1 Sekunde
    static const unsigned long SAFETY_CHECK_INTERVAL_MS = 5000; // 5 Sekunden
    
public:
    RunningState(Application* app);
    
    void enter() override;
    void exit() override;
    void update() override;
    void handleEvent(const String& event, const JsonObject& data) override;
    
private:
    void performHeartbeat();
    void performSensorCheck();
    void performSafetyCheck();
    void handleMQTTMessage(const String& topic, const String& payload);
    void handleConnectionLoss();
    bool checkEmergencyConditions();
};

#endif
```

#### src/state/ErrorState.h
```cpp
#ifndef ERROR_STATE_H
#define ERROR_STATE_H

#include "BaseState.h"

class ErrorState : public BaseState {
private:
    String error_reason;
    unsigned long error_start_time;
    int recovery_attempts;
    
    static const int MAX_RECOVERY_ATTEMPTS = 3;
    static const unsigned long RECOVERY_INTERVAL_MS = 10000; // 10 Sekunden
    static const unsigned long MAX_ERROR_TIME_MS = 300000; // 5 Minuten
    
public:
    ErrorState(Application* app);
    
    void enter() override;
    void exit() override;
    void update() override;
    void handleEvent(const String& event, const JsonObject& data) override;
    
    void setErrorReason(const String& reason) { error_reason = reason; }
    String getErrorReason() const { return error_reason; }
    
private:
    bool attemptRecovery();
    bool shouldRestart() const;
    void performRestart();
};

#endif
```

### 7.3 Haupt-Application-Klasse
#### src/core/Application.h
```cpp
#ifndef APPLICATION_H
#define APPLICATION_H

#include "config/ConfigManager.h"
#include "state/StateMachine.h"
#include "sensors/SensorManager.h"
#include "actuators/ActuatorManager.h"
#include "commands/CommandProcessor.h"
#include "network/WiFiManager.h"
#include "network/MQTTClient.h"
#include "network/MDNSDiscovery.h"
#include "network/OTAManager.h"
#include "core/Logger.h"

class Application {
private:
    // Core-Komponenten
    ConfigManager config_manager;
    StateMachine state_machine;
    Logger logger;
    
    // Manager
    SensorManager sensor_manager;
    ActuatorManager actuator_manager;
    CommandProcessor command_processor;
    
    // Netzwerk
    WiFiManager wifi_manager;
    MQTTClient mqtt_client;
    MDNSDiscovery mdns_discovery;
    OTAManager ota_manager;
    
    // System-Status
    unsigned long start_time;
    unsigned long loop_count;
    unsigned long last_memory_check;
    
public:
    Application();
    
    void setup();
    void loop();
    
    // Getter für Manager (für States)
    ConfigManager& getConfigManager() { return config_manager; }
    SensorManager& getSensorManager() { return sensor_manager; }
    ActuatorManager& getActuatorManager() { return actuator_manager; }
    CommandProcessor& getCommandProcessor() { return command_processor; }
    WiFiManager& getWiFiManager() { return wifi_manager; }
    MQTTClient& getMQTTClient() { return mqtt_client; }
    MDNSDiscovery& getMDNSDiscovery() { return mdns_discovery; }
    OTAManager& getOTAManager() { return ota_manager; }
    
    // System-Informationen
    unsigned long getUptime() const;
    JsonObject getSystemStatus() const;
    JsonObject getHeartbeatData() const;
    
    // Event-Handling
    void handleMQTTMessage(const String& topic, const String& payload);
    void handleWiFiEvent(const String& event);
    void handleError(const String& error_message);
    
private:
    bool initializeComponents();
    void performMemoryCheck();
    void performWatchdogReset();
    JsonObject getMemoryInfo() const;
};

#endif
```

### 7.4 Minimale main.cpp
#### src/main.cpp
```cpp
#include "core/Application.h"

Application app;

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("HomeGrow Client v3 starting...");
    app.setup();
}

void loop() {
    app.loop();
}
```

### 7.5 Validierung Phase 7
- [ ] State Machine durchläuft alle States korrekt
- [ ] Application orchestriert alle Manager
- [ ] MQTT-Messages werden korrekt verarbeitet
- [ ] Error-Handling funktioniert
- [ ] System startet und läuft stabil
- [ ] Memory-Usage unter 70% (ca. 350KB)

## Phase 8: Safety & Monitoring (Tag 7)

### 8.1 Safety-System implementieren
#### src/safety/SafetyManager.h
```cpp
#ifndef SAFETY_MANAGER_H
#define SAFETY_MANAGER_H

#include "core/Types.h"
#include "config/Config.h"
#include "sensors/SensorManager.h"
#include "actuators/ActuatorManager.h"

enum class SafetyLevel {
    NORMAL,
    WARNING,
    CRITICAL,
    EMERGENCY
};

struct SafetyCondition {
    String condition_id;
    SafetyLevel level;
    String description;
    bool active;
    unsigned long first_detected;
    unsigned long last_checked;
};

class SafetyManager {
private:
    SafetyConfig config;
    SensorManager* sensor_manager;
    ActuatorManager* actuator_manager;
    
    std::vector<SafetyCondition> active_conditions;
    bool emergency_stop_active;
    String emergency_reason;
    unsigned long last_safety_check;
    
    static const unsigned long SAFETY_CHECK_INTERVAL_MS = 5000; // 5 Sekunden
    
public:
    SafetyManager();
    
    bool init(const SafetyConfig& safety_config, SensorManager* sensor_mgr, ActuatorManager* actuator_mgr);
    void loop();
    
    // Safety-Checks
    bool performSafetyCheck();
    bool checkSensorValues();
    bool checkActuatorStates();
    bool checkSystemHealth();
    
    // Emergency-Handling
    void triggerEmergencyStop(const String& reason);
    void clearEmergencyStop();
    bool isEmergencyStopActive() const { return emergency_stop_active; }
    String getEmergencyReason() const { return emergency_reason; }
    
    // Condition-Management
    void addCondition(const SafetyCondition& condition);
    void removeCondition(const String& condition_id);
    void clearConditions(SafetyLevel level);
    
    // Status für Monitoring
    JsonObject getStatusJson() const;
    std::vector<SafetyCondition> getActiveConditions() const { return active_conditions; }
    
private:
    bool checkPHLimits();
    bool checkTDSLimits();
    bool checkPumpRuntimes();
    bool checkMemoryUsage();
    bool checkConnectivity();
    
    void logSafetyEvent(const String& event, SafetyLevel level, const String& details = "");
};

#endif
```

### 8.2 Heartbeat-System erweitern
#### src/monitoring/HeartbeatManager.h
```cpp
#ifndef HEARTBEAT_MANAGER_H
#define HEARTBEAT_MANAGER_H

#include "core/Types.h"
#include "network/MQTTClient.h"
#include "sensors/SensorManager.h"
#include "actuators/ActuatorManager.h"
#include "safety/SafetyManager.h"

class HeartbeatManager {
private:
    MQTTClient* mqtt_client;
    SensorManager* sensor_manager;
    ActuatorManager* actuator_manager;
    SafetyManager* safety_manager;
    
    unsigned long last_heartbeat;
    unsigned long heartbeat_interval_ms;
    unsigned long heartbeat_count;
    
public:
    HeartbeatManager();
    
    bool init(MQTTClient* mqtt, SensorManager* sensors, ActuatorManager* actuators, SafetyManager* safety);
    void loop();
    
    void setInterval(unsigned long interval_ms) { heartbeat_interval_ms = interval_ms; }
    bool shouldSendHeartbeat() const;
    
private:
    JsonObject createHeartbeatData() const;
    JsonObject getSystemInfo() const;
    JsonObject getMemoryInfo() const;
    JsonObject getNetworkInfo() const;
    JsonObject getSensorStatus() const;
    JsonObject getActuatorStatus() const;
    JsonObject getSafetyStatus() const;
};

#endif
```

### 8.3 Validierung Phase 8
- [ ] Safety-Checks erkennen kritische Werte
- [ ] Emergency-Stop funktioniert sofort
- [ ] Heartbeat enthält alle relevanten Daten
- [ ] Memory-Monitoring funktioniert
- [ ] System bleibt unter 75% Memory-Usage (ca. 375KB)

## Phase 9: Testing & Validation (Tag 8)

### 9.1 Umfassende Code-Validierung
```bash
# Kompilierung testen
pio run

# Memory-Usage analysieren
pio run --target size

# Static Analysis (falls verfügbar)
pio check
```

### 9.2 JSON-Schema-Validierung
#### test/schemas/sensor_data_schema.json
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["timestamp", "device_timestamp", "sensor_id", "values", "unit"],
  "properties": {
    "timestamp": {"type": "string", "format": "date-time"},
    "device_timestamp": {"type": "integer"},
    "sensor_id": {"type": "string", "enum": ["ph", "tds"]},
    "values": {
      "type": "object",
      "required": ["raw", "calibrated", "filtered"],
      "properties": {
        "raw": {"type": "number"},
        "calibrated": {"type": "number"},
        "filtered": {"type": "number"}
      }
    },
    "unit": {"type": "string"},
    "quality": {"type": "string", "enum": ["good", "warning", "error"]},
    "calibration_status": {"type": "string", "enum": ["valid", "invalid", "expired"]}
  }
}
```

#### test/schemas/command_schema.json
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["command_id", "command", "params"],
  "properties": {
    "command_id": {"type": "string"},
    "command": {"type": "string", "enum": [
      "activate_pump", "dose", "adjust_ph_by", "set_ph_target",
      "adjust_tds_by", "set_tds_target", "schedule_pump", "cancel_schedule",
      "emergency_stop", "reset_system", "calibrate_sensor", "update_config"
    ]},
    "params": {"type": "object"},
    "priority": {"type": "string", "enum": ["low", "normal", "high", "critical"]},
    "timeout_sec": {"type": "integer", "minimum": 1, "maximum": 300},
    "retry_count": {"type": "integer", "minimum": 0, "maximum": 5}
  }
}
```

### 9.3 Simulation-Tests
#### test/simulation/sensor_simulation.cpp
```cpp
// Simuliert Sensordaten für verschiedene Szenarien
void testSensorReadings() {
    // pH-Werte: Normal, Grenzwerte, Kritisch
    testPHSensor(7.0);  // Normal
    testPHSensor(6.0);  // Grenzwert
    testPHSensor(3.5);  // Kritisch -> Emergency Stop
    
    // TDS-Werte: Normal, Grenzwerte, Kritisch
    testTDSSensor(600);   // Normal
    testTDSSensor(800);   // Grenzwert
    testTDSSensor(2500);  // Kritisch -> Emergency Stop
}
```

#### test/simulation/command_simulation.cpp
```cpp
// Simuliert Command-Verarbeitung
void testCommandProcessing() {
    // Basis-Commands
    testActivatePump("water_pump", 30);
    testDoseVolume("ph_down", 5.0);
    
    // Advanced Commands
    testAdjustPHBy(0.5);
    testSetPHTarget(6.5);
    
    // Error-Cases
    testInvalidCommand();
    testCommandTimeout();
}
```

### 9.4 Memory-Profiling
#### test/memory/memory_test.cpp
```cpp
void testMemoryUsage() {
    Serial.println("=== Memory Usage Test ===");
    
    // Basis-Memory
    size_t free_heap_start = ESP.getFreeHeap();
    Serial.printf("Free Heap at Start: %d bytes\n", free_heap_start);
    
    // Nach Initialisierung
    app.setup();
    size_t free_heap_after_init = ESP.getFreeHeap();
    Serial.printf("Free Heap after Init: %d bytes\n", free_heap_after_init);
    Serial.printf("Memory used by Init: %d bytes\n", free_heap_start - free_heap_after_init);
    
    // Nach 1000 Loops
    for(int i = 0; i < 1000; i++) {
        app.loop();
        delay(1);
    }
    size_t free_heap_after_loops = ESP.getFreeHeap();
    Serial.printf("Free Heap after 1000 loops: %d bytes\n", free_heap_after_loops);
    
    // Memory-Leak-Check
    if(free_heap_after_loops < free_heap_after_init - 1000) {
        Serial.println("WARNING: Possible memory leak detected!");
    }
}
```

### 9.5 Validierung Phase 9
- [ ] Alle Module kompilieren ohne Fehler
- [ ] JSON-Schemas validieren korrekt
- [ ] Simulation-Tests laufen durch
- [ ] Memory-Usage stabil unter 80% (ca. 400KB)
- [ ] Keine Memory-Leaks erkannt

## Phase 10: Migration & Deployment (Sonntag)

### 10.1 Migrations-Vorbereitung
#### migration/migration_checklist.md
```markdown
# Migration Checklist HomeGrow Client v3

## Pre-Migration (Samstag Abend)
- [ ] v2 System Backup erstellen
- [ ] v2 Konfiguration exportieren
- [ ] v3 Code final kompiliert und getestet
- [ ] Hardware-Pins dokumentiert
- [ ] MQTT-Broker bereit für v3 Topics

## Migration (Sonntag)
- [ ] v2 System stoppen
- [ ] Hardware-Verbindungen prüfen
- [ ] v3 Firmware flashen
- [ ] Erste Verbindung testen
- [ ] v2-Konfiguration zu v3 migrieren
- [ ] Sensor-Kalibrierung übertragen und prüfen
- [ ] Pumpen-Tests durchführen
- [ ] MQTT-Kommunikation validieren (neue v3 Topics)

## Post-Migration
- [ ] 24h Monitoring
- [ ] Performance-Metriken sammeln
- [ ] Error-Logs analysieren
- [ ] Backup-Plan aktivieren falls nötig
```

### 10.2 Migrations-Script
#### migration/migrate_config.py
```python
#!/usr/bin/env python3
"""
Konvertiert v2 Konfiguration zu v3 Format
"""

import json
import sys

def migrate_v2_to_v3(v2_config):
    """Konvertiert v2 Config zu v3 Format"""
    v3_config = {
        "device": {
            "id": "homegrow_client_001",
            "name": "HomeGrow Client v3",
            "firmware_version": "3.0.0"
        },
        "sensors": {},
        "actuators": {},
        "safety": {
            "emergency_stop_conditions": {
                "ph_min": 4.0,
                "ph_max": 8.5,
                "tds_max": 2000
            }
        }
    }
    
    # Sensor-Migration
    if "sensors" in v2_config:
        for sensor_type, sensor_config in v2_config["sensors"].items():
            v3_config["sensors"][sensor_type] = {
                "enabled": True,
                "pin": sensor_config.get("pin", 34 if sensor_type == "ph" else 35),
                "calibration": sensor_config.get("calibration", {}),
                "noise_filter": {
                    "enabled": True,
                    "type": "moving_average",
                    "window_size": 10
                },
                "publishing": {
                    "rate_hz": 1.0 / sensor_config.get("reading_interval", 60),
                    "publish_raw": True,
                    "publish_calibrated": True,
                    "publish_filtered": True
                }
            }
    
    # Aktor-Migration - v2 zu v3 Mapping
    if "actuators" in v2_config:
        # v2 zu v3 Pump-Mapping
        v2_to_v3_mapping = {
            "pump_water": {"id": "water_pump", "pin": 16, "type": "relay"},
            "pump_air": {"id": "air_pump", "pin": 17, "type": "relay"},
            "pump_ph_down": {"id": "ph_down", "pin": 18, "type": "peristaltic"},
            "pump_ph_up": {"id": "ph_up", "pin": 19, "type": "peristaltic"},
            "pump_nutrient_1": {"id": "nutrient_a", "pin": 20, "type": "peristaltic"},
            "pump_nutrient_2": {"id": "nutrient_b", "pin": 21, "type": "peristaltic"},
            "pump_nutrient_3": {"id": "cal_mag", "pin": 22, "type": "peristaltic"}
        }
        
        for v2_pump_id, pump_config in v2_config["actuators"].items():
            if v2_pump_id in v2_to_v3_mapping:
                mapping = v2_to_v3_mapping[v2_pump_id]
                v3_config["actuators"][mapping["id"]] = {
                    "enabled": True,
                    "pin": mapping["pin"],
                    "type": mapping["type"],
                    "flow_rate_ml_per_sec": pump_config.get("flow_rate", 1.0),
                    "max_runtime_sec": 300,
                    "cooldown_sec": 60
                }
    
    return v3_config

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: migrate_config.py <v2_config.json> <v3_config.json>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        v2_config = json.load(f)
    
    v3_config = migrate_v2_to_v3(v2_config)
    
    with open(sys.argv[2], 'w') as f:
        json.dump(v3_config, f, indent=2)
    
    print(f"Migration complete: {sys.argv[1]} -> {sys.argv[2]}")
```

### 10.3 Debug-Tools für Live-Migration
#### debug/mqtt_monitor.py
```python
#!/usr/bin/env python3
"""
MQTT-Monitor für Live-Debugging während Migration
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

class MQTTMonitor:
    def __init__(self, broker_host, broker_port=1883):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.broker_host = broker_host
        self.broker_port = broker_port
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker with result code {rc}")
        # Subscribe zu allen HomeGrow Topics
        client.subscribe("homegrow/+/+/+")
        client.subscribe("homegrow/devices/+/+/+")
        
    def on_message(self, client, userdata, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        topic = msg.topic
        
        try:
            payload = json.loads(msg.payload.decode())
            payload_str = json.dumps(payload, indent=2)
        except:
            payload_str = msg.payload.decode()
        
        print(f"[{timestamp}] {topic}")
        print(f"  {payload_str}")
        print("-" * 50)
        
    def start_monitoring(self):
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_forever()

if __name__ == "__main__":
    monitor = MQTTMonitor("192.168.1.100")  # Broker-IP anpassen
    monitor.start_monitoring()
```

### 10.4 Hardware-Validierung
#### debug/hardware_test.cpp
```cpp
// Minimaler Hardware-Test ohne MQTT
void setup() {
    Serial.begin(115200);
    delay(2000);
    
    Serial.println("=== HomeGrow v3 Hardware Test ===");
    
    // Pin-Tests
    testSensorPins();
    testActuatorPins();
    testMemory();
    
    Serial.println("Hardware test complete.");
}

void testSensorPins() {
    Serial.println("Testing sensor pins...");
    
    // pH-Sensor (Pin 34)
    int ph_raw = analogRead(34);
    Serial.printf("pH Sensor (Pin 34): %d\n", ph_raw);
    
    // TDS-Sensor (Pin 35)
    int tds_raw = analogRead(35);
    Serial.printf("TDS Sensor (Pin 35): %d\n", tds_raw);
}

void testActuatorPins() {
    Serial.println("Testing actuator pins...");
    
    int pins[] = {16, 17, 18, 19, 20, 21, 22};
    String names[] = {"Water", "Air", "pH Down", "pH Up", "Nutrient A", "Nutrient B", "Cal-Mag"};
    
    for(int i = 0; i < 7; i++) {
        pinMode(pins[i], OUTPUT);
        
        Serial.printf("Testing %s Pump (Pin %d)...", names[i].c_str(), pins[i]);
        digitalWrite(pins[i], HIGH);
        delay(100);
        digitalWrite(pins[i], LOW);
        Serial.println(" OK");
    }
}

void testMemory() {
    Serial.println("Memory status:");
    Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("Total Heap: %d bytes\n", ESP.getHeapSize());
    Serial.printf("Free PSRAM: %d bytes\n", ESP.getFreePsram());
}

void loop() {
    delay(1000);
}
```

### 10.5 Rollback-Plan
#### rollback/rollback_procedure.md
```markdown
# Rollback-Procedure HomeGrow Client v3

## Wenn v3 nicht funktioniert:

### Sofortmaßnahmen (< 5 Minuten)
1. v2 Firmware wieder flashen
2. v2 Konfiguration wiederherstellen
3. MQTT-Broker auf v2 Topics zurückstellen
4. System-Funktionalität prüfen

### Backup-Dateien bereithalten:
- `homegrow_client_v2_backup.bin` (Firmware)
- `v2_config_backup.json` (Konfiguration)
- `v2_calibration_backup.json` (Kalibrierungsdaten)

### Rollback-Command:
```bash
# v2 Firmware flashen
pio run --target upload --upload-port /dev/ttyUSB0 --project-dir ../homegrow_client_v2

# v2 Konfiguration wiederherstellen
mosquitto_pub -h 192.168.1.100 -t "homegrow/homegrow_client_1/config" -f v2_config_backup.json
```
```

### 10.6 MQTT-Topics v3 Schema
#### Sensor-Daten
```
homegrow/devices/{device_id}/sensors/ph
homegrow/devices/{device_id}/sensors/tds
```

#### Commands
```
homegrow/devices/{device_id}/commands
homegrow/devices/{device_id}/commands/response
```

#### System-Status
```
homegrow/devices/{device_id}/heartbeat
homegrow/devices/{device_id}/status
homegrow/devices/{device_id}/logs
```

#### Konfiguration
```
homegrow/devices/{device_id}/config/request
homegrow/devices/{device_id}/config/response
```

### 10.7 Validierung Phase 10
- [ ] Migrations-Tools getestet
- [ ] Debug-Tools funktionieren
- [ ] Hardware-Test läuft
- [ ] Rollback-Plan dokumentiert
- [ ] Alle Backup-Dateien erstellt
- [ ] v3 MQTT-Topics dokumentiert

## Zusammenfassung & Erfolgskriterien

### Gesamte Implementierung
- **Geschätzte Entwicklungszeit**: 8 Tage
- **Geschätzte Migrations-Zeit**: 4-6 Stunden
- **Memory-Target**: < 80% (ca. 400KB von 520KB)
- **Code-Zeilen**: ca. 8000-10000 Zeilen

### Erfolgskriterien für Sonntag
1. **System startet**: Alle States werden durchlaufen
2. **Sensoren funktionieren**: pH/TDS-Werte werden gelesen und publiziert
3. **Pumpen funktionieren**: Alle 7 Pumpen sind steuerbar
4. **MQTT funktioniert**: v3 Topics und erweiterte Payloads
5. **Commands funktionieren**: Basis- und Advanced-Commands werden ausgeführt
6. **Safety funktioniert**: Emergency-Stop bei kritischen Werten
7. **Monitoring funktioniert**: Heartbeat mit allen Daten

### Risiko-Mitigation
- **Backup-Plan**: v2 System kann in < 5 Minuten wiederhergestellt werden
- **Clean Migration**: Kompletter Wechsel zu v3 ohne Legacy-Ballast
- **Schrittweise Migration**: Einzelne Features können deaktiviert werden
- **Remote-Debugging**: Umfangreiche Logs über MQTT
- **Hardware-Schutz**: Safety-System verhindert Schäden

### Nächste Schritte nach erfolgreicher Migration
1. **Monitoring**: 24h Überwachung der Stabilität
2. **Optimierung**: Performance-Tuning basierend auf Live-Daten
3. **Features**: Erweiterte Commands und Automatisierung
4. **Documentation**: Benutzer-Handbuch und API-Dokumentation

Diese Implementierungsstrategie gewährleistet eine strukturierte, sichere und nachvollziehbare Entwicklung des HomeGrow Client v3 ohne Hardware-Tests, mit dem Ziel einer erfolgreichen Migration am Sonntag. 