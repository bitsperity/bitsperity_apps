# HomeGrow Server - Implementierungsplan

Dieser Plan beschreibt die Struktur und Implementierung des HomeGrow Servers basierend auf den Anforderungen im README.md.

## Architektur

```mermaid
flowchart TB
    subgraph "HomeGrow Server"
        MQTT[MQTT-Client]
        AutoLogic[Automatisierungslogik]
        Rules[Regelengine]
        DeviceManager[Gerätemanager]
        Config[Konfigurationsmanager]
        Logger[Logger]
    end
    
    MQTT <--> Broker[MQTT Broker]
    MQTT <--> AutoLogic
    AutoLogic <--> Rules
    AutoLogic <--> DeviceManager
    DeviceManager <--> Config
    AutoLogic --> Logger
    DeviceManager --> MongoDB[(MongoDB)]
```

## Verzeichnisstruktur

```mermaid
flowchart TD
    homegrow_server --> src
    homegrow_server --> config
    homegrow_server --> rules
    homegrow_server --> tests
    homegrow_server --> requirements.txt
    homegrow_server --> README.md
    homegrow_server --> Dockerfile
    
    src --> main.py
    src --> mqtt_client.py
    src --> automation.py
    src --> rules_engine.py
    src --> device_manager.py
    src --> config_manager.py
    src --> logger.py
    src --> models
    
    models --> device.py
    models --> rule.py
    models --> sensor_data.py
    
    config --> config.yaml
    rules --> default_rules.json
```

## Klassendiagramm

```mermaid
classDiagram
    class MQTTClient {
        -client
        -config
        -device_manager
        -automation
        +connect()
        +disconnect()
        +publish(topic, payload)
        +subscribe(topic)
        +on_message(client, userdata, message)
        +handle_sensor_data(device_id, data)
        +handle_heartbeat(device_id, data)
        +handle_config_request(device_id, data)
    }
    
    class DeviceManager {
        -devices
        -config_manager
        -db_client
        +get_device(device_id)
        +register_device(device_id, info)
        +update_device(device_id, info)
        +get_all_devices()
        +get_device_config(device_id)
        +save_device_config(device_id, config)
        +create_default_config(device_id)
    }
    
    class ConfigManager {
        -config
        -db_client
        +load_config()
        +save_config()
        +get_device_config(device_id)
        +save_device_config(device_id, config)
        +create_default_config(device_id)
    }
    
    class Automation {
        -rules_engine
        -device_manager
        -mqtt_client
        +process_sensor_data(device_id, sensor_data)
        +check_rules(device_id, sensor_data)
        +execute_action(device_id, action)
    }
    
    class RulesEngine {
        -rules
        +load_rules(rules_file)
        +evaluate_rule(rule, sensor_data)
        +get_actions(rule, sensor_data)
    }
    
    class Logger {
        +setup()
        +get_logger(name)
    }
    
    class Device {
        -id
        -status
        -last_seen
        -sensors
        -config
        +update_status(status)
        +update_sensor_data(sensor_data)
        +get_config()
        +set_config(config)
    }
    
    class Rule {
        -id
        -description
        -conditions
        -actions
        -enabled
        +evaluate(sensor_data)
        +get_actions()
    }
    
    class SensorData {
        -device_id
        -timestamp
        -values
        +get_value(sensor_type)
    }
    
    MQTTClient --> DeviceManager
    MQTTClient --> Automation
    DeviceManager --> ConfigManager
    DeviceManager --> Device
    Automation --> RulesEngine
    Automation --> DeviceManager
    RulesEngine --> Rule
    DeviceManager ..> SensorData
    Automation ..> SensorData
```

## Datenfluss

