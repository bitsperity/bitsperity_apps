#include "LinearCalibration.h"
#include "../../core/Logger.h"
#include <math.h>

LinearCalibration::LinearCalibration() : 
    slope(1.0),
    offset(0.0),
    valid(false) {
}

float LinearCalibration::calibrate(float raw_value) const {
    if (!valid) {
        Logger::warn("Linear calibration not valid, returning raw value", "LinearCalibration");
        return raw_value;
    }
    
    // y = mx + b
    return slope * raw_value + offset;
}

bool LinearCalibration::loadFromJson(const JsonObject& calibration_data) {
    // Prüfe ob direkte Parameter vorhanden sind
    if (calibration_data.containsKey("slope") && calibration_data.containsKey("offset")) {
        slope = calibration_data["slope"] | 1.0;
        offset = calibration_data["offset"] | 0.0;
        valid = true;
        Logger::debug("Linear calibration loaded: slope=" + String(slope) + 
                     ", offset=" + String(offset), "LinearCalibration");
        return true;
    }
    
    // Prüfe ob 2-Punkt-Kalibrierung vorhanden ist
    if (calibration_data.containsKey("points")) {
        JsonArray points = calibration_data["points"];
        if (points.size() >= 2) {
            float raw1 = points[0]["raw"] | 0.0;
            float value1 = points[0]["value"] | points[0]["ph"] | points[0]["tds"] | 0.0;
            float raw2 = points[1]["raw"] | 0.0;
            float value2 = points[1]["value"] | points[1]["ph"] | points[1]["tds"] | 0.0;
            
            return setTwoPoints(raw1, value1, raw2, value2);
        }
    }
    
    Logger::error("Invalid linear calibration data", "LinearCalibration");
    valid = false;
    return false;
}

DynamicJsonDocument LinearCalibration::toJson() const {
    DynamicJsonDocument doc(128);
    
    doc["type"] = "linear";
    doc["slope"] = slope;
    doc["offset"] = offset;
    doc["valid"] = valid;
    
    return doc;
}

bool LinearCalibration::setTwoPoints(float raw1, float value1, float raw2, float value2) {
    // Prüfe ob Punkte unterschiedlich sind
    if (fabs(raw2 - raw1) < 0.001) {
        Logger::error("Calibration points too close (raw values identical)", "LinearCalibration");
        valid = false;
        return false;
    }
    
    // Berechne Steigung: m = (y2 - y1) / (x2 - x1)
    slope = (value2 - value1) / (raw2 - raw1);
    
    // Berechne Offset: b = y - mx
    offset = value1 - slope * raw1;
    
    valid = true;
    
    Logger::info("Linear calibration calculated from 2 points:", "LinearCalibration");
    Logger::info("  Point 1: raw=" + String(raw1) + ", value=" + String(value1), "LinearCalibration");
    Logger::info("  Point 2: raw=" + String(raw2) + ", value=" + String(value2), "LinearCalibration");
    Logger::info("  Result: slope=" + String(slope) + ", offset=" + String(offset), "LinearCalibration");
    
    return true;
}

void LinearCalibration::setParameters(float new_slope, float new_offset) {
    slope = new_slope;
    offset = new_offset;
    valid = true;
    
    Logger::debug("Linear calibration parameters set: slope=" + String(slope) + 
                 ", offset=" + String(offset), "LinearCalibration");
} 