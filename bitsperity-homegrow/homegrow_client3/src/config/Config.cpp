#include "Config.h"
#include "default_config.h"
#include "../core/Logger.h"

Config::Config() : loaded(false) {
    // Initialisiere mit Default-Werten
    device_id = "homegrow_client_001";
    device_name = "HomeGrow Client v3";
    location = "Gewächshaus";
    firmware_version = "3.0.0";
    hardware_version = "1.0";
}

bool Config::loadFromJson(const String& json) {
    DeserializationError error = deserializeJson(config_doc, json);
    
    if (error) {
        Logger::error("Failed to parse config JSON: " + String(error.c_str()), "Config");
        return false;
    }
    
    // Device-Konfiguration
    JsonObject device = config_doc["device"];
    if (device) {
        device_id = device["id"] | device_id;
        device_name = device["name"] | device_name;
        location = device["location"] | location;
        firmware_version = device["firmware_version"] | firmware_version;
        hardware_version = device["hardware_version"] | hardware_version;
    }
    
    // WiFi-Konfiguration
    JsonObject wifi_obj = config_doc["wifi"];
    if (wifi_obj) {
        parseWiFiConfig(wifi_obj);
    }
    
    // MQTT-Konfiguration
    JsonObject mqtt_obj = config_doc["mqtt"];
    if (mqtt_obj) {
        parseMQTTConfig(mqtt_obj);
    }
    
    // Sensor-Konfigurationen
    JsonObject sensors = config_doc["sensors"];
    if (sensors) {
        JsonObject ph = sensors["ph"];
        if (ph) parseSensorConfig(ph_sensor, ph);
        
        JsonObject tds = sensors["tds"];
        if (tds) parseSensorConfig(tds_sensor, tds);
    }
    
    // Aktor-Konfigurationen
    JsonObject actuators = config_doc["actuators"];
    if (actuators) {
        JsonObject water = actuators["water_pump"];
        if (water) parseActuatorConfig(water_pump, water);
        
        JsonObject air = actuators["air_pump"];
        if (air) parseActuatorConfig(air_pump, air);
        
        JsonArray pumps = actuators["dosing_pumps"];
        if (pumps) parseDosingPumps(pumps);
    }
    
    // Safety-Konfiguration
    JsonObject safety_obj = config_doc["safety"];
    if (safety_obj) {
        parseSafetyConfig(safety_obj);
    }
    
    // System-Konfiguration
    JsonObject system_obj = config_doc["system"];
    if (system_obj) {
        parseSystemConfig(system_obj);
    }
    
    loaded = true;
    Logger::info("Configuration loaded successfully", "Config");
    return true;
}

bool Config::loadDefaults() {
    return loadFromJson(DEFAULT_CONFIG_JSON);
}

void Config::parseWiFiConfig(const JsonObject& wifi_obj) {
    wifi.ssid = wifi_obj["ssid"] | "";
    wifi.password = wifi_obj["password"] | "";
    wifi.hostname = wifi_obj["hostname"] | "homegrow-client";
    wifi.static_ip = wifi_obj["static_ip"] | "";
    
    JsonArray dns = wifi_obj["dns_servers"];
    if (dns && dns.size() >= 2) {
        wifi.dns_servers[0] = dns[0] | "8.8.8.8";
        wifi.dns_servers[1] = dns[1] | "8.8.4.4";
    }
}

void Config::parseMQTTConfig(const JsonObject& mqtt_obj) {
    JsonObject discovery = mqtt_obj["broker_discovery"];
    if (discovery) {
        mqtt.broker_discovery_enabled = discovery["enabled"] | true;
        mqtt.service_name = discovery["service_name"] | "_mqtt._tcp";
        mqtt.fallback_host = discovery["fallback_host"] | "192.168.1.100";
        mqtt.fallback_port = discovery["fallback_port"] | 1883;
    }
    
    JsonObject auth = mqtt_obj["auth"];
    if (auth) {
        mqtt.username = auth["username"] | "";
        mqtt.password = auth["password"] | "";
    }
    
    mqtt.qos = mqtt_obj["qos"] | 1;
    mqtt.retain = mqtt_obj["retain"] | false;
    mqtt.keepalive = mqtt_obj["keepalive"] | 60;
    mqtt.clean_session = mqtt_obj["clean_session"] | true;
}

void Config::parseSensorConfig(SensorConfig& sensor, const JsonObject& sensor_obj) {
    sensor.enabled = sensor_obj["enabled"] | true;
    sensor.pin = sensor_obj["pin"] | 34;
    
    // Kalibrierung als JsonDocument speichern
    JsonObject cal = sensor_obj["calibration"];
    if (cal) {
        sensor.calibration.clear();
        sensor.calibration.set(cal);
    }
    
    // Noise-Filter als JsonDocument speichern
    JsonObject filter = sensor_obj["noise_filter"];
    if (filter) {
        sensor.noise_filter.clear();
        sensor.noise_filter.set(filter);
    }
    
    // Publishing als JsonDocument speichern
    JsonObject pub = sensor_obj["publishing"];
    if (pub) {
        sensor.publishing.clear();
        sensor.publishing.set(pub);
    }
}

