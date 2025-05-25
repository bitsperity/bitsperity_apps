#include "MQTTClient.h"

// Statische Member-Initialisierung
MQTTClient* MQTTClient::instance = nullptr;

MQTTClient::MQTTClient() : 
    mqtt_client(wifi_client),
    connected(false),
    last_connection_attempt(0),
    last_heartbeat(0),
    messages_sent(0),
    messages_failed(0) {
    instance = this;
}

bool MQTTClient::init(const MQTTConfig& mqtt_config, const String& dev_id) {
    config = mqtt_config;
    device_id = dev_id;
    
    Logger::info("Initializing MQTT Client", "MQTT");
    Logger::info("Device ID: " + device_id, "MQTT");
    
    // MQTT-Client konfigurieren
    mqtt_client.setCallback(mqttCallback);
    mqtt_client.setKeepAlive(config.keepalive);
    mqtt_client.setBufferSize(1024); // Größerer Buffer für JSON-Payloads
    
    // Topics einrichten
    setupTopics();
    
    return true;
}

void MQTTClient::setupTopics() {
    base_topic = "homegrow/devices/" + device_id;
    sensor_topic_template = base_topic + "/sensors/";
    command_topic = base_topic + "/commands";
    command_response_topic = base_topic + "/commands/response";
    heartbeat_topic = base_topic + "/heartbeat";
    status_topic = base_topic + "/status";
    config_request_topic = base_topic + "/config/request";
    config_response_topic = base_topic + "/config/response";
    log_topic = base_topic + "/logs";
    
    Logger::debug("Base topic: " + base_topic, "MQTT");
}

bool MQTTClient::connect(const String& broker_host, int broker_port) {
    if (broker_host.isEmpty()) {
        Logger::error("Broker host is empty", "MQTT");
        return false;
    }
    
    Logger::info("Connecting to MQTT broker: " + broker_host + ":" + String(broker_port), "MQTT");
    
    // MQTT-Server setzen
    mqtt_client.setServer(broker_host.c_str(), broker_port);
    
    // Client-ID generieren
    String client_id = device_id + "_" + String(random(1000, 9999));
    
    // Verbindungsversuch
    bool result = false;
    if (config.username.isEmpty()) {
        result = mqtt_client.connect(client_id.c_str(), nullptr, nullptr, 
                                    status_topic.c_str(), config.qos, config.retain, 
                                    "{\"status\":\"offline\"}");
    } else {
        result = mqtt_client.connect(client_id.c_str(), 
                                    config.username.c_str(), 
                                    config.password.c_str(),
                                    status_topic.c_str(), config.qos, config.retain, 
                                    "{\"status\":\"offline\"}");
    }
    
    if (result) {
        connected = true;
        last_connection_attempt = millis();
        Logger::info("MQTT connected successfully", "MQTT");
        
        // Online-Status publizieren
        publish(status_topic, "{\"status\":\"online\"}", true);
        
        // Subscriptions
        subscribeToCommands();
        subscribeToConfig();
        
        return true;
    } else {
        connected = false;
        Logger::error("MQTT connection failed. Error code: " + String(mqtt_client.state()), "MQTT");
        return false;
    }
}

void MQTTClient::disconnect() {
    if (connected) {
        // Offline-Status publizieren
        publish(status_topic, "{\"status\":\"offline\"}", true);
        mqtt_client.disconnect();
        connected = false;
        Logger::info("MQTT disconnected", "MQTT");
    }
}

bool MQTTClient::subscribeToCommands() {
    if (!mqtt_client.connected()) return false;
    
    bool result = mqtt_client.subscribe(command_topic.c_str(), config.qos);
    if (result) {
        Logger::info("Subscribed to commands: " + command_topic, "MQTT");
    } else {
        Logger::error("Failed to subscribe to commands", "MQTT");
    }
    return result;
}

bool MQTTClient::subscribeToConfig() {
    if (!mqtt_client.connected()) return false;
    
    bool result = mqtt_client.subscribe(config_response_topic.c_str(), config.qos);
    if (result) {
        Logger::info("Subscribed to config: " + config_response_topic, "MQTT");
    } else {
        Logger::error("Failed to subscribe to config", "MQTT");
    }
    return result;
}

void MQTTClient::setMessageCallback(std::function<void(String, String)> callback) {
    message_callback = callback;
}

bool MQTTClient::publish(const String& topic, const String& payload, bool retain) {
    if (!mqtt_client.connected()) {
        messages_failed++;
        return false;
    }
    
    bool result = mqtt_client.publish(topic.c_str(), payload.c_str(), retain);
    
    if (result) {
        messages_sent++;
        Logger::debug("Published to " + topic + ": " + payload.substring(0, 100), "MQTT");
    } else {
        messages_failed++;
        Logger::error("Failed to publish to " + topic, "MQTT");
    }
    
    return result;
}

