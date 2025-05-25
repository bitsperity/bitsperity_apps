#ifndef TDS_SENSOR_H
#define TDS_SENSOR_H

#include "BaseSensor.h"

class TDSSensor : public BaseSensor {
private:
    static const int SAMPLE_COUNT = 10;
    static constexpr float TDS_MIN = 0.0;
    static constexpr float TDS_MAX = 5000.0;
    static constexpr float TEMPERATURE_COMPENSATION = 25.0; // Standard-Temperatur
    
public:
    TDSSensor();
    
    bool init(const SensorConfig& sensor_config) override;
    SensorReading read() override;
    bool calibrate(const JsonArray& calibration_points) override;
    
protected:
    float readRaw() override;
    
private:
    float readAverageRaw();
    float compensateTemperature(float tds_value) const;
    bool isValidTDS(float tds_value) const;
};

#endif // TDS_SENSOR_H 