#include "MovingAverageFilter.h"
#include "../../core/Logger.h"
#include <algorithm>
#include <cmath>

MovingAverageFilter::MovingAverageFilter(size_t window_size, float outlier_threshold) :
    window_size(window_size),
    current_index(0),
    buffer_full(false),
    outlier_threshold(outlier_threshold) {
    
    buffer.reserve(window_size);
    Logger::debug("MovingAverageFilter created with window size " + String(window_size), "MovingAverageFilter");
}

float MovingAverageFilter::filter(float value) {
    // Prüfe auf Outlier wenn Buffer genug Daten hat
    if (buffer.size() >= 3 && isOutlier(value)) {
        Logger::debug("Outlier detected: " + String(value) + ", using average instead", "MovingAverageFilter");
        return calculateAverage();
    }
    
    // Füge Wert zum Buffer hinzu
    if (buffer.size() < window_size) {
        buffer.push_back(value);
    } else {
        buffer[current_index] = value;
        buffer_full = true;
    }
    
    // Index für Ringbuffer aktualisieren
    current_index = (current_index + 1) % window_size;
    
    // Durchschnitt berechnen und zurückgeben
    return calculateAverage();
}

void MovingAverageFilter::reset() {
    buffer.clear();
    current_index = 0;
    buffer_full = false;
    Logger::debug("MovingAverageFilter reset", "MovingAverageFilter");
}

bool MovingAverageFilter::loadFromJson(const JsonObject& filter_config) {
    if (filter_config.containsKey("window_size")) {
        window_size = filter_config["window_size"] | 10;
        buffer.clear();
        buffer.reserve(window_size);
        current_index = 0;
        buffer_full = false;
    }
    
    if (filter_config.containsKey("outlier_threshold")) {
        outlier_threshold = filter_config["outlier_threshold"] | 2.0;
    }
    
    Logger::info("MovingAverageFilter configured: window_size=" + String(window_size) + 
                ", outlier_threshold=" + String(outlier_threshold), "MovingAverageFilter");
    
    return true;
}

DynamicJsonDocument MovingAverageFilter::toJson() const {
    DynamicJsonDocument doc(256);
    
    doc["type"] = "moving_average";
    doc["window_size"] = window_size;
    doc["outlier_threshold"] = outlier_threshold;
    doc["buffer_size"] = buffer.size();
    doc["buffer_full"] = buffer_full;
    
    if (!buffer.empty()) {
        doc["current_average"] = calculateAverage();
        doc["current_std_dev"] = calculateStandardDeviation();
    }
    
    return doc;
}

bool MovingAverageFilter::isOutlier(float value) const {
    if (buffer.size() < 3) {
        return false; // Nicht genug Daten für Outlier-Erkennung
    }
    
    float avg = calculateAverage();
    float std_dev = calculateStandardDeviation();
    
    if (std_dev == 0) {
        return false; // Keine Variation in den Daten
    }
    
    // Z-Score berechnen
    float z_score = fabs(value - avg) / std_dev;
    
    return z_score > outlier_threshold;
}

float MovingAverageFilter::calculateAverage() const {
    if (buffer.empty()) {
        return 0;
    }
    
    float sum = 0;
    for (float val : buffer) {
        sum += val;
    }
    
    return sum / buffer.size();
}

float MovingAverageFilter::calculateStandardDeviation() const {
    if (buffer.size() < 2) {
        return 0;
    }
    
    float avg = calculateAverage();
    float sum_squared_diff = 0;
    
    for (float val : buffer) {
        float diff = val - avg;
        sum_squared_diff += diff * diff;
    }
    
    return sqrt(sum_squared_diff / (buffer.size() - 1));
}

float MovingAverageFilter::calculateMedian() const {
    if (buffer.empty()) {
        return 0;
    }
    
    std::vector<float> sorted_buffer = buffer;
    std::sort(sorted_buffer.begin(), sorted_buffer.end());
    
    size_t n = sorted_buffer.size();
    if (n % 2 == 0) {
        return (sorted_buffer[n/2 - 1] + sorted_buffer[n/2]) / 2.0;
    } else {
        return sorted_buffer[n/2];
    }
} 