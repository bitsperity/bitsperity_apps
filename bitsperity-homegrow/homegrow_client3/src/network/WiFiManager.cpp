#include "WiFiManager.h"

// Statische Instanz für Event-Handler
static WiFiManager* wifiManagerInstance = nullptr;

WiFiManager::WiFiManager() : 
    status(WiFiStatus::DISCONNECTED),
    last_connection_attempt(0),
    connection_attempts(0) {
    wifiManagerInstance = this;
}

bool WiFiManager::init(const WiFiConfig& wifi_config) {
    config = wifi_config;
    
    Logger::info("Initializing WiFi Manager", "WiFi");
    Logger::info("SSID: " + config.ssid, "WiFi");
    Logger::info("Hostname: " + config.hostname, "WiFi");
    
    // WiFi-Events registrieren
    WiFi.onEvent(WiFiEventHandler);
    
    // WiFi-Modus setzen
    WiFi.mode(WIFI_STA);
    WiFi.setHostname(config.hostname.c_str());
    
    // Statische IP wenn konfiguriert
    if (!config.static_ip.isEmpty()) {
        IPAddress ip, gateway, subnet, dns1, dns2;
        if (ip.fromString(config.static_ip)) {
            // Standard-Gateway und Subnet annehmen
            gateway = IPAddress(ip[0], ip[1], ip[2], 1);
            subnet = IPAddress(255, 255, 255, 0);
            
            if (!config.dns_servers[0].isEmpty()) {
                dns1.fromString(config.dns_servers[0]);
            }
            if (!config.dns_servers[1].isEmpty()) {
                dns2.fromString(config.dns_servers[1]);
            }
            
            WiFi.config(ip, gateway, subnet, dns1, dns2);
            Logger::info("Static IP configured: " + config.static_ip, "WiFi");
        }
    }
    
    return true;
}

bool WiFiManager::connect() {
    if (config.ssid.isEmpty()) {
        Logger::error("WiFi SSID not configured", "WiFi");
        status = WiFiStatus::FAILED;
        return false;
    }
    
    if (status == WiFiStatus::CONNECTING) {
        Logger::debug("Already connecting to WiFi", "WiFi");
        return false;
    }
    
    Logger::info("Connecting to WiFi: " + config.ssid, "WiFi");
    status = WiFiStatus::CONNECTING;
    connection_attempts++;
    last_connection_attempt = millis();
    
    WiFi.begin(config.ssid.c_str(), config.password.c_str());
    
    // Auf Verbindung warten (mit Timeout)
    unsigned long start_time = millis();
    while (WiFi.status() != WL_CONNECTED && 
           millis() - start_time < CONNECTION_TIMEOUT) {
        delay(100);
        
        // Logging alle 2 Sekunden
        if ((millis() - start_time) % 2000 < 100) {
            Logger::debug("Connecting... " + String((millis() - start_time) / 1000) + "s", "WiFi");
        }
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        status = WiFiStatus::CONNECTED;
        connection_attempts = 0;
        Logger::info("WiFi connected successfully", "WiFi");
        Logger::info("IP Address: " + WiFi.localIP().toString(), "WiFi");
        Logger::info("RSSI: " + String(WiFi.RSSI()) + " dBm", "WiFi");
        return true;
    } else {
        status = WiFiStatus::FAILED;
        Logger::error("WiFi connection failed after " + String(CONNECTION_TIMEOUT/1000) + "s", "WiFi");
        
        if (connection_attempts >= MAX_CONNECTION_ATTEMPTS) {
            Logger::error("Max connection attempts reached. Restarting...", "WiFi");
            delay(1000);
            ESP.restart();
        }
        
        return false;
    }
}

bool WiFiManager::isConnected() const {
    return WiFi.status() == WL_CONNECTED && status == WiFiStatus::CONNECTED;
}

int WiFiManager::getRSSI() const {
    if (isConnected()) {
        return WiFi.RSSI();
    }
    return -100;
}

String WiFiManager::getIP() const {
    if (isConnected()) {
        return WiFi.localIP().toString();
    }
    return "0.0.0.0";
}

String WiFiManager::getMAC() const {
    return WiFi.macAddress();
}

String WiFiManager::getSSID() const {
    if (isConnected()) {
        return WiFi.SSID();
    }
    return "";
}

void WiFiManager::handleDisconnection() {
    if (status == WiFiStatus::CONNECTED) {
        status = WiFiStatus::DISCONNECTED;
        Logger::warn("WiFi disconnected", "WiFi");
    }
}

bool WiFiManager::shouldReconnect() const {
    if (status == WiFiStatus::DISCONNECTED || status == WiFiStatus::FAILED) {
        return millis() - last_connection_attempt > RECONNECT_INTERVAL;
    }
    return false;
}

void WiFiManager::loop() {
    // Automatische Wiederverbindung
    if (shouldReconnect()) {
        Logger::info("Attempting WiFi reconnection...", "WiFi");
        connect();
    }
    
    // Status-Update
    if (status == WiFiStatus::CONNECTED && WiFi.status() != WL_CONNECTED) {
        handleDisconnection();
    }
}

DynamicJsonDocument WiFiManager::getStatusJson() const {
    DynamicJsonDocument doc(256);
    
    doc["connected"] = isConnected();
    doc["ssid"] = getSSID();
    doc["ip"] = getIP();
    doc["mac"] = getMAC();
    doc["rssi"] = getRSSI();
    doc["quality"] = getRSSI() > -50 ? "excellent" : 
                     getRSSI() > -60 ? "good" : 
                     getRSSI() > -70 ? "fair" : "poor";
    doc["connection_attempts"] = connection_attempts;
    
    return doc;
}

void WiFiManager::onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
    switch (event) {
        case ARDUINO_EVENT_WIFI_STA_GOT_IP:
            Logger::info("WiFi got IP: " + WiFi.localIP().toString(), "WiFi");
            status = WiFiStatus::CONNECTED;
            break;
            
        case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
            Logger::warn("WiFi disconnected", "WiFi");
            handleDisconnection();
            break;
            
        case ARDUINO_EVENT_WIFI_STA_LOST_IP:
            Logger::warn("WiFi lost IP", "WiFi");
            break;
            
        default:
            break;
    }
}

void WiFiManager::WiFiEventHandler(WiFiEvent_t event, WiFiEventInfo_t info) {
    if (wifiManagerInstance) {
        wifiManagerInstance->onWiFiEvent(event, info);
    }
} 