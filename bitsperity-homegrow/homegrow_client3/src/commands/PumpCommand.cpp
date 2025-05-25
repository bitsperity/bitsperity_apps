#include "PumpCommand.h"

// ActivatePumpCommand Implementation
ActivatePumpCommand::ActivatePumpCommand(const String& cmd_id, ActuatorManager* manager) :
    BaseCommand(cmd_id, "activate_pump"),
    actuator_manager(manager),
    duration_ms(0) {
}

bool ActivatePumpCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    if (!getStringParam("pump_id", pump_id) || pump_id.length() == 0) {
        setError("Missing or invalid pump_id parameter");
        return false;
    }
    
    int duration_sec;
    if (!getIntParam("duration_sec", duration_sec) || duration_sec <= 0) {
        setError("Missing or invalid duration_sec parameter");
        return false;
    }
    
    duration_ms = duration_sec * 1000UL;
    
    if (!actuator_manager->getActuator(pump_id)) {
        setError("Pump " + pump_id + " not found");
        return false;
    }
    
    return true;
}

bool ActivatePumpCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    if (actuator_manager->activateActuator(pump_id, duration_ms)) {
        DynamicJsonDocument result(256);
        result["pump_id"] = pump_id;
        result["duration_ms"] = duration_ms;
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        return true;
    } else {
        setError("Failed to activate pump " + pump_id);
        return false;
    }
}

void ActivatePumpCommand::abort() {
    actuator_manager->deactivateActuator(pump_id);
    setStatus(CommandStatus::FAILED);
}

// StopPumpCommand Implementation
StopPumpCommand::StopPumpCommand(const String& cmd_id, ActuatorManager* manager) :
    BaseCommand(cmd_id, "stop_pump"),
    actuator_manager(manager) {
}

bool StopPumpCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    if (!getStringParam("pump_id", pump_id) || pump_id.length() == 0) {
        setError("Missing or invalid pump_id parameter");
        return false;
    }
    
    if (!actuator_manager->getActuator(pump_id)) {
        setError("Pump " + pump_id + " not found");
        return false;
    }
    
    return true;
}

bool StopPumpCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    if (actuator_manager->deactivateActuator(pump_id)) {
        DynamicJsonDocument result(256);
        result["pump_id"] = pump_id;
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        return true;
    } else {
        setError("Failed to stop pump " + pump_id);
        return false;
    }
}

void StopPumpCommand::abort() {
    // Nichts zu tun, da wir bereits stoppen
}

// StopAllPumpsCommand Implementation
StopAllPumpsCommand::StopAllPumpsCommand(const String& cmd_id, ActuatorManager* manager) :
    BaseCommand(cmd_id, "stop_all_pumps"),
    actuator_manager(manager) {
}

bool StopAllPumpsCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    return true; // Keine Parameter erforderlich
}

bool StopAllPumpsCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    if (actuator_manager->stopAllActuators()) {
        DynamicJsonDocument result(256);
        result["message"] = "All pumps stopped";
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        return true;
    } else {
        setError("Failed to stop all pumps");
        return false;
    }
}

void StopAllPumpsCommand::abort() {
    // Nichts zu tun, da wir bereits alle stoppen
}

// DoseVolumeCommand Implementation
DoseVolumeCommand::DoseVolumeCommand(const String& cmd_id, ActuatorManager* manager) :
    BaseCommand(cmd_id, "dose_volume"),
    actuator_manager(manager),
    volume_ml(0) {
}

bool DoseVolumeCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    if (!getStringParam("pump_id", pump_id) || pump_id.length() == 0) {
        setError("Missing or invalid pump_id parameter");
        return false;
    }
    
    if (!getFloatParam("volume_ml", volume_ml) || volume_ml <= 0) {
        setError("Missing or invalid volume_ml parameter");
        return false;
    }
    
    if (!actuator_manager->canDose(pump_id, volume_ml)) {
        setError("Cannot dose " + String(volume_ml) + " ml with pump " + pump_id);
        return false;
    }
    
    return true;
}

bool DoseVolumeCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    if (actuator_manager->dose(pump_id, volume_ml)) {
        DynamicJsonDocument result(256);
        result["pump_id"] = pump_id;
        result["volume_ml"] = volume_ml;
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        return true;
    } else {
        setError("Failed to dose " + String(volume_ml) + " ml with pump " + pump_id);
        return false;
    }
}

void DoseVolumeCommand::abort() {
    actuator_manager->deactivateActuator(pump_id);
    setStatus(CommandStatus::FAILED);
}

// SchedulePumpCommand Implementation
SchedulePumpCommand::SchedulePumpCommand(const String& cmd_id, ActuatorManager* manager) :
    BaseCommand(cmd_id, "schedule_pump"),
    actuator_manager(manager),
    interval_minutes(0),
    duration_seconds(0) {
}

bool SchedulePumpCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    if (!getStringParam("pump_id", pump_id) || pump_id.length() == 0) {
        setError("Missing or invalid pump_id parameter");
        return false;
    }
    
    int interval_min, duration_sec;
    if (!getIntParam("interval_minutes", interval_min) || interval_min <= 0) {
        setError("Missing or invalid interval_minutes parameter");
        return false;
    }
    
    if (!getIntParam("duration_seconds", duration_sec) || duration_sec <= 0) {
        setError("Missing or invalid duration_seconds parameter");
        return false;
    }
    
    interval_minutes = interval_min;
    duration_seconds = duration_sec;
    
    if (!actuator_manager->getActuator(pump_id)) {
        setError("Pump " + pump_id + " not found");
        return false;
    }
    
    return true;
}

bool SchedulePumpCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    if (actuator_manager->setSchedule(pump_id, interval_minutes, duration_seconds)) {
        DynamicJsonDocument result(256);
        result["pump_id"] = pump_id;
        result["interval_minutes"] = interval_minutes;
        result["duration_seconds"] = duration_seconds;
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        return true;
    } else {
        setError("Failed to set schedule for pump " + pump_id);
        return false;
    }
}

void SchedulePumpCommand::abort() {
    // Schedule wird nicht gesetzt
}

// CancelScheduleCommand Implementation
CancelScheduleCommand::CancelScheduleCommand(const String& cmd_id, ActuatorManager* manager) :
    BaseCommand(cmd_id, "cancel_schedule"),
    actuator_manager(manager) {
}

bool CancelScheduleCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    if (!getStringParam("pump_id", pump_id) || pump_id.length() == 0) {
        setError("Missing or invalid pump_id parameter");
        return false;
    }
    
    if (!actuator_manager->getActuator(pump_id)) {
        setError("Pump " + pump_id + " not found");
        return false;
    }
    
    return true;
}

bool CancelScheduleCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    if (actuator_manager->cancelSchedule(pump_id)) {
        DynamicJsonDocument result(256);
        result["pump_id"] = pump_id;
        result["message"] = "Schedule cancelled";
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        return true;
    } else {
        setError("Failed to cancel schedule for pump " + pump_id);
        return false;
    }
}

void CancelScheduleCommand::abort() {
    // Nichts zu tun
} 