#ifndef BASE_SENSOR_H
#define BASE_SENSOR_H

#include "../core/Types.h"
#include "../config/Config.h"
#include "../core/Logger.h"
#include <memory>

// Forward-Deklarationen
class Calibration;
class NoiseFilter;

class BaseSensor {
protected:
    SensorType type;
    SensorConfig config;
    std::unique_ptr<Calibration> calibration;
    std::unique_ptr<NoiseFilter> filter;
    
    SensorReading last_reading;
    unsigned long last_read_time;
    bool initialized;
    int pin;
    
public:
    BaseSensor(SensorType sensor_type);
    virtual ~BaseSensor() = default;
    
    virtual bool init(const SensorConfig& sensor_config) = 0;
    virtual SensorReading read() = 0;
    virtual bool calibrate(const JsonArray& calibration_points) = 0;
    
    // Getters
    SensorType getType() const { return type; }
    const SensorReading& getLastReading() const { return last_reading; }
    bool isInitialized() const { return initialized; }
    int getPin() const { return pin; }
    
    // Status für Monitoring
    virtual DynamicJsonDocument getStatusJson() const;
    virtual bool isHealthy() const;
    
protected:
    virtual float readRaw() = 0;
    float applyCalibration(float raw_value);
    float applyFilter(float calibrated_value);
    bool validateReading(float value) const;
    void updateReadingQuality(SensorReading& reading) const;
};

#endif // BASE_SENSOR_H 