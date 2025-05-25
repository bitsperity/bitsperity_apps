#ifndef DOSING_PUMP_H
#define DOSING_PUMP_H

#include "Pump.h"

class DosingPump : public Pump {
private:
    String substance;
    String concentration;
    float max_dose_ml;
    unsigned long last_dose_time;
    float total_volume_dispensed_ml;
    
public:
    DosingPump(const String& id);
    
    bool init(const ActuatorConfig& actuator_config) override;
    
    // Dosier-spezifische Methoden
    bool dose(float volume_ml) override;
    bool canDose(float volume_ml) const;
    
    // Substanz-Information
    String getSubstance() const { return substance; }
    String getConcentration() const { return concentration; }
    float getTotalVolumeDispensed() const { return total_volume_dispensed_ml; }
    float getMaxDose() const { return max_dose_ml; }
    
    // Status für Monitoring
    DynamicJsonDocument getStatusJson() const override;
    
private:
    bool validateDoseRequest(float volume_ml) const;
    void logDose(float volume_ml);
};

#endif // DOSING_PUMP_H 