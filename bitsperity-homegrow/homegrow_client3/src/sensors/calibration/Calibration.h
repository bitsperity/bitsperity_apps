#ifndef CALIBRATION_H
#define CALIBRATION_H

#include <ArduinoJson.h>
#include <memory>

class Calibration {
public:
    virtual ~Calibration() = default;
    virtual float calibrate(float raw_value) const = 0;
    virtual bool loadFromJson(const JsonObject& calibration_data) = 0;
    virtual DynamicJsonDocument toJson() const = 0;
    virtual bool isValid() const = 0;
    
    static std::unique_ptr<Calibration> createFromConfig(const JsonObject& config);
};

#endif // CALIBRATION_H 