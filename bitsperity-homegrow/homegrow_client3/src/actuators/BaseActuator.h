#ifndef BASE_ACTUATOR_H
#define BASE_ACTUATOR_H

#include "../core/Types.h"
#include "../config/Config.h"
#include "../core/Logger.h"

class BaseActuator {
protected:
    String actuator_id;
    ActuatorType type;
    ActuatorConfig config;
    ActuatorState state;
    
    unsigned long activation_start_time;
    unsigned long last_activation_end;
    unsigned long total_runtime_ms;
    unsigned long activation_count;
    
    bool initialized;
    String last_error;
    int pin;
    
public:
    BaseActuator(const String& id, ActuatorType actuator_type);
    virtual ~BaseActuator() = default;
    
    virtual bool init(const ActuatorConfig& actuator_config) = 0;
    virtual bool activate(unsigned long duration_ms) = 0;
    virtual bool deactivate() = 0;
    virtual void loop() = 0;
    
    // Status-Abfragen
    bool isActive() const { return state == ActuatorState::ACTIVE; }
    bool canActivate() const;
    ActuatorState getState() const { return state; }
    String getId() const { return actuator_id; }
    ActuatorType getType() const { return type; }
    int getPin() const { return pin; }
    
    // Sicherheitsprüfungen
    bool isInCooldown() const;
    unsigned long getRemainingCooldown() const;
    bool hasExceededMaxRuntime() const;
    
    // Statistiken
    unsigned long getTotalRuntimeMs() const { return total_runtime_ms; }
    unsigned long getActivationCount() const { return activation_count; }
    float getRuntimeHours() const { return total_runtime_ms / 3600000.0; }
    
    // Status für Monitoring
    virtual DynamicJsonDocument getStatusJson() const;
    virtual bool isHealthy() const;
    
protected:
    virtual bool hardwareActivate() = 0;
    virtual bool hardwareDeactivate() = 0;
    
    void setState(ActuatorState new_state);
    void logActivation(unsigned long duration_ms);
    void logDeactivation();
    bool validateActivationRequest(unsigned long duration_ms) const;
};

#endif // BASE_ACTUATOR_H 