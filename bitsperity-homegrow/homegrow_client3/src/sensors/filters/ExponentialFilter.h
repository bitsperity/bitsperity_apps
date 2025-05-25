#ifndef EXPONENTIAL_FILTER_H
#define EXPONENTIAL_FILTER_H

#include "NoiseFilter.h"

class ExponentialFilter : public NoiseFilter {
private:
    float alpha;
    float filtered_value;
    bool initialized;
    float outlier_threshold;
    float last_valid_value;
    
public:
    ExponentialFilter(float alpha = 0.1, float outlier_threshold = 2.0);
    
    float filter(float value) override;
    void reset() override;
    bool loadFromJson(const JsonObject& filter_config) override;
    DynamicJsonDocument toJson() const override;
    
    // Getter/Setter
    float getAlpha() const { return alpha; }
    void setAlpha(float new_alpha);
    
private:
    bool isOutlier(float value) const;
};

#endif // EXPONENTIAL_FILTER_H 