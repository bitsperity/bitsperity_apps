#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>
#include <esp_wifi.h>
#include "../config/Config.h"
#include "../core/Logger.h"

enum class WiFiStatus {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    FAILED
};

class WiFiManager {
private:
    WiFiConfig config;
    WiFiStatus status;
    unsigned long last_connection_attempt;
    int connection_attempts;
    static const int MAX_CONNECTION_ATTEMPTS = 5;
    static const unsigned long CONNECTION_TIMEOUT = 10000; // 10 Sekunden
    static const unsigned long RECONNECT_INTERVAL = 5000; // 5 Sekunden
    
public:
    WiFiManager();
    
    bool init(const WiFiConfig& wifi_config);
    bool connect();
    bool isConnected() const;
    WiFiStatus getStatus() const { return status; }
    
    // Monitoring
    int getRSSI() const;
    String getIP() const;
    String getMAC() const;
    String getSSID() const;
    
    // Reconnection
    void handleDisconnection();
    bool shouldReconnect() const;
    void loop();
    
    // Status für Heartbeat
    DynamicJsonDocument getStatusJson() const;
    
private:
    void configureWiFi();
    void onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info);
    static void WiFiEventHandler(WiFiEvent_t event, WiFiEventInfo_t info);
};

#endif // WIFI_MANAGER_H 