void Config::parseActuatorConfig(ActuatorConfig& actuator, const JsonObject& actuator_obj) {
    actuator.enabled = actuator_obj["enabled"] | true;
    actuator.pin = actuator_obj["pin"] | 16;
    actuator.type = actuator_obj["type"] | "relay";
    actuator.flow_rate_ml_per_sec = actuator_obj["flow_rate_ml_per_sec"] | 1.0;
    actuator.max_runtime_sec = actuator_obj["max_runtime_sec"] | 300;
    actuator.cooldown_sec = actuator_obj["cooldown_sec"] | 60;
    
    JsonObject sched = actuator_obj["scheduled"];
    if (sched) {
        actuator.scheduled.clear();
        actuator.scheduled.set(sched);
    }
    
    actuator.substance = actuator_obj["substance"] | "";
    actuator.concentration = actuator_obj["concentration"] | "";
}

void Config::parseDosingPumps(const JsonArray& pumps_array) {
    int index = 0;
    for (JsonObject pump : pumps_array) {
        if (index >= 5) break;
        
        parseActuatorConfig(dosing_pumps[index], pump);
        
        // ID-Mapping für einfacheren Zugriff
        String id = pump["id"] | "";
        if (id == "ph_down") index = 0;
        else if (id == "ph_up") index = 1;
        else if (id == "nutrient_a") index = 2;
        else if (id == "nutrient_b") index = 3;
        else if (id == "cal_mag") index = 4;
        
        index++;
    }
}

void Config::parseSafetyConfig(const JsonObject& safety_obj) {
    JsonObject emergency = safety_obj["emergency_stop_conditions"];
    if (emergency) {
        safety.ph_min = emergency["ph_min"] | 4.0;
        safety.ph_max = emergency["ph_max"] | 8.5;
        safety.tds_max = emergency["tds_max"] | 2000;
    }
    
    JsonObject pump_prot = safety_obj["pump_protection"];
    if (pump_prot) {
        safety.pump_max_runtime_sec = pump_prot["max_runtime_sec"] | 300;
        safety.pump_cooldown_sec = pump_prot["cooldown_sec"] | 60;
    }
    
    JsonObject sensor_val = safety_obj["sensor_validation"];
    if (sensor_val) {
        safety.outlier_threshold = sensor_val["outlier_threshold"] | 2.0;
        safety.plausibility_checks = sensor_val["plausibility_checks"] | true;
    }
}

void Config::parseSystemConfig(const JsonObject& system_obj) {
    JsonObject watchdog = system_obj["watchdog"];
    if (watchdog) {
        system.watchdog_enabled = watchdog["enabled"] | true;
        system.watchdog_timeout_sec = watchdog["timeout_sec"] | 30;
    }
    
    JsonObject ota = system_obj["ota"];
    if (ota) {
        system.ota_enabled = ota["enabled"] | true;
        system.ota_password = ota["password"] | "homegrow_ota";
        system.ota_port = ota["port"] | 3232;
    }
    
    JsonObject logging = system_obj["logging"];
    if (logging) {
        system.log_level = logging["level"] | "INFO";
        system.serial_logging = logging["serial"] | true;
        system.mqtt_logging = logging["mqtt"] | true;
    }
    
    JsonObject status = system_obj["status"];
    if (status) {
        system.heartbeat_interval_sec = status["heartbeat_interval_sec"] | 30;
    }
}

ActuatorConfig* Config::getDosingPump(const String& pump_id) {
    if (pump_id == "ph_down") return &dosing_pumps[0];
    if (pump_id == "ph_up") return &dosing_pumps[1];
    if (pump_id == "nutrient_a") return &dosing_pumps[2];
    if (pump_id == "nutrient_b") return &dosing_pumps[3];
    if (pump_id == "cal_mag") return &dosing_pumps[4];
    return nullptr;
}

SensorConfig* Config::getSensor(SensorType type) {
    switch (type) {
        case SensorType::PH:
            return &ph_sensor;
        case SensorType::TDS:
            return &tds_sensor;
        default:
            return nullptr;
    }
}

bool Config::validate() const {
    // Basis-Validierung
    if (device_id.isEmpty()) {
        Logger::error("Device ID is empty", "Config");
        return false;
    }
    
    // WiFi-Validierung
    if (wifi.ssid.isEmpty()) {
        Logger::warn("WiFi SSID is empty", "Config");
    }
    
    // MQTT-Validierung
    if (!mqtt.broker_discovery_enabled && mqtt.fallback_host.isEmpty()) {
        Logger::error("No MQTT broker configured", "Config");
        return false;
    }
    
    // Sensor-Validierung
    if (!ph_sensor.enabled && !tds_sensor.enabled) {
        Logger::warn("No sensors enabled", "Config");
    }
    
    // Safety-Validierung
    if (safety.ph_min >= safety.ph_max) {
        Logger::error("Invalid pH safety range", "Config");
        return false;
    }
    
    return true;
}

String Config::toJson() const {
    String output;
    serializeJsonPretty(config_doc, output);
    return output;
} 