#include "MultiPointCalibration.h"
#include "../../core/Logger.h"
#include <algorithm>

MultiPointCalibration::MultiPointCalibration() : valid(false) {
}

float MultiPointCalibration::calibrate(float raw_value) const {
    if (!isValid()) {
        Logger::warn("Multi-point calibration not valid, returning raw value", "MultiPointCalibration");
        return raw_value;
    }
    
    return interpolate(raw_value);
}

bool MultiPointCalibration::loadFromJson(const JsonObject& calibration_data) {
    clearPoints();
    
    if (!calibration_data.containsKey("points")) {
        Logger::error("No calibration points found", "MultiPointCalibration");
        return false;
    }
    
    JsonArray points_array = calibration_data["points"];
    
    for (JsonObject point : points_array) {
        float raw = point["raw"] | 0.0;
        float value = point["value"] | point["ph"] | point["tds"] | 0.0;
        
        if (!addPoint(raw, value)) {
            Logger::error("Failed to add calibration point", "MultiPointCalibration");
            return false;
        }
    }
    
    if (points.size() < 2) {
        Logger::error("Multi-point calibration requires at least 2 points", "MultiPointCalibration");
        valid = false;
        return false;
    }
    
    sortPoints();
    valid = true;
    
    Logger::info("Multi-point calibration loaded with " + String(points.size()) + " points", "MultiPointCalibration");
    return true;
}

DynamicJsonDocument MultiPointCalibration::toJson() const {
    DynamicJsonDocument doc(512);
    
    doc["type"] = "multi_point";
    doc["valid"] = valid;
    
    JsonArray points_array = doc.createNestedArray("points");
    
    for (const auto& point : points) {
        JsonObject p = points_array.createNestedObject();
        p["raw"] = point.raw;
        p["value"] = point.value;
    }
    
    return doc;
}

bool MultiPointCalibration::addPoint(float raw, float value) {
    // Prüfe ob Punkt bereits existiert
    for (const auto& point : points) {
        if (fabs(point.raw - raw) < 0.001) {
            Logger::warn("Calibration point with raw value " + String(raw) + " already exists", "MultiPointCalibration");
            return false;
        }
    }
    
    CalibrationPoint newPoint;
    newPoint.raw = raw;
    newPoint.value = value;
    points.push_back(newPoint);
    
    Logger::debug("Added calibration point: raw=" + String(raw) + ", value=" + String(value), "MultiPointCalibration");
    return true;
}

void MultiPointCalibration::clearPoints() {
    points.clear();
    valid = false;
}

float MultiPointCalibration::interpolate(float raw_value) const {
    if (points.empty()) return raw_value;
    
    // Wenn nur ein Punkt vorhanden ist (sollte nicht passieren wenn valid)
    if (points.size() == 1) {
        return points[0].value;
    }
    
    // Finde die zwei nächsten Punkte für Interpolation
    
    // Wenn raw_value kleiner als kleinster Punkt -> Extrapolation mit ersten zwei Punkten
    if (raw_value <= points[0].raw) {
        float slope = (points[1].value - points[0].value) / (points[1].raw - points[0].raw);
        return points[0].value + slope * (raw_value - points[0].raw);
    }
    
    // Wenn raw_value größer als größter Punkt -> Extrapolation mit letzten zwei Punkten
    if (raw_value >= points.back().raw) {
        size_t n = points.size();
        float slope = (points[n-1].value - points[n-2].value) / (points[n-1].raw - points[n-2].raw);
        return points[n-1].value + slope * (raw_value - points[n-1].raw);
    }
    
    // Lineare Interpolation zwischen zwei Punkten
    for (size_t i = 0; i < points.size() - 1; i++) {
        if (raw_value >= points[i].raw && raw_value <= points[i+1].raw) {
            float x1 = points[i].raw;
            float y1 = points[i].value;
            float x2 = points[i+1].raw;
            float y2 = points[i+1].value;
            
            // Lineare Interpolation: y = y1 + (y2-y1)/(x2-x1) * (x-x1)
            float slope = (y2 - y1) / (x2 - x1);
            return y1 + slope * (raw_value - x1);
        }
    }
    
    // Sollte nie erreicht werden
    return raw_value;
}

void MultiPointCalibration::sortPoints() {
    std::sort(points.begin(), points.end(), 
              [](const CalibrationPoint& a, const CalibrationPoint& b) {
                  return a.raw < b.raw;
              });
    
    Logger::debug("Calibration points sorted by raw value", "MultiPointCalibration");
} 