#include "SensorManager.h"
#include "calibration/Calibration.h"
#include "filters/NoiseFilter.h"

SensorManager::SensorManager() :
    mqtt_client(nullptr),
    ph_publish_rate_hz(1.0),
    tds_publish_rate_hz(0.5),
    last_ph_publish(0),
    last_tds_publish(0),
    initialized(false) {
}

bool SensorManager::init(const Config& config, MQTTClient* mqtt) {
    if (!mqtt) {
        Logger::error("MQTT client is null", "SensorManager");
        return false;
    }
    
    mqtt_client = mqtt;
    
    // Sensoren initialisieren
    initializeSensors(config);
    
    // Publishing-Raten aus Konfiguration laden
    if (config.ph_sensor.publishing.size() > 0) {
        ph_publish_rate_hz = config.ph_sensor.publishing["rate_hz"] | 1.0;
    }
    
    if (config.tds_sensor.publishing.size() > 0) {
        tds_publish_rate_hz = config.tds_sensor.publishing["rate_hz"] | 0.5;
    }
    
    initialized = true;
    
    Logger::info("SensorManager initialized with " + String(sensors.size()) + " sensors", "SensorManager");
    Logger::info("pH publish rate: " + String(ph_publish_rate_hz) + " Hz", "SensorManager");
    Logger::info("TDS publish rate: " + String(tds_publish_rate_hz) + " Hz", "SensorManager");
    
    return true;
}

void SensorManager::loop() {
    if (!initialized) {
        return;
    }
    
    // Alle Sensoren lesen
    readAllSensors();
    
    // Sensor-Daten publizieren wenn nötig
    publishSensorData();
}

bool SensorManager::addSensor(std::unique_ptr<BaseSensor> sensor) {
    if (!sensor) {
        Logger::error("Cannot add null sensor", "SensorManager");
        return false;
    }
    
    SensorType type = sensor->getType();
    
    // Prüfe ob Sensor bereits existiert
    for (const auto& existing_sensor : sensors) {
        if (existing_sensor->getType() == type) {
            Logger::warn("Sensor of type already exists, replacing", "SensorManager");
            // TODO: Sensor ersetzen statt hinzufügen
            break;
        }
    }
    
    sensors.push_back(std::move(sensor));
    Logger::info("Sensor added successfully", "SensorManager");
    
    return true;
}

BaseSensor* SensorManager::getSensor(SensorType type) {
    for (const auto& sensor : sensors) {
        if (sensor->getType() == type) {
            return sensor.get();
        }
    }
    
    return nullptr;
}

bool SensorManager::readAllSensors() {
    bool all_success = true;
    
    for (const auto& sensor : sensors) {
        if (!sensor->isInitialized()) {
            continue;
        }
        
        SensorReading reading = sensor->read();
        
        if (reading.quality == "error") {
            Logger::warn("Sensor reading failed for sensor type " + String((int)sensor->getType()), "SensorManager");
            all_success = false;
        }
    }
    
    return all_success;
}

bool SensorManager::publishSensorData() {
    if (!mqtt_client || !mqtt_client->isConnected()) {
        return false;
    }
    
    bool all_published = true;
    
    for (const auto& sensor : sensors) {
        if (!sensor->isInitialized()) {
            continue;
        }
        
        if (shouldPublishSensor(sensor->getType())) {
            if (publishSensorReading(sensor.get())) {
                updatePublishTimestamps(sensor->getType());
            } else {
                all_published = false;
            }
        }
    }
    
    return all_published;
}

bool SensorManager::calibrateSensor(SensorType type, const JsonArray& calibration_points) {
    BaseSensor* sensor = getSensor(type);
    if (!sensor) {
        Logger::error("Sensor not found for calibration", "SensorManager");
        return false;
    }
    
    if (sensor->calibrate(calibration_points)) {
        Logger::info("Sensor calibration successful", "SensorManager");
        return true;
    } else {
        Logger::error("Sensor calibration failed", "SensorManager");
        return false;
    }
}

DynamicJsonDocument SensorManager::getStatusJson() const {
    DynamicJsonDocument doc(1024);
    
    doc["initialized"] = initialized;
    doc["sensor_count"] = sensors.size();
    doc["all_healthy"] = areAllSensorsHealthy();
    
    JsonArray sensor_array = doc.createNestedArray("sensors");
    
    for (const auto& sensor : sensors) {
        JsonObject sensor_obj = sensor_array.createNestedObject();
        sensor_obj["type"] = (int)sensor->getType();
        sensor_obj["initialized"] = sensor->isInitialized();
        sensor_obj["healthy"] = sensor->isHealthy();
        
        if (sensor->isInitialized()) {
            const SensorReading& reading = sensor->getLastReading();
            sensor_obj["last_reading_timestamp"] = reading.timestamp;
            sensor_obj["quality"] = reading.quality;
            sensor_obj["calibration_valid"] = reading.calibration_valid;
        }
    }
    
    JsonObject publish_rates = doc.createNestedObject("publish_rates");
    publish_rates["ph_hz"] = ph_publish_rate_hz;
    publish_rates["tds_hz"] = tds_publish_rate_hz;
    
    return doc;
}

bool SensorManager::areAllSensorsHealthy() const {
    for (const auto& sensor : sensors) {
        if (sensor->isInitialized() && !sensor->isHealthy()) {
            return false;
        }
    }
    
    return true;
}

bool SensorManager::shouldPublishSensor(SensorType type) const {
    unsigned long current_time = millis();
    unsigned long interval_ms;
    unsigned long last_publish;
    
    switch (type) {
        case SensorType::PH:
            interval_ms = (unsigned long)(1000.0 / ph_publish_rate_hz);
            last_publish = last_ph_publish;
            break;
        case SensorType::TDS:
            interval_ms = (unsigned long)(1000.0 / tds_publish_rate_hz);
            last_publish = last_tds_publish;
            break;
        default:
            return false;
    }
    
    return (current_time - last_publish) >= interval_ms;
}

void SensorManager::updatePublishTimestamps(SensorType type) {
    unsigned long current_time = millis();
    
    switch (type) {
        case SensorType::PH:
            last_ph_publish = current_time;
            break;
        case SensorType::TDS:
            last_tds_publish = current_time;
            break;
    }
}

bool SensorManager::publishSensorReading(BaseSensor* sensor) {
    if (!sensor || !mqtt_client) {
        return false;
    }
    
    const SensorReading& reading = sensor->getLastReading();
    
    return mqtt_client->publishSensorData(sensor->getType(), reading);
}

void SensorManager::initializeSensors(const Config& config) {
    // pH-Sensor initialisieren
    if (config.ph_sensor.enabled) {
        std::unique_ptr<PHSensor> ph_sensor(new PHSensor());
        if (ph_sensor->init(config.ph_sensor)) {
            addSensor(std::move(ph_sensor));
        } else {
            Logger::error("Failed to initialize pH sensor", "SensorManager");
        }
    }
    
    // TDS-Sensor initialisieren
    if (config.tds_sensor.enabled) {
        std::unique_ptr<TDSSensor> tds_sensor(new TDSSensor());
        if (tds_sensor->init(config.tds_sensor)) {
            addSensor(std::move(tds_sensor));
        } else {
            Logger::error("Failed to initialize TDS sensor", "SensorManager");
        }
    }
} 