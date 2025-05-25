#ifndef PH_SENSOR_H
#define PH_SENSOR_H

#include "BaseSensor.h"

class PHSensor : public BaseSensor {
private:
    static const int SAMPLE_COUNT = 10;
    static constexpr float PH_MIN = 0.0;
    static constexpr float PH_MAX = 14.0;
    
public:
    PHSensor();
    
    bool init(const SensorConfig& sensor_config) override;
    SensorReading read() override;
    bool calibrate(const JsonArray& calibration_points) override;
    
protected:
    float readRaw() override;
    
private:
    float readAverageRaw();
    bool isValidPH(float ph_value) const;
};

#endif // PH_SENSOR_H 