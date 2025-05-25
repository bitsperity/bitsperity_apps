#include "TDSSensor.h"
#include "calibration/Calibration.h"
#include "filters/NoiseFilter.h"

TDSSensor::TDSSensor() : BaseSensor(SensorType::TDS) {
    Logger::debug("TDSSensor created", "TDSSensor");
}

bool TDSSensor::init(const SensorConfig& sensor_config) {
    config = sensor_config;
    pin = config.pin;
    
    Logger::info("Initializing TDS sensor on pin " + String(pin), "TDSSensor");
    
    // Pin als Analog-Input konfigurieren
    pinMode(pin, INPUT);
    
    // Kalibrierung laden wenn vorhanden
    if (config.calibration.size() > 0) {
        calibration = Calibration::createFromConfig(config.calibration.as<JsonObject>());
        if (calibration && calibration->isValid()) {
            Logger::info("TDS calibration loaded successfully", "TDSSensor");
            last_reading.calibration_valid = true;
        } else {
            Logger::warn("TDS calibration invalid or failed to load", "TDSSensor");
            last_reading.calibration_valid = false;
        }
    }
    
    // Filter laden wenn konfiguriert
    if (config.noise_filter.size() > 0) {
        JsonObject filterConfig = config.noise_filter.as<JsonObject>();
        if (filterConfig["enabled"] | false) {
            filter = NoiseFilter::createFromConfig(filterConfig);
            if (filter) {
                Logger::info("TDS noise filter loaded successfully", "TDSSensor");
            }
        }
    }
    
    initialized = true;
    Logger::info("TDS sensor initialized successfully", "TDSSensor");
    return true;
}

SensorReading TDSSensor::read() {
    if (!initialized) {
        Logger::error("TDS sensor not initialized", "TDSSensor");
        return last_reading;
    }
    
    // Rohwert lesen
    float raw = readAverageRaw();
    last_reading.raw = raw;
    
    // Kalibrierung anwenden
    float calibrated = applyCalibration(raw);
    
    // Temperaturkompensation
    calibrated = compensateTemperature(calibrated);
    last_reading.calibrated = calibrated;
    
    // Filter anwenden
    float filtered = applyFilter(calibrated);
    last_reading.filtered = filtered;
    
    // Timestamp aktualisieren
    last_reading.timestamp = millis();
    last_read_time = millis();
    
    // Validierung
    if (!isValidTDS(filtered)) {
        Logger::warn("Invalid TDS reading: " + String(filtered), "TDSSensor");
        last_reading.quality = "error";
    } else {
        updateReadingQuality(last_reading);
    }
    
    Logger::debug("TDS reading - Raw: " + String(raw) + 
                 ", Calibrated: " + String(calibrated) + 
                 ", Filtered: " + String(filtered) + 
                 ", Quality: " + last_reading.quality, "TDSSensor");
    
    return last_reading;
}

bool TDSSensor::calibrate(const JsonArray& calibration_points) {
    if (calibration_points.size() < 1) {
        Logger::error("TDS calibration requires at least 1 point", "TDSSensor");
        return false;
    }
    
    // Neue Kalibrierung erstellen
    DynamicJsonDocument cal_doc(256);
    JsonObject cal_obj = cal_doc.to<JsonObject>();
    
    if (calibration_points.size() == 1) {
        // Single-Point-Kalibrierung
        cal_obj["type"] = "single_point";
        JsonObject ref = cal_obj.createNestedObject("reference_point");
        ref["raw"] = calibration_points[0]["raw"];
        ref["tds"] = calibration_points[0]["tds"];
    } else {
        // Multi-Point-Kalibrierung
        cal_obj["type"] = "multi_point";
        JsonArray points = cal_obj.createNestedArray("points");
        
        for (JsonObject point : calibration_points) {
            JsonObject newPoint = points.createNestedObject();
            newPoint["raw"] = point["raw"];
            newPoint["tds"] = point["tds"];
        }
    }
    
    // Kalibrierung laden
    calibration = Calibration::createFromConfig(cal_obj);
    if (calibration && calibration->isValid()) {
        last_reading.calibration_valid = true;
        Logger::info("TDS sensor calibrated successfully with " + 
                    String(calibration_points.size()) + " point(s)", "TDSSensor");
        return true;
    } else {
        last_reading.calibration_valid = false;
        Logger::error("TDS calibration failed", "TDSSensor");
        return false;
    }
}

float TDSSensor::readRaw() {
    return analogRead(pin);
}

float TDSSensor::readAverageRaw() {
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
        Logger::error("No valid TDS readings", "TDSSensor");
        return 0;
    }
    
    return sum / validSamples;
}

float TDSSensor::compensateTemperature(float tds_value) const {
    // Einfache Temperaturkompensation
    // TDS-Werte sind normalerweise auf 25°C normiert
    // Ohne Temperatursensor nehmen wir 25°C an
    float temperature = TEMPERATURE_COMPENSATION;
    
    // Temperaturkoeffizient für TDS (ca. 2% pro °C)
    float compensationCoefficient = 1.0 + 0.02 * (temperature - 25.0);
    
    return tds_value / compensationCoefficient;
}

bool TDSSensor::isValidTDS(float tds_value) const {
    return tds_value >= TDS_MIN && tds_value <= TDS_MAX && !isnan(tds_value) && !isinf(tds_value);
} 