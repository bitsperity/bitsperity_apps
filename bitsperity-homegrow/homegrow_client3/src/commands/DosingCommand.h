#ifndef DOSING_COMMAND_H
#define DOSING_COMMAND_H

#include "BaseCommand.h"
#include "../actuators/ActuatorManager.h"
#include "../sensors/SensorManager.h"

class AdjustPHByCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    SensorManager* sensor_manager;
    float delta_ph;
    float max_volume_ml;
    
public:
    AdjustPHByCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
    
private:
    float calculateRequiredVolume(float current_ph, float delta_ph) const;
    String selectPHPump(float delta_ph) const;
    float getCurrentPH() const;
};

class SetPHTargetCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    SensorManager* sensor_manager;
    float target_ph;
    float tolerance;
    int max_attempts;
    
public:
    SetPHTargetCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
    
private:
    bool adjustPHToTarget();
    float getCurrentPH() const;
};

class AdjustTDSByCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    SensorManager* sensor_manager;
    float delta_tds;
    float max_volume_ml;
    
public:
    AdjustTDSByCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
    
private:
    float calculateRequiredVolume(float current_tds, float delta_tds) const;
    std::vector<String> selectNutrientPumps() const;
    float getCurrentTDS() const;
};

class SetTDSTargetCommand : public BaseCommand {
private:
    ActuatorManager* actuator_manager;
    SensorManager* sensor_manager;
    float target_tds;
    float tolerance;
    int max_attempts;
    
public:
    SetTDSTargetCommand(const String& cmd_id, ActuatorManager* actuator_mgr, SensorManager* sensor_mgr);
    
    bool validate(const JsonObject& parameters) override;
    bool execute() override;
    void abort() override;
    
private:
    bool adjustTDSToTarget();
    float getCurrentTDS() const;
};

#endif // DOSING_COMMAND_H 