#ifndef LINEAR_CALIBRATION_H
#define LINEAR_CALIBRATION_H

#include "Calibration.h"

class LinearCalibration : public Calibration {
private:
    float slope;
    float offset;
    bool valid;
    
public:
    LinearCalibration();
    
    float calibrate(float raw_value) const override;
    bool loadFromJson(const JsonObject& calibration_data) override;
    DynamicJsonDocument toJson() const override;
    bool isValid() const override { return valid; }
    
    // Für 2-Punkt-Kalibrierung
    bool setTwoPoints(float raw1, float value1, float raw2, float value2);
    
    // Direkte Parameter
    void setParameters(float slope, float offset);
    float getSlope() const { return slope; }
    float getOffset() const { return offset; }
};

#endif // LINEAR_CALIBRATION_H 