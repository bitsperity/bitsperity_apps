#ifndef MOVING_AVERAGE_FILTER_H
#define MOVING_AVERAGE_FILTER_H

#include "NoiseFilter.h"
#include <vector>

class MovingAverageFilter : public NoiseFilter {
private:
    std::vector<float> buffer;
    size_t window_size;
    size_t current_index;
    bool buffer_full;
    float outlier_threshold;
    
public:
    MovingAverageFilter(size_t window_size = 10, float outlier_threshold = 2.0);
    
    float filter(float value) override;
    void reset() override;
    bool loadFromJson(const JsonObject& filter_config) override;
    DynamicJsonDocument toJson() const override;
    
private:
    bool isOutlier(float value) const;
    float calculateAverage() const;
    float calculateStandardDeviation() const;
    float calculateMedian() const;
};

#endif // MOVING_AVERAGE_FILTER_H 