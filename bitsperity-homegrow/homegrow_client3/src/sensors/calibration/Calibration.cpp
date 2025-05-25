#include "Calibration.h"
#include "LinearCalibration.h"
#include "MultiPointCalibration.h"
#include "../../core/Logger.h"

std::unique_ptr<Calibration> Calibration::createFromConfig(const JsonObject& config) {
    if (config.isNull() || config.size() == 0) {
        Logger::warn("No calibration config provided", "Calibration");
        return nullptr;
    }
    
    String type = config["type"] | "";
    
    if (type == "linear") {
        std::unique_ptr<LinearCalibration> calibration(new LinearCalibration());
        if (calibration->loadFromJson(config)) {
            Logger::info("Created linear calibration", "Calibration");
            return std::move(calibration);
        }
    } else if (type == "multi_point") {
        std::unique_ptr<MultiPointCalibration> calibration(new MultiPointCalibration());
        if (calibration->loadFromJson(config)) {
            Logger::info("Created multi-point calibration", "Calibration");
            return std::move(calibration);
        }
    } else if (type == "single_point") {
        // Single-Point ist ein Spezialfall von Linear-Kalibrierung
        std::unique_ptr<LinearCalibration> calibration(new LinearCalibration());
        
        // Konvertiere single_point zu linear
        if (config.containsKey("reference_point")) {
            JsonObject ref = config["reference_point"];
            float raw_ref = ref["raw"] | 0.0;
            float value_ref = ref["value"] | ref["ph"] | ref["tds"] | 0.0;
            
            // Bei Single-Point nehmen wir an: slope = value/raw, offset = 0
            // Oder besser: Wir gehen durch (0,0) und (raw_ref, value_ref)
            calibration->setTwoPoints(0, 0, raw_ref, value_ref);
            Logger::info("Created single-point calibration as linear", "Calibration");
            return std::move(calibration);
        }
    } else {
        // Versuche automatisch zu erkennen
        if (config.containsKey("points")) {
            std::unique_ptr<MultiPointCalibration> calibration(new MultiPointCalibration());
            if (calibration->loadFromJson(config)) {
                Logger::info("Auto-detected multi-point calibration", "Calibration");
                return std::move(calibration);
            }
        } else if (config.containsKey("slope") && config.containsKey("offset")) {
            std::unique_ptr<LinearCalibration> calibration(new LinearCalibration());
            if (calibration->loadFromJson(config)) {
                Logger::info("Auto-detected linear calibration", "Calibration");
                return std::move(calibration);
            }
        }
    }
    
    Logger::error("Failed to create calibration from config", "Calibration");
    return nullptr;
} 