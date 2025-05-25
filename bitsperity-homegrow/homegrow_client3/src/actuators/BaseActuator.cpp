#include "BaseActuator.h"

BaseActuator::BaseActuator(const String& id, ActuatorType actuator_type) :
    actuator_id(id),
    type(actuator_type),
    state(ActuatorState::IDLE),
    activation_start_time(0),
    last_activation_end(0),
    total_runtime_ms(0),
    activation_count(0),
    initialized(false),
    pin(-1) {
}

bool BaseActuator::canActivate() const {
    if (!initialized) {
        return false;
    }
    
    if (state != ActuatorState::IDLE) {
        return false;
    }
    
    if (isInCooldown()) {
        return false;
    }
    
    return true;
}

bool BaseActuator::isInCooldown() const {
    if (last_activation_end == 0) {
        return false; // Noch nie aktiviert
    }
    
    unsigned long cooldown_ms = config.cooldown_sec * 1000UL;
    return (millis() - last_activation_end) < cooldown_ms;
}

unsigned long BaseActuator::getRemainingCooldown() const {
    if (!isInCooldown()) {
        return 0;
    }
    
    unsigned long cooldown_ms = config.cooldown_sec * 1000UL;
    unsigned long elapsed = millis() - last_activation_end;
    return cooldown_ms - elapsed;
}

bool BaseActuator::hasExceededMaxRuntime() const {
    if (state != ActuatorState::ACTIVE) {
        return false;
    }
    
    unsigned long runtime_ms = millis() - activation_start_time;
    unsigned long max_runtime_ms = config.max_runtime_sec * 1000UL;
    
    return runtime_ms > max_runtime_ms;
}

void BaseActuator::setState(ActuatorState new_state) {
    if (state != new_state) {
        Logger::debug(actuator_id + " state change: " + 
                     String(static_cast<int>(state)) + " -> " + 
                     String(static_cast<int>(new_state)), "Actuator");
        state = new_state;
    }
}

void BaseActuator::logActivation(unsigned long duration_ms) {
    activation_start_time = millis();
    activation_count++;
    
    DynamicJsonDocument data(128);
    data["duration_ms"] = duration_ms;
    data["activation_count"] = activation_count;
    
    Logger::logActuatorEvent(actuator_id, "activated", data.as<JsonObject>());
}

void BaseActuator::logDeactivation() {
    if (activation_start_time > 0) {
        unsigned long runtime_ms = millis() - activation_start_time;
        total_runtime_ms += runtime_ms;
        last_activation_end = millis();
        
        DynamicJsonDocument data(128);
        data["runtime_ms"] = runtime_ms;
        data["total_runtime_ms"] = total_runtime_ms;
        
        Logger::logActuatorEvent(actuator_id, "deactivated", data.as<JsonObject>());
    }
    
    activation_start_time = 0;
}

bool BaseActuator::validateActivationRequest(unsigned long duration_ms) const {
    if (!initialized) {
        Logger::error(actuator_id + " not initialized", "Actuator");
        return false;
    }
    
    if (!config.enabled) {
        Logger::warn(actuator_id + " is disabled", "Actuator");
        return false;
    }
    
    if (state == ActuatorState::ACTIVE) {
        Logger::warn(actuator_id + " already active", "Actuator");
        return false;
    }
    
    if (isInCooldown()) {
        Logger::warn(actuator_id + " in cooldown for " + 
                    String(getRemainingCooldown() / 1000) + "s", "Actuator");
        return false;
    }
    
    unsigned long max_duration_ms = config.max_runtime_sec * 1000UL;
    if (duration_ms > max_duration_ms) {
        Logger::warn(actuator_id + " requested duration " + String(duration_ms) + 
                    "ms exceeds max " + String(max_duration_ms) + "ms", "Actuator");
        return false;
    }
    
    return true;
}

DynamicJsonDocument BaseActuator::getStatusJson() const {
    DynamicJsonDocument doc(512);
    
    doc["id"] = actuator_id;
    doc["type"] = static_cast<int>(type);
    doc["state"] = static_cast<int>(state);
    doc["state_name"] = state == ActuatorState::IDLE ? "idle" :
                       state == ActuatorState::ACTIVE ? "active" :
                       state == ActuatorState::COOLDOWN ? "cooldown" :
                       state == ActuatorState::ERROR ? "error" : "disabled";
    doc["initialized"] = initialized;
    doc["enabled"] = config.enabled;
    doc["pin"] = pin;
    
    // Runtime-Informationen
    JsonObject runtime = doc.createNestedObject("runtime");
    runtime["total_ms"] = total_runtime_ms;
    runtime["total_hours"] = getRuntimeHours();
    runtime["activation_count"] = activation_count;
    
    if (state == ActuatorState::ACTIVE && activation_start_time > 0) {
        runtime["current_runtime_ms"] = millis() - activation_start_time;
    }
    
    // Cooldown-Informationen
    if (isInCooldown()) {
        JsonObject cooldown = doc.createNestedObject("cooldown");
        cooldown["active"] = true;
        cooldown["remaining_ms"] = getRemainingCooldown();
        cooldown["remaining_sec"] = getRemainingCooldown() / 1000;
    }
    
    // Konfiguration
    JsonObject conf = doc.createNestedObject("config");
    conf["max_runtime_sec"] = config.max_runtime_sec;
    conf["cooldown_sec"] = config.cooldown_sec;
    
    // Letzter Fehler
    if (!last_error.isEmpty()) {
        doc["last_error"] = last_error;
    }
    
    return doc;
}

bool BaseActuator::isHealthy() const {
    if (!initialized) return false;
    if (state == ActuatorState::ERROR) return false;
    if (!config.enabled) return false;
    
    // Prüfe ob zu lange aktiv
    if (state == ActuatorState::ACTIVE && hasExceededMaxRuntime()) {
        return false;
    }
    
    return true;
} 