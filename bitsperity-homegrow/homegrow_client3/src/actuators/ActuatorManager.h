#ifndef ACTUATOR_MANAGER_H
#define ACTUATOR_MANAGER_H

#include "BaseActuator.h"
#include "WaterPump.h"
#include "AirPump.h"
#include "DosingPump.h"
#include "../config/Config.h"
#include <map>
#include <memory>

class ActuatorManager {
private:
    std::map<String, std::unique_ptr<BaseActuator>> actuators;
    bool emergency_stop_active;
    String emergency_stop_reason;
    bool initialized;
    
public:
    ActuatorManager();
    
    bool init(const Config& config);
    void loop();
    
    // Aktor-Management
    bool addActuator(std::unique_ptr<BaseActuator> actuator);
    BaseActuator* getActuator(const String& actuator_id);
    DosingPump* getDosingPump(const String& pump_id);
    
    // Basis-Operationen
    bool activateActuator(const String& actuator_id, unsigned long duration_ms);
    bool deactivateActuator(const String& actuator_id);
    bool stopAllActuators();
    
    // Dosier-Operationen
    bool dose(const String& pump_id, float volume_ml);
    bool canDose(const String& pump_id, float volume_ml) const;
    
    // Scheduling
    bool setSchedule(const String& actuator_id, unsigned long interval_minutes, unsigned long duration_seconds);
    bool cancelSchedule(const String& actuator_id);
    
    // Emergency Stop
    void emergencyStop(const String& reason);
    void clearEmergencyStop();
    bool isEmergencyStopActive() const { return emergency_stop_active; }
    String getEmergencyStopReason() const { return emergency_stop_reason; }
    
    // Status für Monitoring
    DynamicJsonDocument getStatusJson() const;
    bool areAllActuatorsHealthy() const;
    bool isInitialized() const { return initialized; }
    
private:
    void initializeActuators(const Config& config);
    bool validateActuatorOperation(const String& actuator_id) const;
    void createDosingPumps(const Config& config);
};

#endif // ACTUATOR_MANAGER_H 