#include "ExponentialFilter.h"
#include "../../core/Logger.h"
#include <cmath>

ExponentialFilter::ExponentialFilter(float alpha, float outlier_threshold) :
    alpha(alpha),
    filtered_value(0),
    initialized(false),
    outlier_threshold(outlier_threshold),
    last_valid_value(0) {
    
    // Alpha sollte zwischen 0 und 1 sein
    if (alpha < 0) alpha = 0;
    if (alpha > 1) alpha = 1;
    
    Logger::debug("ExponentialFilter created with alpha " + String(alpha), "ExponentialFilter");
}

float ExponentialFilter::filter(float value) {
    // Beim ersten Wert initialisieren
    if (!initialized) {
        filtered_value = value;
        last_valid_value = value;
        initialized = true;
        return filtered_value;
    }
    
    // Prüfe auf Outlier
    if (isOutlier(value)) {
        Logger::debug("Outlier detected: " + String(value) + ", using last filtered value", "ExponentialFilter");
        return filtered_value;
    }
    
    // Exponential Moving Average: y[n] = α * x[n] + (1-α) * y[n-1]
    filtered_value = alpha * value + (1.0 - alpha) * filtered_value;
    last_valid_value = value;
    
    return filtered_value;
}

void ExponentialFilter::reset() {
    filtered_value = 0;
    initialized = false;
    last_valid_value = 0;
    Logger::debug("ExponentialFilter reset", "ExponentialFilter");
}

bool ExponentialFilter::loadFromJson(const JsonObject& filter_config) {
    if (filter_config.containsKey("alpha")) {
        float new_alpha = filter_config["alpha"] | 0.1;
        setAlpha(new_alpha);
    }
    
    if (filter_config.containsKey("outlier_threshold")) {
        outlier_threshold = filter_config["outlier_threshold"] | 2.0;
    }
    
    Logger::info("ExponentialFilter configured: alpha=" + String(alpha) + 
                ", outlier_threshold=" + String(outlier_threshold), "ExponentialFilter");
    
    return true;
}

DynamicJsonDocument ExponentialFilter::toJson() const {
    DynamicJsonDocument doc(256);
    
    doc["type"] = "exponential";
    doc["alpha"] = alpha;
    doc["outlier_threshold"] = outlier_threshold;
    doc["initialized"] = initialized;
    
    if (initialized) {
        doc["current_filtered"] = filtered_value;
        doc["last_valid_value"] = last_valid_value;
    }
    
    return doc;
}

void ExponentialFilter::setAlpha(float new_alpha) {
    // Clamp alpha zwischen 0 und 1
    if (new_alpha < 0) new_alpha = 0;
    if (new_alpha > 1) new_alpha = 1;
    
    alpha = new_alpha;
    Logger::debug("ExponentialFilter alpha set to " + String(alpha), "ExponentialFilter");
}

bool ExponentialFilter::isOutlier(float value) const {
    if (!initialized) {
        return false; // Kann beim ersten Wert keinen Outlier erkennen
    }
    
    // Einfache Outlier-Erkennung basierend auf relativer Änderung
    float diff = fabs(value - filtered_value);
    float relative_change = diff / fabs(filtered_value);
    
    // Wenn die relative Änderung größer als threshold ist, ist es ein Outlier
    // Bei kleinen Werten (nahe 0) verwenden wir absolute Differenz
    if (fabs(filtered_value) < 1.0) {
        return diff > outlier_threshold;
    } else {
        return relative_change > (outlier_threshold / 10.0); // Threshold anpassen für relative Änderung
    }
} 