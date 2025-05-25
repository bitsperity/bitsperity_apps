#include "PHSensor.h"
#include "calibration/Calibration.h"
#include "filters/NoiseFilter.h"

PHSensor::PHSensor() : BaseSensor(SensorType::PH) {
    Logger::debug("PHSensor created", "PHSensor");
}

bool PHSensor::init(const SensorConfig& sensor_config) {
    config = sensor_config;
    pin = config.pin;
    
    Logger::info("Initializing pH sensor on pin " + String(pin), "PHSensor");
    
    // Pin als Analog-Input konfigurieren
    pinMode(pin, INPUT);
    
    // Kalibrierung laden wenn vorhanden
    if (config.calibration.size() > 0) {
        calibration = Calibration::createFromConfig(config.calibration.as<JsonObject>());
        if (calibration && calibration->isValid()) {
            Logger::info("pH calibration loaded successfully", "PHSensor");
            last_reading.calibration_valid = true;
        } else {
            Logger::warn("pH calibration invalid or failed to load", "PHSensor");
            last_reading.calibration_valid = false;
        }
    }
    
    // Filter laden wenn konfiguriert
    if (config.noise_filter.size() > 0) {
        JsonObject filterConfig = config.noise_filter.as<JsonObject>();
        if (filterConfig["enabled"] | false) {
            filter = NoiseFilter::createFromConfig(filterConfig);
            if (filter) {
                Logger::info("pH noise filter loaded successfully", "PHSensor");
            }
        }
    }
    
    initialized = true;
    Logger::info("pH sensor initialized successfully", "PHSensor");
    return true;
}

SensorReading PHSensor::read() {
    if (!initialized) {
        Logger::error("pH sensor not initialized", "PHSensor");
        return last_reading;
    }
    
    // Rohwert lesen
    float raw = readAverageRaw();
    last_reading.raw = raw;
    
    // Kalibrierung anwenden
    float calibrated = applyCalibration(raw);
    last_reading.calibrated = calibrated;
    
    // Filter anwenden
    float filtered = applyFilter(calibrated);
    last_reading.filtered = filtered;
    
    // Timestamp aktualisieren
    last_reading.timestamp = millis();
    last_read_time = millis();
    
    // Validierung
    if (!isValidPH(filtered)) {
        Logger::warn("Invalid pH reading: " + String(filtered), "PHSensor");
        last_reading.quality = "error";
    } else {
        updateReadingQuality(last_reading);
    }
    
    Logger::debug("pH reading - Raw: " + String(raw) + 
                 ", Calibrated: " + String(calibrated) + 
                 ", Filtered: " + String(filtered) + 
                 ", Quality: " + last_reading.quality, "PHSensor");
    
    return last_reading;
}

bool PHSensor::calibrate(const JsonArray& calibration_points) {
    if (calibration_points.size() < 2) {
        Logger::error("pH calibration requires at least 2 points", "PHSensor");
        return false;
    }
    
    // Neue Kalibrierung erstellen
    DynamicJsonDocument cal_doc(256);
    JsonObject cal_obj = cal_doc.to<JsonObject>();
    cal_obj["type"] = "multi_point";
    JsonArray points = cal_obj.createNestedArray("points");
    
    // Kalibrierungspunkte kopieren
    for (JsonObject point : calibration_points) {
        JsonObject newPoint = points.createNestedObject();
        newPoint["raw"] = point["raw"];
        newPoint["ph"] = point["ph"];
    }
    
    // Kalibrierung laden
    calibration = Calibration::createFromConfig(cal_obj);
    if (calibration && calibration->isValid()) {
        last_reading.calibration_valid = true;
        Logger::info("pH sensor calibrated successfully with " + 
                    String(calibration_points.size()) + " points", "PHSensor");
        return true;
    } else {
        last_reading.calibration_valid = false;
        Logger::error("pH calibration failed", "PHSensor");
        return false;
    }
}

float PHSensor::readRaw() {
    return analogRead(pin);
}

float PHSensor::readAverageRaw() {
    float sum = 0;
    int validSamples = 0;
    
    // Mehrere Messungen für Stabilität
    for (int i = 0; i < SAMPLE_COUNT; i++) {
        float reading = readRaw();
        
        // Einfache Plausibilitätsprüfung
        if (reading >= 0 && reading <= 4095) { // 12-bit ADC
            sum += reading;
            validSamples++;
        }
        
        delay(10); // Kurze Pause zwischen Messungen
    }
    
    if (validSamples == 0) {
        Logger::error("No valid pH readings", "PHSensor");
        return 0;
    }
    
    return sum / validSamples;
}

bool PHSensor::isValidPH(float ph_value) const {
    return ph_value >= PH_MIN && ph_value <= PH_MAX && !isnan(ph_value) && !isinf(ph_value);
} 