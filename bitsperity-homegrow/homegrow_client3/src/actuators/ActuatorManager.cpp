#include "ActuatorManager.h"

ActuatorManager::ActuatorManager() :
    emergency_stop_active(false),
    initialized(false) {
}

bool ActuatorManager::init(const Config& config) {
    // Alle Aktoren initialisieren
    initializeActuators(config);
    
    initialized = true;
    
    Logger::info("ActuatorManager initialized with " + String(actuators.size()) + " actuators", "ActuatorManager");
    
    return true;
}

void ActuatorManager::loop() {
    if (!initialized) {
        return;
    }
    
    // Alle Aktoren aktualisieren
    for (auto& pair : actuators) {
        pair.second->loop();
    }
}

bool ActuatorManager::addActuator(std::unique_ptr<BaseActuator> actuator) {
    if (!actuator) {
        Logger::error("Cannot add null actuator", "ActuatorManager");
        return false;
    }
    
    String id = actuator->getId();
    
    // Prüfe ob Aktor bereits existiert
    if (actuators.find(id) != actuators.end()) {
        Logger::warn("Actuator " + id + " already exists, replacing", "ActuatorManager");
    }
    
    actuators[id] = std::move(actuator);
    Logger::info("Actuator " + id + " added successfully", "ActuatorManager");
    
    return true;
}

BaseActuator* ActuatorManager::getActuator(const String& actuator_id) {
    auto it = actuators.find(actuator_id);
    if (it != actuators.end()) {
        return it->second.get();
    }
    
    return nullptr;
}

DosingPump* ActuatorManager::getDosingPump(const String& pump_id) {
    BaseActuator* actuator = getActuator(pump_id);
    if (actuator && actuator->getType() == ActuatorType::DOSING_PUMP) {
        return static_cast<DosingPump*>(actuator);
    }
    
    return nullptr;
}

bool ActuatorManager::activateActuator(const String& actuator_id, unsigned long duration_ms) {
    if (!validateActuatorOperation(actuator_id)) {
        return false;
    }
    
    BaseActuator* actuator = getActuator(actuator_id);
    if (!actuator) {
        Logger::error("Actuator " + actuator_id + " not found", "ActuatorManager");
        return false;
    }
    
    Logger::info("Activating actuator " + actuator_id + " for " + String(duration_ms) + " ms", "ActuatorManager");
    
    return actuator->activate(duration_ms);
}

bool ActuatorManager::deactivateActuator(const String& actuator_id) {
    BaseActuator* actuator = getActuator(actuator_id);
    if (!actuator) {
        Logger::error("Actuator " + actuator_id + " not found", "ActuatorManager");
        return false;
    }
    
    Logger::info("Deactivating actuator " + actuator_id, "ActuatorManager");
    
    return actuator->deactivate();
}

bool ActuatorManager::stopAllActuators() {
    Logger::info("Stopping all actuators", "ActuatorManager");
    
    bool all_stopped = true;
    
    for (auto& pair : actuators) {
        if (pair.second->isActive()) {
            if (!pair.second->deactivate()) {
                Logger::error("Failed to stop actuator " + pair.first, "ActuatorManager");
                all_stopped = false;
            }
        }
    }
    
    return all_stopped;
}

bool ActuatorManager::dose(const String& pump_id, float volume_ml) {
    if (!validateActuatorOperation(pump_id)) {
        return false;
    }
    
    DosingPump* pump = getDosingPump(pump_id);
    if (!pump) {
        Logger::error("Dosing pump " + pump_id + " not found", "ActuatorManager");
        return false;
    }
    
    Logger::info("Dosing " + String(volume_ml) + " ml with pump " + pump_id, "ActuatorManager");
    
    return pump->dose(volume_ml);
}

bool ActuatorManager::canDose(const String& pump_id, float volume_ml) const {
    DosingPump* pump = const_cast<ActuatorManager*>(this)->getDosingPump(pump_id);
    if (!pump) {
        return false;
    }
    
    return pump->canDose(volume_ml);
}

bool ActuatorManager::setSchedule(const String& actuator_id, unsigned long interval_minutes, unsigned long duration_seconds) {
    BaseActuator* actuator = getActuator(actuator_id);
    if (!actuator) {
        Logger::error("Actuator " + actuator_id + " not found for scheduling", "ActuatorManager");
        return false;
    }
    
    // Prüfe ob es eine WaterPump oder AirPump ist
    if (actuator->getType() == ActuatorType::WATER_PUMP) {
        WaterPump* water_pump = static_cast<WaterPump*>(actuator);
        return water_pump->setSchedule(interval_minutes, duration_seconds);
    } else if (actuator->getType() == ActuatorType::AIR_PUMP) {
        AirPump* air_pump = static_cast<AirPump*>(actuator);
        return air_pump->setSchedule(interval_minutes, duration_seconds);
    } else {
        Logger::error("Actuator " + actuator_id + " does not support scheduling", "ActuatorManager");
        return false;
    }
}

