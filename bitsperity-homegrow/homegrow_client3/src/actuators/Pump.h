#ifndef PUMP_H
#define PUMP_H

#include "BaseActuator.h"

class Pump : public BaseActuator {
protected:
    float flow_rate_ml_per_sec;
    unsigned long planned_duration_ms;
    
public:
    Pump(const String& id, ActuatorType pump_type);
    
    bool init(const ActuatorConfig& actuator_config) override;
    bool activate(unsigned long duration_ms) override;
    bool deactivate() override;
    void loop() override;
    
    // Pumpen-spezifische Methoden
    virtual bool dose(float volume_ml);
    float calculateDurationForVolume(float volume_ml) const;
    float calculateVolumeForDuration(unsigned long duration_ms) const;
    
    // Getters
    float getFlowRate() const { return flow_rate_ml_per_sec; }
    
protected:
    bool hardwareActivate() override;
    bool hardwareDeactivate() override;
    
private:
    void checkAutoDeactivation();
};

#endif // PUMP_H 