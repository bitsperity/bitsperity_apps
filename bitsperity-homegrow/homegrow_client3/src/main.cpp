#include <Arduino.h>
#include "core/Logger.h"
#include "config/Config.h"
#include "network/WiFiManager.h"
#include "network/MQTTClient.h"
#include "network/MDNSDiscovery.h"

// Globale Objekte
Config config;
WiFiManager wifiManager;
MQTTClient mqttClient;
MDNSDiscovery mdnsDiscovery;

// WiFi-Credentials (später aus Konfiguration)
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// MQTT-Callback
void handleMQTTMessage(String topic, String payload) {
    Logger::info("MQTT Message: " + topic, "Main");
    
    // Hier später Command-Processing
    if (topic.endsWith("/commands")) {
        Logger::info("Command received: " + payload, "Main");
        // TODO: Command-Processor aufrufen
    } else if (topic.endsWith("/config/response")) {
        Logger::info("Config received: " + payload, "Main");
        // TODO: Config updaten
    }
}

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    Serial.println("\n\n=================================");
    Serial.println("HomeGrow Client v3 Starting...");
    Serial.println("=================================\n");
    
    // Logger initialisieren
    Logger::init("homegrow_client_001", LogLevel::DEBUG);
    Logger::info("System starting...", "Main");
    
    // Konfiguration laden
    Logger::info("Loading configuration...", "Main");
    if (!config.loadDefaults()) {
        Logger::error("Failed to load default configuration", "Main");
        return;
    }
    
    // WiFi-Credentials setzen (temporär)
    config.wifi.ssid = WIFI_SSID;
    config.wifi.password = WIFI_PASSWORD;
    
    // Konfiguration validieren
    if (!config.validate()) {
        Logger::error("Configuration validation failed", "Main");
        return;
    }
    
    Logger::info("Configuration loaded successfully", "Main");
    
    // WiFi initialisieren
    if (!wifiManager.init(config.wifi)) {
        Logger::error("Failed to initialize WiFi", "Main");
        return;
    }
    
    // WiFi verbinden
    if (!wifiManager.connect()) {
        Logger::error("Failed to connect to WiFi", "Main");
        return;
    }
    
    // mDNS initialisieren
    if (!mdnsDiscovery.init(config.wifi.hostname)) {
        Logger::warn("Failed to initialize mDNS", "Main");
    }
    
    // MQTT initialisieren
    if (!mqttClient.init(config.mqtt, config.device_id)) {
        Logger::error("Failed to initialize MQTT", "Main");
        return;
    }
    
    // MQTT-Callback setzen
    mqttClient.setMessageCallback(handleMQTTMessage);
    
    // MQTT-Broker finden und verbinden
    String broker_host = config.mqtt.fallback_host;
    int broker_port = config.mqtt.fallback_port;
    
    if (config.mqtt.broker_discovery_enabled) {
        Logger::info("Searching for MQTT broker via mDNS...", "Main");
        BrokerInfo broker = mdnsDiscovery.discoverBroker(config.mqtt.service_name);
        
        if (broker.found) {
            broker_host = broker.host;
            broker_port = broker.port;
            Logger::info("Using discovered broker", "Main");
        } else {
            Logger::warn("Using fallback broker", "Main");
        }
    }
    
    // MQTT verbinden
    if (!mqttClient.connect(broker_host, broker_port)) {
        Logger::error("Failed to connect to MQTT broker", "Main");
        // Trotzdem weitermachen, wird in loop() erneut versucht
    }
    
    // Logger mit MQTT verbinden
    Logger::setMQTTClient(&mqttClient);
    Logger::setMQTTEnabled(true);
    
    // System-Info ausgeben
    Logger::info("=== System Information ===", "Main");
    Logger::info("Device ID: " + config.device_id, "Main");
    Logger::info("Device Name: " + config.device_name, "Main");
    Logger::info("Firmware Version: " + config.firmware_version, "Main");
    Logger::info("Free Heap: " + String(ESP.getFreeHeap()) + " bytes", "Main");
    Logger::info("Total Heap: " + String(ESP.getHeapSize()) + " bytes", "Main");
    Logger::info("Chip Model: " + String(ESP.getChipModel()), "Main");
    Logger::info("========================", "Main");
    
    Logger::info("System initialization complete", "Main");
}

void loop() {
    // WiFi-Manager loop
    wifiManager.loop();
    
    // MQTT-Client loop
    mqttClient.loop();
    
    // Heartbeat alle 30 Sekunden
    static unsigned long lastHeartbeat = 0;
    if (millis() - lastHeartbeat > 30000) {
        lastHeartbeat = millis();
        
        // Heartbeat-Daten sammeln
        DynamicJsonDocument heartbeat(512);
        heartbeat["timestamp"] = millis();
        heartbeat["uptime_sec"] = millis() / 1000;
        heartbeat["free_heap"] = ESP.getFreeHeap();
        
        // WiFi-Status
        JsonObject wifi = heartbeat.createNestedObject("wifi");
        wifi["connected"] = wifiManager.isConnected();
        wifi["rssi"] = wifiManager.getRSSI();
        wifi["ip"] = wifiManager.getIP();
        
        // MQTT-Status
        JsonObject mqtt = heartbeat.createNestedObject("mqtt");
        mqtt["connected"] = mqttClient.isConnected();
        DynamicJsonDocument mqttStats = mqttClient.getStatistics();
        mqtt["messages_sent"] = mqttStats["messages_sent"];
        mqtt["messages_failed"] = mqttStats["messages_failed"];
        
        // Heartbeat senden
        if (mqttClient.isConnected()) {
            mqttClient.publishHeartbeat(heartbeat);
        }
        
        Logger::debug("Heartbeat - Uptime: " + String(millis() / 1000) + "s", "Main");
        Logger::debug("Free Heap: " + String(ESP.getFreeHeap()) + " bytes", "Main");
    }
    
    // Simulierte Sensor-Daten (temporär für Tests)
    static unsigned long lastSensorRead = 0;
    if (millis() - lastSensorRead > 5000) { // Alle 5 Sekunden
        lastSensorRead = millis();
        
        // Simulierte pH-Messung
        SensorReading phReading;
        phReading.raw = 1721 + random(-50, 50); // Simulierter Rohwert
        phReading.calibrated = 7.0 + (float)random(-10, 10) / 100.0; // pH 6.9 - 7.1
        phReading.filtered = phReading.calibrated;
        phReading.timestamp = millis();
        phReading.quality = "good";
        phReading.calibration_valid = true;
        
        if (mqttClient.isConnected()) {
            mqttClient.publishSensorData(SensorType::PH, phReading);
        }
        
        // Simulierte TDS-Messung
        SensorReading tdsReading;
        tdsReading.raw = 1156 + random(-100, 100); // Simulierter Rohwert
        tdsReading.calibrated = 342 + random(-20, 20); // TDS 322 - 362
        tdsReading.filtered = tdsReading.calibrated;
        tdsReading.timestamp = millis();
        tdsReading.quality = "good";
        tdsReading.calibration_valid = true;
        
        if (mqttClient.isConnected()) {
            mqttClient.publishSensorData(SensorType::TDS, tdsReading);
        }
    }
    
    delay(10);
} 