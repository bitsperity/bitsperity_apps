#include "DosingCommand.h"
#include <vector>

// AdjustPHByCommand Implementation
AdjustPHByCommand::AdjustPHByCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr) :
    BaseCommand(cmd_id, "adjust_ph_by"),
    actuator_manager(actuator_mgr),
    sensor_manager(sensor_mgr),
    delta_ph(0),
    max_volume_ml(10.0) {
}

bool AdjustPHByCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    if (!getFloatParam("delta_ph", delta_ph)) {
        setError("Missing or invalid delta_ph parameter");
        return false;
    }
    
    if (abs(delta_ph) > 2.0) {
        setError("Delta pH too large: " + String(delta_ph) + " (max ±2.0)");
        return false;
    }
    
    // Optional max_volume parameter
    getFloatParam("max_volume_ml", max_volume_ml);
    
    return true;
}

bool AdjustPHByCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    float current_ph = getCurrentPH();
    if (current_ph < 0) {
        setError("Cannot read current pH value");
        return false;
    }
    
    String pump_id = selectPHPump(delta_ph);
    if (pump_id.length() == 0) {
        setError("No suitable pH pump found for delta: " + String(delta_ph));
        return false;
    }
    
    float required_volume = calculateRequiredVolume(current_ph, delta_ph);
    if (required_volume > max_volume_ml) {
        setError("Required volume " + String(required_volume) + " ml exceeds max " + String(max_volume_ml) + " ml");
        return false;
    }
    
    Logger::info("Adjusting pH by " + String(delta_ph) + " using " + String(required_volume) + " ml of " + pump_id, "AdjustPHByCommand");
    
    if (actuator_manager->dose(pump_id, required_volume)) {
        DynamicJsonDocument result(256);
        result["current_ph"] = current_ph;
        result["delta_ph"] = delta_ph;
        result["pump_id"] = pump_id;
        result["volume_ml"] = required_volume;
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        return true;
    } else {
        setError("Failed to dose " + String(required_volume) + " ml with pump " + pump_id);
        return false;
    }
}

void AdjustPHByCommand::abort() {
    // Dosierung kann nicht abgebrochen werden, da sie sofort ausgeführt wird
}

float AdjustPHByCommand::getCurrentPH() const {
    BaseSensor* ph_sensor = sensor_manager->getSensor(SensorType::PH);
    if (!ph_sensor) {
        return -1;
    }
    
    const SensorReading& reading = ph_sensor->getLastReading();
    return reading.filtered;
}

String AdjustPHByCommand::selectPHPump(float delta_ph) const {
    if (delta_ph < 0) {
        return "ph_down";  // pH senken
    } else if (delta_ph > 0) {
        return "ph_up";    // pH erhöhen
    }
    return "";
}

float AdjustPHByCommand::calculateRequiredVolume(float current_ph, float delta_ph) const {
    // Vereinfachte Berechnung: 1 ml pro 0.1 pH-Einheit
    // In der Realität würde dies von der Pufferstärke der Lösung abhängen
    float volume = abs(delta_ph) * 10.0;
    
    // Minimum 0.5 ml, Maximum basierend auf max_volume_ml
    volume = max(0.5f, min(volume, max_volume_ml));
    
    return volume;
}

// SetPHTargetCommand Implementation
SetPHTargetCommand::SetPHTargetCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr) :
    BaseCommand(cmd_id, "set_ph_target"),
    actuator_manager(actuator_mgr),
    sensor_manager(sensor_mgr),
    target_ph(6.5),
    tolerance(0.1),
    max_attempts(3) {
}

bool SetPHTargetCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    if (!getFloatParam("target_ph", target_ph)) {
        setError("Missing or invalid target_ph parameter");
        return false;
    }
    
    if (target_ph < 4.0 || target_ph > 8.5) {
        setError("Target pH out of safe range: " + String(target_ph) + " (4.0-8.5)");
        return false;
    }
    
    // Optional parameters
    getFloatParam("tolerance", tolerance);
    getIntParam("max_attempts", max_attempts);
    
    return true;
}

bool SetPHTargetCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    if (adjustPHToTarget()) {
        DynamicJsonDocument result(256);
        result["target_ph"] = target_ph;
        result["final_ph"] = getCurrentPH();
        result["tolerance"] = tolerance;
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        return true;
    } else {
        setError("Failed to reach target pH after " + String(max_attempts) + " attempts");
        return false;
    }
}

