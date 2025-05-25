#include "WaterPump.h"

WaterPump::WaterPump() : 
    Pump("water_pump", ActuatorType::WATER_PUMP),
    scheduled_enabled(false),
    schedule_interval_ms(0),
    schedule_duration_ms(0),
    last_scheduled_activation(0) {
}

bool WaterPump::init(const ActuatorConfig& actuator_config) {
    // Basis-Pumpen-Initialisierung
    if (!Pump::init(actuator_config)) {
        return false;
    }
    
    // Schedule aus Konfiguration laden wenn vorhanden
    if (actuator_config.scheduled.size() > 0) {
        bool enabled = actuator_config.scheduled["enabled"] | false;
        
        if (enabled) {
            unsigned long interval_min = actuator_config.scheduled["interval_minutes"] | 30;
            unsigned long duration_sec = actuator_config.scheduled["duration_seconds"] | 120;
            
            setSchedule(interval_min, duration_sec);
        }
    }
    
    Logger::info("WaterPump initialized successfully", "WaterPump");
    if (scheduled_enabled) {
        Logger::info("Schedule: every " + String(schedule_interval_ms / 60000) + 
                    " min for " + String(schedule_duration_ms / 1000) + " sec", "WaterPump");
    }
    
    return true;
}

void WaterPump::loop() {
    // Basis-Pumpen-Loop
    Pump::loop();
    
    // Prüfe geplante Aktivierung
    if (scheduled_enabled) {
        checkScheduledActivation();
    }
}

bool WaterPump::setSchedule(unsigned long interval_minutes, unsigned long duration_seconds) {
    if (interval_minutes == 0 || duration_seconds == 0) {
        Logger::error("Invalid schedule parameters", "WaterPump");
        return false;
    }
    
    schedule_interval_ms = interval_minutes * 60000UL;
    schedule_duration_ms = duration_seconds * 1000UL;
    scheduled_enabled = true;
    last_scheduled_activation = 0; // Reset für sofortige erste Aktivierung
    
    Logger::info("WaterPump schedule set: every " + String(interval_minutes) + 
                " min for " + String(duration_seconds) + " sec", "WaterPump");
    
    return true;
}

bool WaterPump::cancelSchedule() {
    scheduled_enabled = false;
    schedule_interval_ms = 0;
    schedule_duration_ms = 0;
    last_scheduled_activation = 0;
    
    Logger::info("WaterPump schedule cancelled", "WaterPump");
    return true;
}

void WaterPump::checkScheduledActivation() {
    if (!scheduled_enabled || state == ActuatorState::ACTIVE) {
        return;
    }
    
    if (shouldActivateScheduled()) {
        Logger::info("WaterPump scheduled activation triggered", "WaterPump");
        
        if (activate(schedule_duration_ms)) {
            last_scheduled_activation = millis();
        } else {
            Logger::warn("WaterPump scheduled activation failed", "WaterPump");
        }
    }
}

bool WaterPump::shouldActivateScheduled() const {
    if (!scheduled_enabled) {
        return false;
    }
    
    // Erste Aktivierung oder Intervall erreicht
    if (last_scheduled_activation == 0) {
        return true;
    }
    
    unsigned long time_since_last = millis() - last_scheduled_activation;
    return time_since_last >= schedule_interval_ms;
}

DynamicJsonDocument WaterPump::getStatusJson() const {
    // Basis-Status von Pump holen
    DynamicJsonDocument doc = Pump::getStatusJson();
    
    // Schedule-Informationen hinzufügen
    JsonObject schedule = doc.createNestedObject("schedule");
    schedule["enabled"] = scheduled_enabled;
    
    if (scheduled_enabled) {
        schedule["interval_minutes"] = schedule_interval_ms / 60000;
        schedule["duration_seconds"] = schedule_duration_ms / 1000;
        
        if (last_scheduled_activation > 0) {
            schedule["last_activation"] = last_scheduled_activation;
            schedule["time_since_last_ms"] = millis() - last_scheduled_activation;
            schedule["next_activation_in_ms"] = schedule_interval_ms - (millis() - last_scheduled_activation);
        } else {
            schedule["next_activation_in_ms"] = 0; // Sofort
        }
    }
    
    return doc;
} 