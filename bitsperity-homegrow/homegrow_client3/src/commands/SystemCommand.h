#ifndef SYSTEM_COMMAND_H
#define SYSTEM_COMMAND_H

#include "BaseCommand.h"
#include "../actuators/ActuatorManager.h"
#include "../sensors/SensorManager.h"

class EmergencyStopCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    String reason;
    
public:
    EmergencyStopCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class ClearEmergencyStopCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    
public:
    ClearEmergencyStopCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class CalibrateSensorCommand : public BaseCommand {
private:
    SensorManager* sensor_manager;
    SensorType sensor_type;
    JsonArray calibration_points;
    
public:
    CalibrateSensorCommand(const String& cmd_id, SensorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
    
private:
    SensorType parseSensorType(const String& sensor_id) const;
};

class ResetSystemCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    
public:
    ResetSystemCommand(const String& cmd_id, ActuatorManager* manager);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
};

class GetSystemStatusCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    SensorManager* sensor_manager;
    
public:
    GetSystemStatusCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
    
private:
    JsonObject createSystemStatus() const;
};

#endif // SYSTEM_COMMAND_H 