void SetPHTargetCommand::abort() {
    // Kann nicht abgebrochen werden
}

bool SetPHTargetCommand::adjustPHToTarget() {
    for (int attempt = 0; attempt < max_attempts; attempt++) {
        float current_ph = getCurrentPH();
        if (current_ph < 0) {
            return false;
        }
        
        float delta = target_ph - current_ph;
        if (abs(delta) <= tolerance) {
            Logger::info("pH target reached: " + String(current_ph), "SetPHTargetCommand");
            return true;
        }
        
        // Erstelle AdjustPHByCommand für diese Anpassung
        String sub_command_id = command_id + "_adjust_" + String(attempt);
        AdjustPHByCommand adjust_command(sub_command_id, actuator_manager, sensor_manager);
        
        DynamicJsonDocument adjust_params(256);
        adjust_params["delta_ph"] = delta * 0.5; // Vorsichtige Anpassung
        adjust_params["max_volume_ml"] = 5.0;    // Kleinere Dosen
        
        if (!adjust_command.validate(adjust_params.as<JsonObject>()) || !adjust_command.execute()) {
            Logger::error("pH adjustment failed on attempt " + String(attempt + 1), "SetPHTargetCommand");
            return false;
        }
        
        // Warte 30 Sekunden für Stabilisierung
        delay(30000);
    }
    
    return false;
}

float SetPHTargetCommand::getCurrentPH() const {
    BaseSensor* ph_sensor = sensor_manager->getSensor(SensorType::PH);
    if (!ph_sensor) {
        return -1;
    }
    
    const SensorReading& reading = ph_sensor->getLastReading();
    return reading.filtered;
}

// AdjustTDSByCommand Implementation
AdjustTDSByCommand::AdjustTDSByCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr) :
    BaseCommand(cmd_id, "adjust_tds_by"),
    actuator_manager(actuator_mgr),
    sensor_manager(sensor_mgr),
    delta_tds(0),
    max_volume_ml(20.0) {
}

bool AdjustTDSByCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    if (!getFloatParam("delta_tds", delta_tds)) {
        setError("Missing or invalid delta_tds parameter");
        return false;
    }
    
    if (delta_tds < 0) {
        setError("Cannot reduce TDS (delta_tds must be positive)");
        return false;
    }
    
    if (delta_tds > 500) {
        setError("Delta TDS too large: " + String(delta_tds) + " (max 500)");
        return false;
    }
    
    // Optional max_volume parameter
    getFloatParam("max_volume_ml", max_volume_ml);
    
    return true;
}

bool AdjustTDSByCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    float current_tds = getCurrentTDS();
    if (current_tds < 0) {
        setError("Cannot read current TDS value");
        return false;
    }
    
    std::vector<String> pumps = selectNutrientPumps();
    if (pumps.empty()) {
        setError("No nutrient pumps available");
        return false;
    }
    
    float total_volume = calculateRequiredVolume(current_tds, delta_tds);
    float volume_per_pump = total_volume / pumps.size();
    
    if (total_volume > max_volume_ml) {
        setError("Required volume " + String(total_volume) + " ml exceeds max " + String(max_volume_ml) + " ml");
        return false;
    }
    
    Logger::info("Adjusting TDS by " + String(delta_tds) + " using " + String(total_volume) + " ml total", "AdjustTDSByCommand");
    
    bool all_success = true;
    for (const String& pump_id : pumps) {
        if (!actuator_manager->dose(pump_id, volume_per_pump)) {
            Logger::error("Failed to dose with pump " + pump_id, "AdjustTDSByCommand");
            all_success = false;
        }
    }
    
    if (all_success) {
        DynamicJsonDocument result(256);
        result["current_tds"] = current_tds;
        result["delta_tds"] = delta_tds;
        result["total_volume_ml"] = total_volume;
        result["pumps_used"] = pumps.size();
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        return true;
    } else {
        setError("Failed to dose with one or more nutrient pumps");
        return false;
    }
}

void AdjustTDSByCommand::abort() {
    // Dosierung kann nicht abgebrochen werden
}

float AdjustTDSByCommand::getCurrentTDS() const {
    BaseSensor* tds_sensor = sensor_manager->getSensor(SensorType::TDS);
    if (!tds_sensor) {
        return -1;
    }
    
    const SensorReading& reading = tds_sensor->getLastReading();
    return reading.filtered;
}

