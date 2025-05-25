#ifndef INIT_STATE_H
#define INIT_STATE_H

#include "BaseState.h"

class InitState : public BaseState {
private:
    bool config_loaded;
    bool logger_initialized;
    bool components_initialized;
    
    static const unsigned long INIT_TIMEOUT_MS = 10000; // 10 Sekunden
    
public:
    InitState(Application* app);
    
    void enter() override;
    void exit() override;
    void update() override;
    void handleEvent(const String& event, const JsonObject& data) override;
    
private:
    bool initializeComponents();
    bool loadConfiguration();
    bool initializeLogger();
    bool initializeManagers();
};

#endif // INIT_STATE_H 