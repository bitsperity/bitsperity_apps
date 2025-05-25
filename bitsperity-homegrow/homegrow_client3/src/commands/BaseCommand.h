#ifndef BASE_COMMAND_H
#define BASE_COMMAND_H

#include "../core/Types.h"
#include "../core/Logger.h"
#include <ArduinoJson.h>

class BaseCommand {
protected:
    String command_id;
    String command_type;
    DynamicJsonDocument params{512};
    CommandStatus status;
    String error_message;
    DynamicJsonDocument result_data{512};
    unsigned long start_time;
    unsigned long execution_time_ms;
    
public:
    BaseCommand(const String& cmd_id, const String& cmd_type);
    virtual ~BaseCommand() = default;
    
    virtual bool validate(const JsonObject& parameters) = 0;
    virtual bool execute() = 0;
    virtual void abort() = 0;
    
    // Getters
    String getCommandId() const { return command_id; }
    String getCommandType() const { return command_type; }
    CommandStatus getStatus() const { return status; }
    String getErrorMessage() const { return error_message; }
    
    // Result
    CommandResult getResult() const;
    JsonObject getResultData();
    
protected:
    void setStatus(CommandStatus new_status);
    void setError(const String& error);
    void setResultData(const JsonObject& data);
    void logCommandStart();
    void logCommandEnd();
    
    // Hilfsmethoden für Parameter-Validierung
    bool hasParam(const String& key) const;
    bool getStringParam(const String& key, String& value) const;
    bool getFloatParam(const String& key, float& value) const;
    bool getIntParam(const String& key, int& value) const;
    bool getBoolParam(const String& key, bool& value) const;
};

#endif // BASE_COMMAND_H 