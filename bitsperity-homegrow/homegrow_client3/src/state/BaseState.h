#ifndef BASE_STATE_H
#define BASE_STATE_H

#include "../core/Types.h"
#include "../core/Logger.h"
#include <ArduinoJson.h>

// Forward-Deklaration
class Application;

class BaseState {
protected:
    Application* app;
    SystemState state_type;
    unsigned long enter_time;
    
public:
    BaseState(Application* application, SystemState type);
    virtual ~BaseState() = default;
    
    virtual void enter() = 0;
    virtual void exit() = 0;
    virtual void update() = 0;
    virtual void handleEvent(const String& event, const JsonObject& data) = 0;
    
    SystemState getType() const { return state_type; }
    unsigned long getUptime() const;
    
    // Status für Monitoring
    virtual DynamicJsonDocument getStatusJson() const;
    
    // Hilfsfunktion
    static String getStateName(SystemState state);
    
protected:
    void logStateEvent(const String& event, const String& message = "");
    bool shouldTimeout(unsigned long timeout_ms) const;
};

#endif // BASE_STATE_H 