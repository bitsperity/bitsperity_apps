#ifndef RUNNING_STATE_H
#define RUNNING_STATE_H

#include "BaseState.h"

class RunningState : public BaseState {
private:
    unsigned long last_heartbeat;
    unsigned long last_sensor_check;
    unsigned long last_safety_check;
    
    static const unsigned long HEARTBEAT_INTERVAL_MS = 30000; // 30 Sekunden
    static const unsigned long SENSOR_CHECK_INTERVAL_MS = 1000; // 1 Sekunde
    static const unsigned long SAFETY_CHECK_INTERVAL_MS = 5000; // 5 Sekunden
    
public:
    RunningState(Application* app);
    
    void enter() override;
    void exit() override;
    void update() override;
    void handleEvent(const String& event, const JsonObject& data) override;
    
private:
    void performHeartbeat();
    void performSensorCheck();
    void performSafetyCheck();
    void handleMQTTMessage(const String& topic, const String& payload);
    void handleConnectionLoss();
    bool checkEmergencyConditions();
};

#endif // RUNNING_STATE_H 