```mermaid
sequenceDiagram
    participant Client as HomeGrow Client
    participant Broker as MQTT Broker
    participant Server as HomeGrow Server
    participant DB as MongoDB
    
    Client->>Broker: Sensordaten senden (homegrow/{client_id}/sensor/ph)
    Broker->>Server: Sensordaten empfangen
    Server->>DB: Sensordaten speichern
    Server->>Server: Regeln auswerten
    
    alt Aktion erforderlich
        Server->>Broker: Befehl senden (homegrow/{client_id}/command)
        Broker->>Client: Befehl empfangen
    end
    
    Client->>Broker: Konfiguration anfragen (homegrow/{client_id}/config/request)
    Broker->>Server: Konfigurationsanfrage empfangen
    Server->>DB: Konfiguration laden
    
    alt Konfiguration existiert
        Server->>Broker: Konfiguration senden (homegrow/{client_id}/config/response)
    else Konfiguration existiert nicht
        Server->>Server: Standardkonfiguration erstellen
        Server->>DB: Standardkonfiguration speichern
        Server->>Broker: Standardkonfiguration senden (homegrow/{client_id}/config/response)
    end
    
    Broker->>Client: Konfiguration empfangen
```

## MQTT-Topics

### Abonnierte Topics
- `homegrow/+/sensor/#`: Sensordaten von allen Geräten
- `homegrow/+/heartbeat`: Heartbeat-Nachrichten von allen Geräten
- `homegrow/+/config/request`: Konfigurationsanfragen von allen Geräten

### Veröffentlichte Topics
- `homegrow/{device_id}/command`: Befehle an Geräte
- `homegrow/{device_id}/config/response`: Konfigurationsantworten an Geräte

## Implementierungsdetails

### main.py
- Haupteinstiegspunkt der Anwendung
- Initialisiert alle Komponenten
- Startet den MQTT-Client
- Verarbeitet Signale für sauberes Herunterfahren

### mqtt_client.py
- Verbindung zum MQTT-Broker
- Abonnieren von Topics
- Verarbeitung eingehender Nachrichten
- Weiterleitung an entsprechende Handler

### device_manager.py
- Verwaltung von Geräten
- Laden und Speichern von Gerätekonfigurationen
- Erstellen von Standardkonfigurationen für neue Geräte

### config_manager.py
- Laden und Speichern der Serverkonfiguration
- Verwaltung von Gerätekonfigurationen
- Schnittstelle zur MongoDB

### automation.py
- Verarbeitung von Sensordaten
- Auswertung von Regeln
- Ausführung von Aktionen

### rules_engine.py
- Laden und Verwalten von Regeln
- Auswertung von Bedingungen
- Generierung von Aktionen

### logger.py
- Konfiguration des Loggings
- Bereitstellung von Loggern für andere Komponenten

### models/device.py
- Datenmodell für Geräte
- Status und Konfiguration

### models/rule.py
- Datenmodell für Regeln
- Bedingungen und Aktionen

### models/sensor_data.py
- Datenmodell für Sensordaten
- Zeitstempel und Werte

## MongoDB-Sammlungen

- `devices`: Informationen über Geräte
- `configs`: Gerätekonfigurationen
- `sensor_data`: Historische Sensordaten
- `rules`: Automatisierungsregeln

## Konfigurationsbeispiel (config.yaml)

```yaml
mqtt:
  broker: "localhost"
  port: 1883
  client_id: "homegrow_server"
  username: ""
  password: ""

mongodb:
  uri: "mongodb://localhost:27017"
  database: "homegrow"

logging:
  level: "info"
  file: "/var/log/homegrow/server.log"

automation:
  check_interval: 60  # Sekunden
  rules_file: "/etc/homegrow/rules.json"
```

## Standardkonfiguration für Geräte

```json
{
  "client_id": "{device_id}",
  "sensors": {
    "ph": {
      "pin": 34,
      "calibration": {
        "offset": 0.0,
        "scale": 1.0
      }
    },
    "tds": {
      "pin": 35,
      "calibration": {
        "offset": 0.0,
        "scale": 1.0
      }
    }
  },
  "actuators": {
    "water_pump": {
      "pin": 16,
      "flow_rate": 100.0
    },
    "air_pump": {
      "pin": 17
    },
    "ph_up_pump": {
      "pin": 18,
      "flow_rate": 10.0
    },
    "ph_down_pump": {
      "pin": 19,
      "flow_rate": 10.0
    },
    "nutrient_pump_1": {
      "pin": 21,
      "flow_rate": 10.0
    },
    "nutrient_pump_2": {
      "pin": 22,
      "flow_rate": 10.0
    },
    "nutrient_pump_3": {
      "pin": 23,
      "flow_rate": 10.0
    }
  }
}
``` 