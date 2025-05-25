#ifndef MULTI_POINT_CALIBRATION_H
#define MULTI_POINT_CALIBRATION_H

#include "Calibration.h"
#include <vector>

class MultiPointCalibration : public Calibration {
private:
    struct CalibrationPoint {
        float raw;
        float value;
    };
    
    std::vector<CalibrationPoint> points;
    bool valid;
    
public:
    MultiPointCalibration();
    
    float calibrate(float raw_value) const override;
    bool loadFromJson(const JsonObject& calibration_data) override;
    DynamicJsonDocument toJson() const override;
    bool isValid() const override { return valid && points.size() >= 2; }
    
    // Punkte hinzufügen
    bool addPoint(float raw, float value);
    void clearPoints();
    size_t getPointCount() const { return points.size(); }
    
private:
    float interpolate(float raw_value) const;
    void sortPoints();
};

#endif // MULTI_POINT_CALIBRATION_H 