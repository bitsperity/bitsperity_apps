#include "BaseState.h"

BaseState::BaseState(Application* application, SystemState type) : 
    app(application), 
    state_type(type),
    enter_time(0) {
}

unsigned long BaseState::getUptime() const {
    return millis() - enter_time;
}

DynamicJsonDocument BaseState::getStatusJson() const {
    DynamicJsonDocument doc(256);
    
    doc["state"] = static_cast<int>(state_type);
    doc["state_name"] = getStateName(state_type);
    doc["uptime_ms"] = getUptime();
    doc["enter_time"] = enter_time;
    
    return doc;
}

void BaseState::logStateEvent(const String& event, const String& message) {
    String log_msg = "[" + getStateName(state_type) + "] " + event;
    if (!message.isEmpty()) {
        log_msg += ": " + message;
    }
    Logger::info(log_msg, "State");
}

bool BaseState::shouldTimeout(unsigned long timeout_ms) const {
    return getUptime() > timeout_ms;
}

// Hilfsfunktion für State-Namen
String BaseState::getStateName(SystemState state) {
    switch (state) {
        case SystemState::INIT: return "INIT";
        case SystemState::CONNECTING_WIFI: return "CONNECTING_WIFI";
        case SystemState::DISCOVERING_BROKER: return "DISCOVERING_BROKER";
        case SystemState::CONNECTING_MQTT: return "CONNECTING_MQTT";
        case SystemState::CONFIG_REQUEST: return "CONFIG_REQUEST";
        case SystemState::RUNNING: return "RUNNING";
        case SystemState::ERROR: return "ERROR";
        case SystemState::EMERGENCY_STOP: return "EMERGENCY_STOP";
        default: return "UNKNOWN";
    }
} 