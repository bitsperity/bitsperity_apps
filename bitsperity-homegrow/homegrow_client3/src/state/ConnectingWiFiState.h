#ifndef CONNECTING_WIFI_STATE_H
#define CONNECTING_WIFI_STATE_H

#include "BaseState.h"

class ConnectingWiFiState : public BaseState {
private:
    int connection_attempts;
    unsigned long last_attempt_time;
    
    static const int MAX_ATTEMPTS = 5;
    static const unsigned long ATTEMPT_INTERVAL_MS = 5000; // 5 Sekunden
    static const unsigned long CONNECTION_TIMEOUT_MS = 30000; // 30 Sekunden
    
public:
    ConnectingWiFiState(Application* app);
    
    void enter() override;
    void exit() override;
    void update() override;
    void handleEvent(const String& event, const JsonObject& data) override;
    
private:
    bool attemptConnection();
    bool shouldRetry() const;
    void handleConnectionFailure();
};

#endif // CONNECTING_WIFI_STATE_H 