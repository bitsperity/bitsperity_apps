#include "CommandProcessor.h"

CommandProcessor::CommandProcessor() :
    actuator_manager(nullptr),
    sensor_manager(nullptr),
    // config_manager(nullptr), // TODO: Implement ConfigManager
    mqtt_client(nullptr),
    commands_processed(0),
    commands_failed(0),
    commands_timeout(0),
    initialized(false) {
}

bool CommandProcessor::init(ActuatorManager* actuator_mgr, SensorManager* sensor_mgr, 
                           MQTTClient* mqtt) {
    if (!actuator_mgr || !sensor_mgr || !mqtt) {
        Logger::error("One or more managers are null", "CommandProcessor");
        return false;
    }
    
    actuator_manager = actuator_mgr;
    sensor_manager = sensor_mgr;
    // config_manager = config_mgr; // TODO: Implement ConfigManager
    mqtt_client = mqtt;
    
    initialized = true;
    
    Logger::info("CommandProcessor initialized successfully", "CommandProcessor");
    
    return true;
}

void CommandProcessor::loop() {
    if (!initialized) {
        return;
    }
    
    // Command-Queue verarbeiten
    processCommandQueue();
    
    // Timeouts prüfen
    checkCommandTimeouts();
    
    // Abgeschlossene Commands aufräumen
    cleanupCompletedCommands();
}

bool CommandProcessor::processCommand(const String& command_json) {
    DynamicJsonDocument command_doc(1024);
    DeserializationError error = deserializeJson(command_doc, command_json);
    
    if (error) {
        Logger::error("Failed to parse command JSON: " + String(error.c_str()), "CommandProcessor");
        return false;
    }
    
    return queueCommand(command_doc);
}

bool CommandProcessor::queueCommand(const DynamicJsonDocument& command) {
    if (!validateCommandJson(command)) {
        return false;
    }
    
    if (command_queue.size() >= MAX_QUEUE_SIZE) {
        Logger::error("Command queue is full", "CommandProcessor");
        return false;
    }
    
    command_queue.push(command);
    Logger::info("Command queued: " + command["command_id"].as<String>(), "CommandProcessor");
    
    return true;
}

void CommandProcessor::processCommandQueue() {
    while (!command_queue.empty()) {
        DynamicJsonDocument command_doc = command_queue.front();
        command_queue.pop();
        
        String command_id = command_doc["command_id"];
        String command_type = command_doc["command"];
        JsonObject params = command_doc["params"];
        
        // Command erstellen
        std::unique_ptr<BaseCommand> command = createCommand(command_type, command_id);
        if (!command) {
            Logger::error("Failed to create command: " + command_type, "CommandProcessor");
            commands_failed++;
            continue;
        }
        
        // Command ausführen
        if (executeCommand(std::move(command), params)) {
            commands_processed++;
        } else {
            commands_failed++;
        }
    }
}

void CommandProcessor::abortCommand(const String& command_id) {
    auto it = active_commands.find(command_id);
    if (it != active_commands.end()) {
        it->second->abort();
        Logger::info("Command " + command_id + " aborted", "CommandProcessor");
    }
}

void CommandProcessor::abortAllCommands() {
    Logger::info("Aborting all active commands", "CommandProcessor");
    
    for (auto& pair : active_commands) {
        pair.second->abort();
    }
}

void CommandProcessor::checkCommandTimeouts() {
    unsigned long current_time = millis();
    
    for (auto& pair : active_commands) {
        BaseCommand* command = pair.second.get();
        
        if (command->getStatus() == CommandStatus::EXECUTING) {
            // Prüfe Timeout (vereinfacht - sollte start_time aus Command verwenden)
            // Für jetzt nehmen wir an, dass Commands schnell ausgeführt werden
        }
    }
}

DynamicJsonDocument CommandProcessor::getStatusJson() const {
    DynamicJsonDocument doc(1024);
    
    doc["initialized"] = initialized;
    doc["active_commands"] = active_commands.size();
    doc["queue_size"] = command_queue.size();
    doc["commands_processed"] = commands_processed;
    doc["commands_failed"] = commands_failed;
    doc["commands_timeout"] = commands_timeout;
    
    JsonArray active_array = doc.createNestedArray("active_command_ids");
    for (const auto& pair : active_commands) {
        active_array.add(pair.first);
    }
    
    return doc;
}