bool MQTTClient::publishSensorData(SensorType type, const SensorReading& reading) {
    String sensor_id = (type == SensorType::PH) ? "ph" : "tds";
    String topic = sensor_topic_template + sensor_id;
    
    DynamicJsonDocument doc(512);
    doc["timestamp"] = millis();
    doc["sensor_id"] = sensor_id;
    
    JsonObject values = doc.createNestedObject("values");
    values["raw"] = reading.raw;
    values["calibrated"] = reading.calibrated;
    values["filtered"] = reading.filtered;
    
    doc["unit"] = (type == SensorType::PH) ? "pH" : "ppm";
    doc["quality"] = reading.quality;
    doc["calibration_valid"] = reading.calibration_valid;
    
    String payload;
    serializeJson(doc, payload);
    
    return publish(topic, payload, false);
}

bool MQTTClient::publishCommandResponse(const CommandResult& result) {
    DynamicJsonDocument doc(512);
    doc["command_id"] = result.command_id;
    doc["status"] = static_cast<int>(result.status);
    doc["status_text"] = result.status == CommandStatus::COMPLETED ? "completed" :
                         result.status == CommandStatus::FAILED ? "failed" :
                         result.status == CommandStatus::TIMEOUT ? "timeout" : "unknown";
    
    if (!result.error_message.isEmpty()) {
        doc["error"] = result.error_message;
    }
    
    // Kopiere die result_data
    JsonObject resultObj = doc.createNestedObject("result");
    JsonObjectConst sourceObj = result.result_data.as<JsonObjectConst>();
    for (JsonPairConst kv : sourceObj) {
        resultObj[kv.key()] = kv.value();
    }
    
    doc["timestamp"] = millis();
    doc["execution_time_ms"] = result.execution_time_ms;
    
    String payload;
    serializeJson(doc, payload);
    
    return publish(command_response_topic, payload, false);
}

bool MQTTClient::publishHeartbeat(const DynamicJsonDocument& heartbeat_data) {
    last_heartbeat = millis();
    
    String payload;
    serializeJson(heartbeat_data, payload);
    
    return publish(heartbeat_topic, payload, false);
}

bool MQTTClient::publishStatus(const DynamicJsonDocument& status_data) {
    String payload;
    serializeJson(status_data, payload);
    
    return publish(status_topic, payload, true);
}

bool MQTTClient::publishLog(const DynamicJsonDocument& log_entry) {
    String payload;
    serializeJson(log_entry, payload);
    
    return publish(log_topic, payload, false);
}

bool MQTTClient::requestConfig() {
    DynamicJsonDocument doc(128);
    doc["device_id"] = device_id;
    doc["timestamp"] = millis();
    doc["request_type"] = "full_config";
    
    String payload;
    serializeJson(doc, payload);
    
    return publish(config_request_topic, payload, false);
}

void MQTTClient::loop() {
    if (!mqtt_client.connected()) {
        connected = false;
        if (shouldReconnect()) {
            reconnect();
        }
    } else {
        mqtt_client.loop();
    }
}

bool MQTTClient::shouldReconnect() const {
    return millis() - last_connection_attempt > 5000; // 5 Sekunden zwischen Versuchen
}

bool MQTTClient::reconnect() {
    Logger::info("Attempting MQTT reconnection...", "MQTT");
    
    // Gleiche Logik wie connect(), aber mit vorhandenen Einstellungen
    String client_id = device_id + "_" + String(random(1000, 9999));
    
    bool result = false;
    if (config.username.isEmpty()) {
        result = mqtt_client.connect(client_id.c_str(), nullptr, nullptr, 
                                    status_topic.c_str(), config.qos, config.retain, 
                                    "{\"status\":\"offline\"}");
    } else {
        result = mqtt_client.connect(client_id.c_str(), 
                                    config.username.c_str(), 
                                    config.password.c_str(),
                                    status_topic.c_str(), config.qos, config.retain, 
                                    "{\"status\":\"offline\"}");
    }
    
    if (result) {
        connected = true;
        last_connection_attempt = millis();
        Logger::info("MQTT reconnected successfully", "MQTT");
        
        // Online-Status publizieren
        publish(status_topic, "{\"status\":\"online\"}", true);
        
        // Subscriptions erneuern
        subscribeToCommands();
        subscribeToConfig();
        
        return true;
    } else {
        connected = false;
        last_connection_attempt = millis();
        Logger::error("MQTT reconnection failed", "MQTT");
        return false;
    }
}

void MQTTClient::handleDisconnection() {
    if (connected) {
        connected = false;
        Logger::warn("MQTT connection lost", "MQTT");
    }
}

DynamicJsonDocument MQTTClient::getStatistics() const {
    DynamicJsonDocument doc(256);
    
    doc["connected"] = connected;
    doc["messages_sent"] = messages_sent;
    doc["messages_failed"] = messages_failed;
    doc["last_heartbeat"] = last_heartbeat;
    doc["uptime"] = millis() - last_connection_attempt;
    
    return doc;
}

void MQTTClient::onMessage(char* topic, byte* payload, unsigned int length) {
    // Payload in String konvertieren
    String message;
    message.reserve(length);
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    
    String topic_str = String(topic);
    
    Logger::info("Message received on " + topic_str + ": " + message.substring(0, 100), "MQTT");
    
    // Callback aufrufen wenn gesetzt
    if (message_callback) {
        message_callback(topic_str, message);
    }
}

void MQTTClient::mqttCallback(char* topic, byte* payload, unsigned int length) {
    if (instance) {
        instance->onMessage(topic, payload, length);
    }
} 