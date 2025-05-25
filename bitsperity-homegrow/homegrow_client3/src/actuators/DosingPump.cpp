#include "DosingPump.h"

DosingPump::DosingPump(const String& id) : 
    Pump(id, ActuatorType::DOSING_PUMP),
    max_dose_ml(50.0),
    last_dose_time(0),
    total_volume_dispensed_ml(0) {
}

bool DosingPump::init(const ActuatorConfig& actuator_config) {
    // Basis-Pumpen-Initialisierung
    if (!Pump::init(actuator_config)) {
        return false;
    }
    
    // Dosier-spezifische Konfiguration
    if (actuator_config.substance.length() > 0) {
        substance = actuator_config.substance;
    } else {
        substance = "Unknown";
    }
    
    if (actuator_config.concentration.length() > 0) {
        concentration = actuator_config.concentration;
    } else {
        concentration = "100%";
    }
    
    // Max-Dose basierend auf max_runtime und flow_rate berechnen
    max_dose_ml = flow_rate_ml_per_sec * config.max_runtime_sec;
    
    Logger::info("DosingPump " + actuator_id + " initialized:", "DosingPump");
    Logger::info("  Substance: " + substance, "DosingPump");
    Logger::info("  Concentration: " + concentration, "DosingPump");
    Logger::info("  Max dose: " + String(max_dose_ml) + " ml", "DosingPump");
    
    return true;
}

bool DosingPump::dose(float volume_ml) {
    if (!validateDoseRequest(volume_ml)) {
        return false;
    }
    
    Logger::info("Dosing " + String(volume_ml) + " ml of " + substance + 
                " with pump " + actuator_id, "DosingPump");
    
    // Basis-Pumpen-Dosierung verwenden
    if (Pump::dose(volume_ml)) {
        logDose(volume_ml);
        return true;
    }
    
    return false;
}

bool DosingPump::canDose(float volume_ml) const {
    return validateDoseRequest(volume_ml);
}

bool DosingPump::validateDoseRequest(float volume_ml) const {
    if (!initialized) {
        Logger::error("DosingPump " + actuator_id + " not initialized", "DosingPump");
        return false;
    }
    
    if (volume_ml <= 0) {
        Logger::error("DosingPump " + actuator_id + " invalid volume: " + String(volume_ml), "DosingPump");
        return false;
    }
    
    if (volume_ml > max_dose_ml) {
        Logger::error("DosingPump " + actuator_id + " volume " + String(volume_ml) + 
                     " ml exceeds max dose " + String(max_dose_ml) + " ml", "DosingPump");
        return false;
    }
    
    // Prüfe Cooldown
    if (isInCooldown()) {
        Logger::warn("DosingPump " + actuator_id + " in cooldown for " + 
                    String(getRemainingCooldown() / 1000) + "s", "DosingPump");
        return false;
    }
    
    // Prüfe ob bereits aktiv
    if (state == ActuatorState::ACTIVE) {
        Logger::warn("DosingPump " + actuator_id + " already active", "DosingPump");
        return false;
    }
    
    return true;
}

void DosingPump::logDose(float volume_ml) {
    total_volume_dispensed_ml += volume_ml;
    last_dose_time = millis();
    
    DynamicJsonDocument data(256);
    data["volume_ml"] = volume_ml;
    data["substance"] = substance;
    data["concentration"] = concentration;
    data["total_dispensed_ml"] = total_volume_dispensed_ml;
    
    Logger::logActuatorEvent(actuator_id, "dose_completed", data.as<JsonObject>());
}

DynamicJsonDocument DosingPump::getStatusJson() const {
    // Basis-Status von Pump holen
    DynamicJsonDocument doc = Pump::getStatusJson();
    
    // Dosier-spezifische Informationen hinzufügen
    JsonObject dosing = doc.createNestedObject("dosing");
    dosing["substance"] = substance;
    dosing["concentration"] = concentration;
    dosing["max_dose_ml"] = max_dose_ml;
    dosing["total_dispensed_ml"] = total_volume_dispensed_ml;
    
    if (last_dose_time > 0) {
        dosing["last_dose_time"] = last_dose_time;
        dosing["time_since_last_dose_ms"] = millis() - last_dose_time;
    }
    
    return doc;
} 