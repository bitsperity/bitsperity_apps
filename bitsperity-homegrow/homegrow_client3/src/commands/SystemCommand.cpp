#include "SystemCommand.h"
#include <WiFi.h>

// EmergencyStopCommand Implementation
EmergencyStopCommand::EmergencyStopCommand(const String& cmd_id, ActuatorManager* manager) :
    BaseCommand(cmd_id, "emergency_stop"),
    actuator_manager(manager) {
}

bool EmergencyStopCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    // Reason ist optional
    getStringParam("reason", reason);
    if (reason.length() == 0) {
        reason = "Manual emergency stop";
    }
    
    return true;
}

bool EmergencyStopCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    Logger::error("EMERGENCY STOP ACTIVATED: " + reason, "EmergencyStopCommand");
    
    actuator_manager->emergencyStop(reason);
    
    DynamicJsonDocument result(256);
    result["message"] = "Emergency stop activated";
    result["reason"] = reason;
    result["timestamp"] = millis();
    setResultData(result.as<JsonObject>());
    setStatus(CommandStatus::COMPLETED);
    
    return true;
}

void EmergencyStopCommand::abort() {
    // Emergency Stop kann nicht abgebrochen werden
}

// ClearEmergencyStopCommand Implementation
ClearEmergencyStopCommand::ClearEmergencyStopCommand(const String& cmd_id, ActuatorManager* manager) :
    BaseCommand(cmd_id, "clear_emergency_stop"),
    actuator_manager(manager) {
}

bool ClearEmergencyStopCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    return true; // Keine Parameter erforderlich
}

bool ClearEmergencyStopCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    if (!actuator_manager->isEmergencyStopActive()) {
        setError("No emergency stop is currently active");
        return false;
    }
    
    actuator_manager->clearEmergencyStop();
    
    DynamicJsonDocument result(256);
    result["message"] = "Emergency stop cleared";
    result["timestamp"] = millis();
    setResultData(result.as<JsonObject>());
    setStatus(CommandStatus::COMPLETED);
    
    Logger::info("Emergency stop cleared", "ClearEmergencyStopCommand");
    
    return true;
}

void ClearEmergencyStopCommand::abort() {
    // Kann nicht abgebrochen werden
}

// CalibrateSensorCommand Implementation
CalibrateSensorCommand::CalibrateSensorCommand(const String& cmd_id, SensorManager* manager) :
    BaseCommand(cmd_id, "calibrate_sensor"),
    sensor_manager(manager),
    sensor_type(SensorType::PH) {
}

bool CalibrateSensorCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    String sensor_id;
    if (!getStringParam("sensor_id", sensor_id)) {
        setError("Missing sensor_id parameter");
        return false;
    }
    
    sensor_type = parseSensorType(sensor_id);
    if (sensor_type != SensorType::PH && sensor_type != SensorType::TDS) {
        setError("Invalid sensor_id: " + sensor_id);
        return false;
    }
    
    if (!params.containsKey("calibration_points")) {
        setError("Missing calibration_points parameter");
        return false;
    }
    
    calibration_points = params["calibration_points"];
    if (calibration_points.size() == 0) {
        setError("Empty calibration_points array");
        return false;
    }
    
    return true;
}

bool CalibrateSensorCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    String sensor_name = (sensor_type == SensorType::PH) ? "pH" : "TDS";
    Logger::info("Starting calibration for " + sensor_name + " sensor", "CalibrateSensorCommand");
    
    if (sensor_manager->calibrateSensor(sensor_type, calibration_points)) {
        DynamicJsonDocument result(256);
        result["sensor_type"] = sensor_name;
        result["calibration_points"] = calibration_points.size();
        result["message"] = "Sensor calibration successful";
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        
        Logger::info(sensor_name + " sensor calibration completed successfully", "CalibrateSensorCommand");
        return true;
    } else {
        setError("Sensor calibration failed for " + sensor_name + " sensor");
        return false;
    }
}

void CalibrateSensorCommand::abort() {
    // Kalibrierung kann nicht abgebrochen werden
}

SensorType CalibrateSensorCommand::parseSensorType(const String& sensor_id) const {
    if (sensor_id == "ph") {
        return SensorType::PH;
    } else if (sensor_id == "tds") {
        return SensorType::TDS;
    }
    
    return SensorType::PH; // Default
}

// ResetSystemCommand Implementation
ResetSystemCommand::ResetSystemCommand(const String& cmd_id, ActuatorManager* manager) :
    BaseCommand(cmd_id, "reset_system"),
    actuator_manager(manager) {
}

bool ResetSystemCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    return true; // Keine Parameter erforderlich
}

bool ResetSystemCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    Logger::info("System reset initiated", "ResetSystemCommand");
    
    // Alle Aktoren stoppen
    actuator_manager->stopAllActuators();
    
    // Emergency Stop löschen falls aktiv
    if (actuator_manager->isEmergencyStopActive()) {
        actuator_manager->clearEmergencyStop();
    }
    
    DynamicJsonDocument result(256);
    result["message"] = "System reset completed";
    result["timestamp"] = millis();
    setResultData(result.as<JsonObject>());
    setStatus(CommandStatus::COMPLETED);
    
    Logger::info("System reset completed", "ResetSystemCommand");
    
    // Nach kurzer Verzögerung ESP32 neu starten
    delay(1000);
    ESP.restart();
    
    return true;
}

void ResetSystemCommand::abort() {
    // System Reset kann nicht abgebrochen werden
}

// GetSystemStatusCommand Implementation
GetSystemStatusCommand::GetSystemStatusCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr) :
    BaseCommand(cmd_id, "get_system_status"),
    actuator_manager(actuator_mgr),
    sensor_manager(sensor_mgr) {
}

bool GetSystemStatusCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    return true; // Keine Parameter erforderlich
}

bool GetSystemStatusCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    JsonObject status = createSystemStatus();
    setResultData(status);
    setStatus(CommandStatus::COMPLETED);
    
    return true;
}

void GetSystemStatusCommand::abort() {
    // Kann nicht abgebrochen werden
}

JsonObject GetSystemStatusCommand::createSystemStatus() const {
    DynamicJsonDocument doc(2048);
    
    // System-Informationen
    doc["timestamp"] = millis();
    doc["uptime_ms"] = millis();
    doc["free_heap"] = ESP.getFreeHeap();
    doc["total_heap"] = ESP.getHeapSize();
    
    // Sensor-Status
    if (sensor_manager) {
        doc["sensors"] = sensor_manager->getStatusJson();
    }
    
    // Aktor-Status
    if (actuator_manager) {
        doc["actuators"] = actuator_manager->getStatusJson();
    }
    
    // WiFi-Status
    doc["wifi"]["connected"] = WiFi.isConnected();
    if (WiFi.isConnected()) {
        doc["wifi"]["rssi"] = WiFi.RSSI();
        doc["wifi"]["ip"] = WiFi.localIP().toString();
    }
    
    return doc.as<JsonObject>();
} 