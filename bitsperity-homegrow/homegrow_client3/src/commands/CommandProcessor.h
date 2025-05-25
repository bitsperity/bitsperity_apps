#ifndef COMMAND_PROCESSOR_H
#define COMMAND_PROCESSOR_H

#include "BaseCommand.h"
#include "PumpCommand.h"
#include "DosingCommand.h"
#include "SystemCommand.h"
#include "../network/MQTTClient.h"
#include "../actuators/ActuatorManager.h"
#include "../sensors/SensorManager.h"
// #include "../config/ConfigManager.h" // TODO: Implement ConfigManager
#include <map>
#include <queue>
#include <memory>

class CommandProcessor {
private:
    std::map<String, std::unique_ptr<BaseCommand>> active_commands;
    std::queue<DynamicJsonDocument> command_queue;
    
    // Manager-Referenzen
    ActuatorManager* actuator_manager;
    SensorManager* sensor_manager;
    // ConfigManager* config_manager; // TODO: Implement ConfigManager
    MQTTClient* mqtt_client;
    
    // Command-Statistiken
    unsigned long commands_processed;
    unsigned long commands_failed;
    unsigned long commands_timeout;
    
    static const unsigned long COMMAND_TIMEOUT_MS = 60000; // 1 Minute
    static const size_t MAX_QUEUE_SIZE = 10;
    
    bool initialized;
    
public:
    CommandProcessor();
    
    bool init(ActuatorManager* actuator_mgr, SensorManager* sensor_mgr, 
              MQTTClient* mqtt);
    
    void loop();
    
    // Command-Verarbeitung
    bool processCommand(const String& command_json);
    bool queueCommand(const DynamicJsonDocument& command);
    void processCommandQueue();
    
    // Command-Management
    void abortCommand(const String& command_id);
    void abortAllCommands();
    void checkCommandTimeouts();
    
    // Status für Monitoring
    DynamicJsonDocument getStatusJson() const;
    bool isInitialized() const { return initialized; }
    
private:
    std::unique_ptr<BaseCommand> createCommand(const String& command_type, const String& command_id);
    bool validateCommandJson(const DynamicJsonDocument& command_doc) const;
    void publishCommandResponse(const CommandResult& result);
    void cleanupCompletedCommands();
    bool executeCommand(std::unique_ptr<BaseCommand> command, const JsonObject& params);
};

#endif // COMMAND_PROCESSOR_H 