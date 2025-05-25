#include "Pump.h"

Pump::Pump(const String& id, ActuatorType pump_type) : 
    BaseActuator(id, pump_type),
    flow_rate_ml_per_sec(0),
    planned_duration_ms(0) {
}

bool Pump::init(const ActuatorConfig& actuator_config) {
    config = actuator_config;
    pin = config.pin;
    flow_rate_ml_per_sec = config.flow_rate_ml_per_sec;
    
    Logger::info("Initializing pump " + actuator_id + " on pin " + String(pin), "Pump");
    
    // Pin als Output konfigurieren
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW); // Sicherstellen dass Pumpe aus ist
    
    initialized = true;
    setState(ActuatorState::IDLE);
    
    Logger::info("Pump " + actuator_id + " initialized successfully", "Pump");
    Logger::info("Flow rate: " + String(flow_rate_ml_per_sec) + " ml/s", "Pump");
    
    return true;
}

bool Pump::activate(unsigned long duration_ms) {
    if (!validateActivationRequest(duration_ms)) {
        return false;
    }
    
    planned_duration_ms = duration_ms;
    
    Logger::info("Activating pump " + actuator_id + " for " + 
                String(duration_ms / 1000.0) + " seconds", "Pump");
    
    if (hardwareActivate()) {
        setState(ActuatorState::ACTIVE);
        logActivation(duration_ms);
        return true;
    } else {
        setState(ActuatorState::ERROR);
        last_error = "Hardware activation failed";
        return false;
    }
}

bool Pump::deactivate() {
    if (state != ActuatorState::ACTIVE) {
        Logger::warn("Pump " + actuator_id + " not active, cannot deactivate", "Pump");
        return false;
    }
    
    Logger::info("Deactivating pump " + actuator_id, "Pump");
    
    if (hardwareDeactivate()) {
        setState(ActuatorState::IDLE);
        logDeactivation();
        planned_duration_ms = 0;
        return true;
    } else {
        setState(ActuatorState::ERROR);
        last_error = "Hardware deactivation failed";
        return false;
    }
}

void Pump::loop() {
    // Prüfe ob automatische Deaktivierung nötig ist
    if (state == ActuatorState::ACTIVE) {
        checkAutoDeactivation();
    }
    
    // Cooldown-Status aktualisieren
    if (state == ActuatorState::IDLE && last_activation_end > 0) {
        if (isInCooldown() && state != ActuatorState::COOLDOWN) {
            setState(ActuatorState::COOLDOWN);
        } else if (!isInCooldown() && state == ActuatorState::COOLDOWN) {
            setState(ActuatorState::IDLE);
        }
    }
}

bool Pump::dose(float volume_ml) {
    if (flow_rate_ml_per_sec <= 0) {
        Logger::error("Pump " + actuator_id + " has invalid flow rate", "Pump");
        return false;
    }
    
    unsigned long duration_ms = calculateDurationForVolume(volume_ml);
    
    Logger::info("Dosing " + String(volume_ml) + " ml with pump " + actuator_id + 
                " (duration: " + String(duration_ms / 1000.0) + "s)", "Pump");
    
    return activate(duration_ms);
}

float Pump::calculateDurationForVolume(float volume_ml) const {
    if (flow_rate_ml_per_sec <= 0) {
        return 0;
    }
    
    // Dauer = Volumen / Flussrate
    float duration_sec = volume_ml / flow_rate_ml_per_sec;
    return duration_sec * 1000.0; // In Millisekunden
}

float Pump::calculateVolumeForDuration(unsigned long duration_ms) const {
    if (flow_rate_ml_per_sec <= 0) {
        return 0;
    }
    
    // Volumen = Flussrate * Zeit
    float duration_sec = duration_ms / 1000.0;
    return flow_rate_ml_per_sec * duration_sec;
}

bool Pump::hardwareActivate() {
    digitalWrite(pin, HIGH);
    Logger::debug("Pump " + actuator_id + " hardware ON (pin " + String(pin) + ")", "Pump");
    return true;
}

bool Pump::hardwareDeactivate() {
    digitalWrite(pin, LOW);
    Logger::debug("Pump " + actuator_id + " hardware OFF (pin " + String(pin) + ")", "Pump");
    return true;
}

void Pump::checkAutoDeactivation() {
    // Prüfe ob geplante Dauer erreicht wurde
    if (planned_duration_ms > 0) {
        unsigned long runtime_ms = millis() - activation_start_time;
        if (runtime_ms >= planned_duration_ms) {
            Logger::info("Pump " + actuator_id + " reached planned duration", "Pump");
            deactivate();
            return;
        }
    }
    
    // Prüfe ob maximale Laufzeit überschritten wurde
    if (hasExceededMaxRuntime()) {
        Logger::warn("Pump " + actuator_id + " exceeded max runtime!", "Pump");
        deactivate();
        setState(ActuatorState::ERROR);
        last_error = "Max runtime exceeded";
    }
} 