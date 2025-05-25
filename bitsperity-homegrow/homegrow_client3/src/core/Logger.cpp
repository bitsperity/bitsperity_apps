#include "Logger.h"
#include "../network/MQTTClient.h"

// Statische Member-Initialisierung
LogLevel Logger::current_level = LogLevel::INFO;
bool Logger::mqtt_enabled = false;
String Logger::device_id = "";
MQTTClient* Logger::mqtt_client = nullptr;

void Logger::init(const String& dev_id, LogLevel level) {
    device_id = dev_id;
    current_level = level;
    
    Serial.println("=== Logger initialized ===");
    Serial.println("Device ID: " + device_id);
    Serial.println("Log Level: " + levelToString(level));
}

void Logger::setMQTTClient(MQTTClient* client) {
    mqtt_client = client;
}

void Logger::setMQTTEnabled(bool enabled) {
    mqtt_enabled = enabled;
}

void Logger::setLevel(LogLevel level) {
    current_level = level;
}

void Logger::debug(const String& message, const String& component) {
    log(LogLevel::DEBUG, message, component);
}

void Logger::info(const String& message, const String& component) {
    log(LogLevel::INFO, message, component);
}

void Logger::warn(const String& message, const String& component) {
    log(LogLevel::WARN, message, component);
}

void Logger::error(const String& message, const String& component) {
    log(LogLevel::ERROR, message, component);
}

void Logger::logCommand(const String& command_id, const String& command, const JsonObject& params) {
    DynamicJsonDocument doc(256);
    doc["command_id"] = command_id;
    doc["command"] = command;
    doc["params"] = params;
    
    logSystemEvent("command_received", doc.as<JsonObject>());
}

void Logger::logSensorReading(SensorType type, const SensorReading& reading) {
    DynamicJsonDocument doc(256);
    doc["sensor_type"] = (type == SensorType::PH) ? "ph" : "tds";
    doc["raw"] = reading.raw;
    doc["calibrated"] = reading.calibrated;
    doc["filtered"] = reading.filtered;
    doc["quality"] = reading.quality;
    doc["calibration_valid"] = reading.calibration_valid;
    
    logSystemEvent("sensor_reading", doc.as<JsonObject>());
}

void Logger::logSystemEvent(const String& event, const JsonObject& data) {
    DynamicJsonDocument doc(512);
    doc["event"] = event;
    doc["data"] = data;
    doc["timestamp"] = millis();
    
    log(LogLevel::INFO, "System Event: " + event, "System");
    
    if (mqtt_enabled && mqtt_client) {
        publishLog(doc);
    }
}

void Logger::logActuatorEvent(const String& actuator_id, const String& event, const JsonObject& data) {
    DynamicJsonDocument doc(512);
    doc["actuator_id"] = actuator_id;
    doc["event"] = event;
    doc["data"] = data;
    doc["timestamp"] = millis();
    
    log(LogLevel::INFO, "Actuator Event: " + actuator_id + " - " + event, "Actuator");
    
    if (mqtt_enabled && mqtt_client) {
        publishLog(doc);
    }
}

void Logger::log(LogLevel level, const String& message, const String& component) {
    if (level < current_level) return;
    
    String timestamp = formatTimestamp();
    String levelStr = levelToString(level);
    String componentStr = component.isEmpty() ? "" : "[" + component + "] ";
    
    // Serial-Ausgabe
    Serial.print(timestamp);
    Serial.print(" [");
    Serial.print(levelStr);
    Serial.print("] ");
    Serial.print(componentStr);
    Serial.println(message);
    
    // MQTT-Logging wenn aktiviert
    if (mqtt_enabled && mqtt_client && level >= LogLevel::WARN) {
        DynamicJsonDocument logEntry(256);
        logEntry["timestamp"] = millis();
        logEntry["level"] = levelToString(level);
        logEntry["message"] = message;
        logEntry["component"] = component;
        logEntry["device_id"] = device_id;
        publishLog(logEntry);
    }
}

String Logger::levelToString(LogLevel level) {
    switch (level) {
        case LogLevel::DEBUG: return "DEBUG";
        case LogLevel::INFO: return "INFO";
        case LogLevel::WARN: return "WARN";
        case LogLevel::ERROR: return "ERROR";
        default: return "UNKNOWN";
    }
}

String Logger::formatTimestamp() {
    unsigned long ms = millis();
    unsigned long seconds = ms / 1000;
    unsigned long minutes = seconds / 60;
    unsigned long hours = minutes / 60;
    
    char buffer[20];
    sprintf(buffer, "%02lu:%02lu:%02lu.%03lu", 
            hours % 24, minutes % 60, seconds % 60, ms % 1000);
    
    return String(buffer);
}

DynamicJsonDocument Logger::createLogEntry(LogLevel level, const String& message, const String& component) {
    DynamicJsonDocument doc(256);
    doc["timestamp"] = millis();
    doc["level"] = levelToString(level);
    doc["message"] = message;
    doc["component"] = component;
    doc["device_id"] = device_id;
    
    return doc;
}

void Logger::publishLog(const DynamicJsonDocument& log_entry) {
    if (!mqtt_client) return;
    
    String topic = "homegrow/devices/" + device_id + "/logs";
    String payload;
    serializeJson(log_entry, payload);
    
    // MQTTClient::publishLog wird später implementiert
    // mqtt_client->publishLog(log_entry);
} 