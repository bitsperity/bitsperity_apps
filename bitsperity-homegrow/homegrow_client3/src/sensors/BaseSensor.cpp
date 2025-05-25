#include "BaseSensor.h"
#include "calibration/Calibration.h"
#include "filters/NoiseFilter.h"
#include <math.h>

BaseSensor::BaseSensor(SensorType sensor_type) : 
    type(sensor_type),
    last_read_time(0),
    initialized(false),
    pin(-1) {
    
    // Initialisiere last_reading mit Default-Werten
    last_reading.raw = 0;
    last_reading.calibrated = 0;
    last_reading.filtered = 0;
    last_reading.timestamp = 0;
    last_reading.quality = "unknown";
    last_reading.calibration_valid = false;
}

float BaseSensor::applyCalibration(float raw_value) {
    if (calibration && calibration->isValid()) {
        return calibration->calibrate(raw_value);
    }
    // Ohne Kalibrierung: Rohwert zurückgeben
    return raw_value;
}

float BaseSensor::applyFilter(float calibrated_value) {
    if (filter) {
        return filter->filter(calibrated_value);
    }
    // Ohne Filter: Kalibrierten Wert zurückgeben
    return calibrated_value;
}

bool BaseSensor::validateReading(float value) const {
    // Basis-Validierung: Wert sollte nicht NaN oder Inf sein
    if (isnan(value) || isinf(value)) {
        return false;
    }
    
    // Sensor-spezifische Validierung in abgeleiteten Klassen
    return true;
}

void BaseSensor::updateReadingQuality(SensorReading& reading) const {
    // Qualität basierend auf verschiedenen Faktoren bestimmen
    if (!reading.calibration_valid) {
        reading.quality = "uncalibrated";
    } else if (!validateReading(reading.filtered)) {
        reading.quality = "error";
    } else if (abs(reading.filtered - reading.calibrated) > 
               (reading.calibrated * 0.1)) { // > 10% Abweichung
        reading.quality = "warning";
    } else {
        reading.quality = "good";
    }
}

DynamicJsonDocument BaseSensor::getStatusJson() const {
    DynamicJsonDocument doc(512);
    
    doc["type"] = (type == SensorType::PH) ? "ph" : "tds";
    doc["initialized"] = initialized;
    doc["pin"] = pin;
    doc["enabled"] = config.enabled;
    
    // Letzte Messung
    JsonObject last = doc.createNestedObject("last_reading");
    last["raw"] = last_reading.raw;
    last["calibrated"] = last_reading.calibrated;
    last["filtered"] = last_reading.filtered;
    last["quality"] = last_reading.quality;
    last["timestamp"] = last_reading.timestamp;
    last["age_ms"] = millis() - last_reading.timestamp;
    
    // Kalibrierungs-Status
    JsonObject cal = doc.createNestedObject("calibration");
    cal["valid"] = last_reading.calibration_valid;
    if (calibration) {
        cal["type"] = "configured";
    } else {
        cal["type"] = "none";
    }
    
    // Filter-Status
    JsonObject filt = doc.createNestedObject("filter");
    if (filter) {
        filt["enabled"] = true;
        filt["type"] = "configured";
    } else {
        filt["enabled"] = false;
    }
    
    return doc;
}

bool BaseSensor::isHealthy() const {
    if (!initialized) return false;
    
    // Prüfe ob letzte Messung zu alt ist (> 5 Minuten)
    if (millis() - last_reading.timestamp > 300000) {
        return false;
    }
    
    // Prüfe Qualität der letzten Messung
    if (last_reading.quality == "error") {
        return false;
    }
    
    return true;
} 