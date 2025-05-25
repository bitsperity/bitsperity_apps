#ifndef LOGGER_H
#define LOGGER_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include "Types.h"

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
    static class MQTTClient* mqtt_client;
    
public:
    static void init(const String& device_id, LogLevel level = LogLevel::INFO);
    static void setMQTTClient(class MQTTClient* client);
    static void setMQTTEnabled(bool enabled);
    static void setLevel(LogLevel level);
    
    // Basis-Logging
    static void debug(const String& message, const String& component = "");
    static void info(const String& message, const String& component = "");
    static void warn(const String& message, const String& component = "");
    static void error(const String& message, const String& component = "");
    
    // Spezielle Log-Funktionen
    static void logCommand(const String& command_id, const String& command, const JsonObject& params);
    static void logSensorReading(SensorType type, const SensorReading& reading);
    static void logSystemEvent(const String& event, const JsonObject& data = JsonObject());
    static void logActuatorEvent(const String& actuator_id, const String& event, const JsonObject& data = JsonObject());
    
private:
    static void log(LogLevel level, const String& message, const String& component);
    static String levelToString(LogLevel level);
    static String formatTimestamp();
    static DynamicJsonDocument createLogEntry(LogLevel level, const String& message, const String& component);
    static void publishLog(const DynamicJsonDocument& log_entry);
};

#endif // LOGGER_H 