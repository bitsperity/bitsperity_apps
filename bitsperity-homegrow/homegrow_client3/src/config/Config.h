#ifndef CONFIG_H
#define CONFIG_H

#include <ArduinoJson.h>
#include "../core/Types.h"

// WiFi-Konfiguration
struct WiFiConfig {
    String ssid;
    String password;
    String hostname;
    String static_ip;  // Optional
    String dns_servers[2];
};

// MQTT-Konfiguration
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

// Sensor-Konfiguration
struct SensorConfig {
    bool enabled;
    int pin;
    DynamicJsonDocument calibration{256};
    DynamicJsonDocument noise_filter{256};
    DynamicJsonDocument publishing{256};
};

// Aktor-Konfiguration
struct ActuatorConfig {
    bool enabled;
    int pin;
    String type;
    float flow_rate_ml_per_sec;
    int max_runtime_sec;
    int cooldown_sec;
    DynamicJsonDocument scheduled{256};
    String substance;  // Für Dosierpumpen
    String concentration;
};

// Safety-Konfiguration
struct SafetyConfig {
    float ph_min;
    float ph_max;
    float tds_max;
    int pump_max_runtime_sec;
    int pump_cooldown_sec;
    float outlier_threshold;
    bool plausibility_checks;
};

// System-Konfiguration
struct SystemConfig {
    bool watchdog_enabled;
    int watchdog_timeout_sec;
    bool ota_enabled;
    String ota_password;
    int ota_port;
    String log_level;
    bool serial_logging;
    bool mqtt_logging;
    int heartbeat_interval_sec;
};

class Config {
private:
    DynamicJsonDocument config_doc{4096};
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
    SystemConfig system;
    
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
    bool isLoaded() const { return loaded; }
    
    // Getter für spezifische Konfigurationen
    ActuatorConfig* getDosingPump(const String& pump_id);
    SensorConfig* getSensor(SensorType type);
    
private:
    void parseWiFiConfig(const JsonObject& wifi_obj);
    void parseMQTTConfig(const JsonObject& mqtt_obj);
    void parseSensorConfig(SensorConfig& sensor, const JsonObject& sensor_obj);
    void parseActuatorConfig(ActuatorConfig& actuator, const JsonObject& actuator_obj);
    void parseSafetyConfig(const JsonObject& safety_obj);
    void parseSystemConfig(const JsonObject& system_obj);
    void parseDosingPumps(const JsonArray& pumps_array);
};

#endif // CONFIG_H 