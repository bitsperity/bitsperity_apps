#include "NoiseFilter.h"
#include "MovingAverageFilter.h"
#include "ExponentialFilter.h"
#include "../../core/Logger.h"

std::unique_ptr<NoiseFilter> NoiseFilter::createFromConfig(const JsonObject& config) {
    if (config.isNull() || config.size() == 0) {
        Logger::warn("No filter config provided", "NoiseFilter");
        return nullptr;
    }
    
    // Prüfe ob Filter aktiviert ist
    bool enabled = config["enabled"] | true;
    if (!enabled) {
        Logger::info("Filter disabled in config", "NoiseFilter");
        return nullptr;
    }
    
    String type = config["type"] | "";
    
    if (type == "moving_average") {
        size_t window_size = config["window_size"] | 10;
        float outlier_threshold = config["outlier_threshold"] | 2.0;
        
        std::unique_ptr<MovingAverageFilter> filter(new MovingAverageFilter(window_size, outlier_threshold));
        if (filter->loadFromJson(config)) {
            Logger::info("Created moving average filter", "NoiseFilter");
            return std::move(filter);
        }
    } else if (type == "exponential") {
        float alpha = config["alpha"] | 0.1;
        float outlier_threshold = config["outlier_threshold"] | 2.0;
        
        std::unique_ptr<ExponentialFilter> filter(new ExponentialFilter(alpha, outlier_threshold));
        if (filter->loadFromJson(config)) {
            Logger::info("Created exponential filter", "NoiseFilter");
            return std::move(filter);
        }
    } else {
        Logger::error("Unknown filter type: " + type, "NoiseFilter");
    }
    
    return nullptr;
} 