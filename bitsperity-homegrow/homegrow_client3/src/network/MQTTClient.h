#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

#include <PubSubClient.h>
#include <WiFiClient.h>
#include "../config/Config.h"
#include "../core/Logger.h"
#include "../core/Types.h"
#include <functional>

class MQTTClient {
private:
    WiFiClient wifi_client;
    PubSubClient mqtt_client;
    MQTTConfig config;
    String device_id;
    
    bool connected;
    unsigned long last_connection_attempt;
    unsigned long last_heartbeat;
    unsigned long messages_sent;
    unsigned long messages_failed;
    
    // Topic-Templates
    String base_topic;
    String sensor_topic_template;
    String command_topic;
    String command_response_topic;
    String heartbeat_topic;
    String status_topic;
    String config_request_topic;
    String config_response_topic;
    String log_topic;
    
    // Callback-Funktionen
    std::function<void(String, String)> message_callback;
    
    // Statische Instanz für Callback
    static MQTTClient* instance;
    
public:
    MQTTClient();
    
    bool init(const MQTTConfig& mqtt_config, const String& device_id);
    bool connect(const String& broker_host, int broker_port);
    bool isConnected() const { return connected; }
    void disconnect();
    
    // Publishing
    bool publishSensorData(SensorType type, const SensorReading& reading);
    bool publishCommandResponse(const CommandResult& result);
    bool publishHeartbeat(const DynamicJsonDocument& heartbeat_data);
    bool publishStatus(const DynamicJsonDocument& status_data);
    bool publishLog(const DynamicJsonDocument& log_entry);
    bool requestConfig();
    
    // Subscription
    bool subscribeToCommands();
    bool subscribeToConfig();
    void setMessageCallback(std::function<void(String, String)> callback);
    
    // Maintenance
    void loop();
    bool shouldReconnect() const;
    void handleDisconnection();
    
    // Statistics für Heartbeat
    DynamicJsonDocument getStatistics() const;
    
private:
    void onMessage(char* topic, byte* payload, unsigned int length);
    static void mqttCallback(char* topic, byte* payload, unsigned int length);
    String buildTopic(const String& template_topic, const String& sensor_id = "") const;
    bool publish(const String& topic, const String& payload, bool retain = false);
    void setupTopics();
    bool reconnect();
};

#endif // MQTT_CLIENT_H 