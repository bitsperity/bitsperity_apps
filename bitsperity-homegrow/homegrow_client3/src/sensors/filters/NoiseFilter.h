#ifndef NOISE_FILTER_H
#define NOISE_FILTER_H

#include <ArduinoJson.h>
#include <memory>

class NoiseFilter {
public:
    virtual ~NoiseFilter() = default;
    virtual float filter(float value) = 0;
    virtual void reset() = 0;
    virtual bool loadFromJson(const JsonObject& filter_config) = 0;
    virtual DynamicJsonDocument toJson() const = 0;
    
    static std::unique_ptr<NoiseFilter> createFromConfig(const JsonObject& config);
};

#endif // NOISE_FILTER_H 