std::unique_ptr<BaseCommand> CommandProcessor::createCommand(const String& command_type, const String& command_id) {
    if (command_type == "activate_pump") {
        return std::unique_ptr<BaseCommand>(new ActivatePumpCommand(command_id, actuator_manager));
    } else if (command_type == "stop_pump") {
        return std::unique_ptr<BaseCommand>(new StopPumpCommand(command_id, actuator_manager));
    } else if (command_type == "stop_all_pumps") {
        return std::unique_ptr<BaseCommand>(new StopAllPumpsCommand(command_id, actuator_manager));
    } else if (command_type == "dose_volume") {
        return std::unique_ptr<BaseCommand>(new DoseVolumeCommand(command_id, actuator_manager));
    } else if (command_type == "schedule_pump") {
        return std::unique_ptr<BaseCommand>(new SchedulePumpCommand(command_id, actuator_manager));
    } else if (command_type == "cancel_schedule") {
        return std::unique_ptr<BaseCommand>(new CancelScheduleCommand(command_id, actuator_manager));
    } else if (command_type == "adjust_ph_by") {
        return std::unique_ptr<BaseCommand>(new AdjustPHByCommand(command_id, actuator_manager, sensor_manager));
    } else if (command_type == "set_ph_target") {
        return std::unique_ptr<BaseCommand>(new SetPHTargetCommand(command_id, actuator_manager, sensor_manager));
    } else if (command_type == "adjust_tds_by") {
        return std::unique_ptr<BaseCommand>(new AdjustTDSByCommand(command_id, actuator_manager, sensor_manager));
    } else if (command_type == "set_tds_target") {
        return std::unique_ptr<BaseCommand>(new SetTDSTargetCommand(command_id, actuator_manager, sensor_manager));
    } else if (command_type == "emergency_stop") {
        return std::unique_ptr<BaseCommand>(new EmergencyStopCommand(command_id, actuator_manager));
    } else if (command_type == "clear_emergency_stop") {
        return std::unique_ptr<BaseCommand>(new ClearEmergencyStopCommand(command_id, actuator_manager));
    } else if (command_type == "calibrate_sensor") {
        return std::unique_ptr<BaseCommand>(new CalibrateSensorCommand(command_id, sensor_manager));
    } else if (command_type == "reset_system") {
        return std::unique_ptr<BaseCommand>(new ResetSystemCommand(command_id, actuator_manager));
    } else if (command_type == "get_system_status") {
        return std::unique_ptr<BaseCommand>(new GetSystemStatusCommand(command_id, actuator_manager, sensor_manager));
    }
    
    Logger::error("Unknown command type: " + command_type, "CommandProcessor");
    return nullptr;
}

bool CommandProcessor::validateCommandJson(const DynamicJsonDocument& command_doc) const {
    if (!command_doc.containsKey("command_id")) {
        Logger::error("Command missing command_id", "CommandProcessor");
        return false;
    }
    
    if (!command_doc.containsKey("command")) {
        Logger::error("Command missing command type", "CommandProcessor");
        return false;
    }
    
    if (!command_doc.containsKey("params")) {
        Logger::error("Command missing params", "CommandProcessor");
        return false;
    }
    
    String command_id = command_doc["command_id"];
    if (command_id.length() == 0) {
        Logger::error("Command ID is empty", "CommandProcessor");
        return false;
    }
    
    // Prüfe ob Command bereits aktiv ist
    if (active_commands.find(command_id) != active_commands.end()) {
        Logger::error("Command " + command_id + " is already active", "CommandProcessor");
        return false;
    }
    
    return true;
}

void CommandProcessor::publishCommandResponse(const CommandResult& result) {
    if (!mqtt_client || !mqtt_client->isConnected()) {
        return;
    }
    
    mqtt_client->publishCommandResponse(result);
}

void CommandProcessor::cleanupCompletedCommands() {
    auto it = active_commands.begin();
    while (it != active_commands.end()) {
        CommandStatus status = it->second->getStatus();
        
        if (status == CommandStatus::COMPLETED || 
            status == CommandStatus::FAILED || 
            status == CommandStatus::TIMEOUT) {
            
            // Response publizieren
            publishCommandResponse(it->second->getResult());
            
            // Command entfernen
            it = active_commands.erase(it);
        } else {
            ++it;
        }
    }
}

bool CommandProcessor::executeCommand(std::unique_ptr<BaseCommand> command, const JsonObject& params) {
    String command_id = command->getCommandId();
    
    // Validierung
    if (!command->validate(params)) {
        Logger::error("Command validation failed: " + command_id, "CommandProcessor");
        publishCommandResponse(command->getResult());
        return false;
    }
    
    // Command zu aktiven Commands hinzufügen
    active_commands[command_id] = std::move(command);
    
    // Ausführung
    if (active_commands[command_id]->execute()) {
        Logger::info("Command executed successfully: " + command_id, "CommandProcessor");
        return true;
    } else {
        Logger::error("Command execution failed: " + command_id, "CommandProcessor");
        return false;
    }
} 