bool ActuatorManager::cancelSchedule(const String& actuator_id) {
    BaseActuator* actuator = getActuator(actuator_id);
    if (!actuator) {
        Logger::error("Actuator " + actuator_id + " not found for schedule cancellation", "ActuatorManager");
        return false;
    }
    
    // Prüfe ob es eine WaterPump oder AirPump ist
    if (actuator->getType() == ActuatorType::WATER_PUMP) {
        WaterPump* water_pump = static_cast<WaterPump*>(actuator);
        return water_pump->cancelSchedule();
    } else if (actuator->getType() == ActuatorType::AIR_PUMP) {
        AirPump* air_pump = static_cast<AirPump*>(actuator);
        return air_pump->cancelSchedule();
    } else {
        Logger::error("Actuator " + actuator_id + " does not support scheduling", "ActuatorManager");
        return false;
    }
}

void ActuatorManager::emergencyStop(const String& reason) {
    Logger::error("EMERGENCY STOP: " + reason, "ActuatorManager");
    
    emergency_stop_active = true;
    emergency_stop_reason = reason;
    
    // Alle Aktoren sofort stoppen
    stopAllActuators();
}

void ActuatorManager::clearEmergencyStop() {
    if (emergency_stop_active) {
        Logger::info("Emergency stop cleared", "ActuatorManager");
        emergency_stop_active = false;
        emergency_stop_reason = "";
    }
}

DynamicJsonDocument ActuatorManager::getStatusJson() const {
    DynamicJsonDocument doc(2048);
    
    doc["initialized"] = initialized;
    doc["actuator_count"] = actuators.size();
    doc["all_healthy"] = areAllActuatorsHealthy();
    doc["emergency_stop_active"] = emergency_stop_active;
    
    if (emergency_stop_active) {
        doc["emergency_stop_reason"] = emergency_stop_reason;
    }
    
    JsonArray actuator_array = doc.createNestedArray("actuators");
    
    for (const auto& pair : actuators) {
        JsonObject actuator_obj = actuator_array.createNestedObject();
        actuator_obj["id"] = pair.first;
        actuator_obj["type"] = (int)pair.second->getType();
        actuator_obj["state"] = (int)pair.second->getState();
        actuator_obj["healthy"] = pair.second->isHealthy();
        actuator_obj["runtime_hours"] = pair.second->getRuntimeHours();
        actuator_obj["activation_count"] = pair.second->getActivationCount();
        
        if (pair.second->isInCooldown()) {
            actuator_obj["cooldown_remaining_ms"] = pair.second->getRemainingCooldown();
        }
    }
    
    return doc;
}

bool ActuatorManager::areAllActuatorsHealthy() const {
    for (const auto& pair : actuators) {
        if (!pair.second->isHealthy()) {
            return false;
        }
    }
    
    return true;
}

bool ActuatorManager::validateActuatorOperation(const String& actuator_id) const {
    if (emergency_stop_active) {
        Logger::error("Emergency stop active, operation denied for " + actuator_id, "ActuatorManager");
        return false;
    }
    
    if (!initialized) {
        Logger::error("ActuatorManager not initialized", "ActuatorManager");
        return false;
    }
    
    return true;
}

void ActuatorManager::initializeActuators(const Config& config) {
    // Wasserpumpe initialisieren
    if (config.water_pump.enabled) {
        std::unique_ptr<WaterPump> water_pump(new WaterPump());
        if (water_pump->init(config.water_pump)) {
            addActuator(std::move(water_pump));
        } else {
            Logger::error("Failed to initialize water pump", "ActuatorManager");
        }
    }
    
    // Luftpumpe initialisieren
    if (config.air_pump.enabled) {
        std::unique_ptr<AirPump> air_pump(new AirPump());
        if (air_pump->init(config.air_pump)) {
            addActuator(std::move(air_pump));
        } else {
            Logger::error("Failed to initialize air pump", "ActuatorManager");
        }
    }
    
    // Dosierpumpen initialisieren
    createDosingPumps(config);
}

void ActuatorManager::createDosingPumps(const Config& config) {
    // Standard Dosierpumpen-IDs
    String pump_ids[] = {"ph_down", "ph_up", "nutrient_a", "nutrient_b", "cal_mag"};
    
    for (int i = 0; i < 5; i++) {
        if (config.dosing_pumps[i].enabled) {
            std::unique_ptr<DosingPump> dosing_pump(new DosingPump(pump_ids[i]));
            if (dosing_pump->init(config.dosing_pumps[i])) {
                addActuator(std::move(dosing_pump));
            } else {
                Logger::error("Failed to initialize dosing pump " + pump_ids[i], "ActuatorManager");
            }
        }
    }
} 