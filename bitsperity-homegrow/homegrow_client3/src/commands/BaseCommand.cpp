#include "BaseCommand.h"

BaseCommand::BaseCommand(const String& cmd_id, const String& cmd_type) :
    command_id(cmd_id),
    command_type(cmd_type),
    status(CommandStatus::PENDING),
    start_time(0),
    execution_time_ms(0) {
}

CommandResult BaseCommand::getResult() const {
    CommandResult result;
    result.command_id = command_id;
    result.status = status;
    result.error_message = error_message;
    result.result_data = result_data;
    result.execution_time_ms = execution_time_ms;
    
    return result;
}

JsonObject BaseCommand::getResultData() {
    return result_data.to<JsonObject>();
}

void BaseCommand::setStatus(CommandStatus new_status) {
    status = new_status;
    
    if (status == CommandStatus::EXECUTING && start_time == 0) {
        start_time = millis();
        logCommandStart();
    } else if (status == CommandStatus::COMPLETED || status == CommandStatus::FAILED || status == CommandStatus::TIMEOUT) {
        if (start_time > 0) {
            execution_time_ms = millis() - start_time;
        }
        logCommandEnd();
    }
}

void BaseCommand::setError(const String& error) {
    error_message = error;
    setStatus(CommandStatus::FAILED);
    Logger::error("Command " + command_id + " failed: " + error, "BaseCommand");
}

void BaseCommand::setResultData(const JsonObject& data) {
    result_data.clear();
    result_data.set(data);
}

void BaseCommand::logCommandStart() {
    Logger::info("Command " + command_id + " (" + command_type + ") started", "BaseCommand");
}

void BaseCommand::logCommandEnd() {
    String status_str;
    switch (status) {
        case CommandStatus::COMPLETED:
            status_str = "completed";
            break;
        case CommandStatus::FAILED:
            status_str = "failed";
            break;
        case CommandStatus::TIMEOUT:
            status_str = "timeout";
            break;
        default:
            status_str = "unknown";
            break;
    }
    
    Logger::info("Command " + command_id + " " + status_str + " in " + 
                String(execution_time_ms) + " ms", "BaseCommand");
}

bool BaseCommand::hasParam(const String& key) const {
    return params.containsKey(key);
}

bool BaseCommand::getStringParam(const String& key, String& value) const {
    if (!hasParam(key)) {
        return false;
    }
    
    value = params[key] | "";
    return true;
}

bool BaseCommand::getFloatParam(const String& key, float& value) const {
    if (!hasParam(key)) {
        return false;
    }
    
    if (params[key].is<float>() || params[key].is<int>()) {
        value = params[key];
        return true;
    }
    
    return false;
}

bool BaseCommand::getIntParam(const String& key, int& value) const {
    if (!hasParam(key)) {
        return false;
    }
    
    if (params[key].is<int>()) {
        value = params[key];
        return true;
    }
    
    return false;
}

bool BaseCommand::getBoolParam(const String& key, bool& value) const {
    if (!hasParam(key)) {
        return false;
    }
    
    if (params[key].is<bool>()) {
        value = params[key];
        return true;
    }
    
    return false;
} 