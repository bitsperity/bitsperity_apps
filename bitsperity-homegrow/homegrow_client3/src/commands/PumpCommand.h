#ifndef PUMP_COMMAND_H
#define PUMP_COMMAND_H

#include "BaseCommand.h"
#include "../actuators/ActuatorManager.h"

class ActivatePumpCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String pump_id;
    unsigned long duration_ms;
    
public:
    ActivatePumpCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class StopPumpCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String pump_id;
    
public:
    StopPumpCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class StopAllPumpsCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    
public:
    StopAllPumpsCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class DoseVolumeCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String pump_id;
    float volume_ml;
    
public:
    DoseVolumeCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class SchedulePumpCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String pump_id;
    unsigned long interval_minutes;
    unsigned long duration_seconds;
    
public:
    SchedulePumpCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class CancelScheduleCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String pump_id;
    
public:
    CancelScheduleCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

#endif // PUMP_COMMAND_H 