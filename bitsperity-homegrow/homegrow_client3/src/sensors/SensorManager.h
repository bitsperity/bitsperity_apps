#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include "BaseSensor.h"
#include "PHSensor.h"
#include "TDSSensor.h"
#include "../network/MQTTClient.h"
#include "../config/Config.h"
#include <vector>
#include <memory>

class SensorManager {
private:
    std::vector<std::unique_ptr<BaseSensor>> sensors;
    MQTTClient* mqtt_client;
    
    // Publishing-Konfiguration
    float ph_publish_rate_hz;
    float tds_publish_rate_hz;
    unsigned long last_ph_publish;
    unsigned long last_tds_publish;
    
    bool initialized;
    
public:
    SensorManager();
    
    bool init(const Config& config, MQTTClient* mqtt);
    void loop();
    
    // Sensor-Management
    bool addSensor(std::unique_ptr<BaseSensor> sensor);
    BaseSensor* getSensor(SensorType type);
    
    // Datenerfassung
    bool readAllSensors();
    bool publishSensorData();
    
    // Kalibrierung
    bool calibrateSensor(SensorType type, const JsonArray& calibration_points);
    
    // Status für Heartbeat
    DynamicJsonDocument getStatusJson() const;
    bool areAllSensorsHealthy() const;
    bool isInitialized() const { return initialized; }
    
private:
    bool shouldPublishSensor(SensorType type) const;
    void updatePublishTimestamps(SensorType type);
    bool publishSensorReading(BaseSensor* sensor);
    void initializeSensors(const Config& config);
};

#endif // SENSOR_MANAGER_H 