std::vector<String> AdjustTDSByCommand::selectNutrientPumps() const {
    std::vector<String> pumps;
    
    // Prüfe verfügbare Nährstoffpumpen
    if (actuator_manager->getDosingPump("nutrient_a")) {
        pumps.push_back("nutrient_a");
    }
    if (actuator_manager->getDosingPump("nutrient_b")) {
        pumps.push_back("nutrient_b");
    }
    if (actuator_manager->getDosingPump("cal_mag")) {
        pumps.push_back("cal_mag");
    }
    
    return pumps;
}

float AdjustTDSByCommand::calculateRequiredVolume(float current_tds, float delta_tds) const {
    // Vereinfachte Berechnung: 1 ml pro 50 TDS-Einheiten
    // In der Realität würde dies von der Nährstoffkonzentration abhängen
    float volume = delta_tds / 50.0;
    
    // Minimum 1 ml, Maximum basierend auf max_volume_ml
    volume = max(1.0f, min(volume, max_volume_ml));
    
    return volume;
}

// SetTDSTargetCommand Implementation
SetTDSTargetCommand::SetTDSTargetCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr) :
    BaseCommand(cmd_id, "set_tds_target"),
    actuator_manager(actuator_mgr),
    sensor_manager(sensor_mgr),
    target_tds(600),
    tolerance(50),
    max_attempts(3) {
}

bool SetTDSTargetCommand::validate(const JsonObject& parameters) {
    params.set(parameters);
    
    if (!getFloatParam("target_tds", target_tds)) {
        setError("Missing or invalid target_tds parameter");
        return false;
    }
    
    if (target_tds < 100 || target_tds > 2000) {
        setError("Target TDS out of safe range: " + String(target_tds) + " (100-2000)");
        return false;
    }
    
    // Optional parameters
    getFloatParam("tolerance", tolerance);
    getIntParam("max_attempts", max_attempts);
    
    return true;
}

bool SetTDSTargetCommand::execute() {
    setStatus(CommandStatus::EXECUTING);
    
    if (adjustTDSToTarget()) {
        DynamicJsonDocument result(256);
        result["target_tds"] = target_tds;
        result["final_tds"] = getCurrentTDS();
        result["tolerance"] = tolerance;
        setResultData(result.as<JsonObject>());
        setStatus(CommandStatus::COMPLETED);
        return true;
    } else {
        setError("Failed to reach target TDS after " + String(max_attempts) + " attempts");
        return false;
    }
}

void SetTDSTargetCommand::abort() {
    // Kann nicht abgebrochen werden
}

bool SetTDSTargetCommand::adjustTDSToTarget() {
    for (int attempt = 0; attempt < max_attempts; attempt++) {
        float current_tds = getCurrentTDS();
        if (current_tds < 0) {
            return false;
        }
        
        float delta = target_tds - current_tds;
        if (abs(delta) <= tolerance) {
            Logger::info("TDS target reached: " + String(current_tds), "SetTDSTargetCommand");
            return true;
        }
        
        if (delta <= 0) {
            Logger::warn("TDS already at or above target, cannot reduce", "SetTDSTargetCommand");
            return true; // Kann TDS nicht reduzieren
        }
        
        // Erstelle AdjustTDSByCommand für diese Anpassung
        String sub_command_id = command_id + "_adjust_" + String(attempt);
        AdjustTDSByCommand adjust_command(sub_command_id, actuator_manager, sensor_manager);
        
        DynamicJsonDocument adjust_params(256);
        adjust_params["delta_tds"] = delta * 0.5; // Vorsichtige Anpassung
        adjust_params["max_volume_ml"] = 10.0;    // Kleinere Dosen
        
        if (!adjust_command.validate(adjust_params.as<JsonObject>()) || !adjust_command.execute()) {
            Logger::error("TDS adjustment failed on attempt " + String(attempt + 1), "SetTDSTargetCommand");
            return false;
        }
        
        // Warte 60 Sekunden für Stabilisierung
        delay(60000);
    }
    
    return false;
}

float SetTDSTargetCommand::getCurrentTDS() const {
    BaseSensor* tds_sensor = sensor_manager->getSensor(SensorType::TDS);
    if (!tds_sensor) {
        return -1;
    }
    
    const SensorReading& reading = tds_sensor->getLastReading();
    return reading.filtered;
} 