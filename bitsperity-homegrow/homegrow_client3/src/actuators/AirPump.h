#ifndef AIR_PUMP_H
#define AIR_PUMP_H

#include "Pump.h"

class AirPump : public Pump {
private:
    bool scheduled_enabled;
    unsigned long schedule_interval_ms;
    unsigned long schedule_duration_ms;
    unsigned long last_scheduled_activation;
    
public:
    AirPump();
    
    bool init(const ActuatorConfig& actuator_config) override;
    void loop() override;
    
    // Scheduling
    bool setSchedule(unsigned long interval_minutes, unsigned long duration_seconds);
    bool cancelSchedule();
    bool isScheduleEnabled() const { return scheduled_enabled; }
    
    // Status für Monitoring
    DynamicJsonDocument getStatusJson() const override;
    
private:
    void checkScheduledActivation();
    bool shouldActivateScheduled() const;
};

#endif // AIR_PUMP_H 