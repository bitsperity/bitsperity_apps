#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#include "BaseState.h"
#include "../core/Types.h"
#include "../core/Logger.h"
#include <memory>

// Forward-Deklaration
class Application;

class StateMachine {
private:
    std::unique_ptr<BaseState> current_state;
    SystemState current_state_type;
    Application* app;
    unsigned long state_start_time;
    unsigned long total_state_transitions;
    
public:
    StateMachine(Application* application);
    
    void init();
    void update();
    void transition(SystemState new_state);
    
    SystemState getCurrentStateType() const { return current_state_type; }
    BaseState* getCurrentState() const { return current_state.get(); }
    unsigned long getStateUptime() const;
    
    // Event-Handling
    void handleEvent(const String& event, const JsonObject& data = JsonObject());
    
    // Status für Monitoring
    DynamicJsonDocument getStatusJson() const;
    
private:
    std::unique_ptr<BaseState> createState(SystemState state_type);
    void logStateTransition(SystemState from, SystemState to);
};

#endif // STATE_MACHINE_H 