#ifndef TYPES_H
#define TYPES_H

#include <Arduino.h>
#include <ArduinoJson.h>

// System-Zustände
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

// Sensor-Typen
enum class SensorType {
    PH,
    TDS
};

// Aktor-Typen
enum class ActuatorType {
    WATER_PUMP,
    AIR_PUMP,
    DOSING_PUMP
};

// Command-Status
enum class CommandStatus {
    PENDING,
    EXECUTING,
    COMPLETED,
    FAILED,
    TIMEOUT
};

// Sensor-Messwerte
struct SensorReading {
    float raw;
    float calibrated;
    float filtered;
    unsigned long timestamp;
    String quality;
    bool calibration_valid;
};

// Command-Ergebnis
struct CommandResult {
    String command_id;
    CommandStatus status;
    String error_message;
    DynamicJsonDocument result_data{512};
    unsigned long execution_time_ms;
};

// Safety-Level
enum class SafetyLevel {
    NORMAL,
    WARNING,
    CRITICAL,
    EMERGENCY
};

// Aktor-Zustand
enum class ActuatorState {
    IDLE,
    ACTIVE,
    COOLDOWN,
    ERROR,
    ACTUATOR_DISABLED
};

#endif // TYPES_H 