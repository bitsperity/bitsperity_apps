#!/usr/bin/env python3
"""
bitsperity-mqtt-mcp - Simple MCP Server
Phase 1: JSON-RPC 2.0 MCP Protocol Server
Phase 2: Real MQTT Integration 
Phase 3: Simple Data Optimization

Implements 7 MQTT tools für AI-gestützte IoT device analysis:
- establish_connection, list_active_connections, close_connection (Phase 1)
- list_topics, subscribe_and_collect, publish_message (Phase 2)
- get_topic_schema (Phase 3)
"""

import sys
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os
import time

from mqtt_connection_manager import MQTTConnectionManager
from mqtt_tools import MQTTTools

# MongoDB für Tool Call Logging (analog zu MongoDB MCP)
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Configure logging für development + production
log_handlers = [logging.StreamHandler(sys.stderr)]

# Optional file handler if directory exists and is writable (production)
try:
    if os.path.exists('/app/logs'):
        # Test if we can write to the logs directory
        test_file = '/app/logs/.write_test'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        # If we can write, add file handler
        log_handlers.append(logging.FileHandler('/app/logs/mcp-server.log'))
        print("File logging enabled: /app/logs/mcp-server.log", file=sys.stderr)
    else:
        print("Logs directory not found - using STDERR only", file=sys.stderr)
except (PermissionError, OSError) as e:
    print(f"File logging disabled due to permissions: {e}", file=sys.stderr)
    print("Using STDERR logging only", file=sys.stderr)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# MongoDB Configuration for logging (reuse existing connection)
MONGODB_CONNECTION_STRING = "mongodb://umbrel:umbrel@bitsperity-mongodb_mongodb_1:27017/"
MONGODB_DATABASE = "mqtt_mcp_sessions"  # Same database as sessions
TOOL_CALLS_COLLECTION = "mcp_tool_calls"
SYSTEM_LOGS_COLLECTION = "mcp_system_logs"
PERFORMANCE_METRICS_COLLECTION = "mcp_performance_metrics"

class MQTTMCPLogger:
    """MongoDB logger for tool calls and system logs"""
    
    def __init__(self):
        self.mongodb_client = None
        self.db = None
        self._init_mongodb_connection()
    
    def _init_mongodb_connection(self):
        """Initialize MongoDB connection for logging"""
        try:
            self.mongodb_client = MongoClient(
                MONGODB_CONNECTION_STRING,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            
            # Test connection
            self.mongodb_client.admin.command('ping')
            
            # Get database
            self.db = self.mongodb_client[MONGODB_DATABASE]
            
            # Create TTL indexes for automatic cleanup
            # Tool calls: 24 hours
            self.db[TOOL_CALLS_COLLECTION].create_index(
                "timestamp",
                expireAfterSeconds=86400  # 24 hours
            )
            
            # System logs: 7 days  
            self.db[SYSTEM_LOGS_COLLECTION].create_index(
                "timestamp", 
                expireAfterSeconds=604800  # 7 days
            )
            
            # Performance metrics: 7 days
            self.db[PERFORMANCE_METRICS_COLLECTION].create_index(
                "timestamp",
                expireAfterSeconds=604800  # 7 days
            )
            
            logger.info("MongoDB logging connection established")
            
        except PyMongoError as e:
            logger.warning(f"MongoDB logging failed, tool calls won't be logged: {e}")
            self.mongodb_client = None
        except Exception as e:
            logger.warning(f"Unexpected error with MongoDB logging: {e}")
            self.mongodb_client = None
    
    def log_tool_call(self, tool_name: str, params: dict, success: bool, 
                     duration: float, result: dict = None, error: str = None):
        """Log tool call to MongoDB"""
        if not self.mongodb_client:
            return
            
        try:
            doc = {
                'timestamp': datetime.now(),
                'tool_name': tool_name,
                'params': params,
                'success': success,
                'duration_ms': round(duration * 1000, 2),
                'result_summary': str(result).get('success', False) if result else False,
                'error': error,
                'result_size_kb': round(len(str(result)) / 1024, 2) if result else 0
            }
            
            self.db[TOOL_CALLS_COLLECTION].insert_one(doc)
            
        except Exception as e:
            logger.error(f"Failed to log tool call: {e}")
    
    def log_system_event(self, event_type: str, message: str, level: str = "INFO", 
                        metadata: dict = None):
        """Log system event to MongoDB"""
        if not self.mongodb_client:
            return
            
        try:
            doc = {
                'timestamp': datetime.now(),
                'event_type': event_type,
                'level': level,
                'message': message,
                'metadata': metadata or {}
            }
            
            self.db[SYSTEM_LOGS_COLLECTION].insert_one(doc)
            
        except Exception as e:
            logger.error(f"Failed to log system event: {e}")
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "",
                              metadata: dict = None):
        """Log performance metric to MongoDB"""
        if not self.mongodb_client:
            return
            
        try:
            doc = {
                'timestamp': datetime.now(),
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                'metadata': metadata or {}
            }
            
            self.db[PERFORMANCE_METRICS_COLLECTION].insert_one(doc)
            
        except Exception as e:
            logger.error(f"Failed to log performance metric: {e}")

# Global logger instance
mqtt_logger = MQTTMCPLogger()

class SimpleMCPServer:
    """
    Simple MCP (Model Context Protocol) Server für MQTT Integration
    
    Implements JSON-RPC 2.0 protocol for MCP communication
    Phase 1: Basic session management ✅
    Phase 2: Real MQTT integration ✅  
    Phase 3: Simple data optimization 🚀
    """
    
    def __init__(self):
        """Initialize MCP Server"""
        self.connection_manager = MQTTConnectionManager()
        self.mqtt_tools = MQTTTools(self.connection_manager)
        
        # Phase 3: Register all 10 tools with unique MQTT prefixes
        self.tools = {
            # Phase 1: Session Management Tools ✅
            'mqtt_establish_connection': self.mqtt_tools.establish_connection,
            'mqtt_list_active_connections': self.mqtt_tools.list_active_connections,
            'mqtt_close_connection': self.mqtt_tools.close_connection,
            
            # Phase 2: MQTT Core Tools ✅
            'mqtt_list_topics': self.mqtt_tools.list_topics,
            'mqtt_subscribe_and_collect': self.mqtt_tools.subscribe_and_collect,
            'mqtt_publish_message': self.mqtt_tools.publish_message,
            
            # Phase 3: Data Optimization Tools 🚀
            'mqtt_get_topic_schema': self.mqtt_tools.get_topic_schema,
            
            # Phase 4: Advanced Tools
            'mqtt_debug_device': self.mqtt_tools.debug_device,
            'mqtt_monitor_performance': self.mqtt_tools.monitor_performance,
            'mqtt_test_connection': self.mqtt_tools.test_connection
        }
        
        # MCP Tool Definitions for discovery with unique names
        self.tool_definitions = {
            'mqtt_establish_connection': {
                'name': 'mqtt_establish_connection',
                'description': 'Establishes a new MQTT broker connection with session management',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'connection_string': {
                            'type': 'string',
                            'description': 'MQTT connection string (mqtt://[username:password@]broker:port[/client_id])'
                        }
                    },
                    'required': ['connection_string']
                }
            },
            'mqtt_list_active_connections': {
                'name': 'mqtt_list_active_connections',
                'description': 'Lists all currently active MQTT connections',
                'inputSchema': {
                    'type': 'object',
                    'properties': {}
                }
            },
            'mqtt_close_connection': {
                'name': 'mqtt_close_connection',
                'description': 'Closes an active MQTT connection and cleans up the session',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'session_id': {
                            'type': 'string',
                            'description': 'Session ID of the connection to close'
                        }
                    },
                    'required': ['session_id']
                }
            },
            'mqtt_list_topics': {
                'name': 'mqtt_list_topics',
                'description': 'Discovers available MQTT topics on the broker by subscribing to wildcard patterns',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'session_id': {
                            'type': 'string',
                            'description': 'Session ID of an active MQTT connection'
                        },
                        'pattern': {
                            'type': 'string',
                            'description': 'MQTT topic pattern for discovery (default: "#" for all topics)',
                            'default': '#'
                        }
                    },
                    'required': ['session_id']
                }
            },
            'mqtt_subscribe_and_collect': {
                'name': 'mqtt_subscribe_and_collect',
                'description': 'Subscribes to MQTT topic pattern and collects messages for a specified duration',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'session_id': {
                            'type': 'string',
                            'description': 'Session ID of an active MQTT connection'
                        },
                        'topic_pattern': {
                            'type': 'string',
                            'description': 'MQTT topic pattern to subscribe to'
                        },
                        'duration_seconds': {
                            'type': 'integer',
                            'description': 'How long to collect messages (10-300 seconds)',
                            'minimum': 10,
                            'maximum': 300,
                            'default': 30
                        }
                    },
                    'required': ['session_id', 'topic_pattern']
                }
            },
            'mqtt_publish_message': {
                'name': 'mqtt_publish_message',
                'description': 'Publishes a message to an MQTT topic with specified QoS and retain settings',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'session_id': {
                            'type': 'string',
                            'description': 'Session ID of an active MQTT connection'
                        },
                        'topic': {
                            'type': 'string',
                            'description': 'MQTT topic to publish to (no wildcards allowed)'
                        },
                        'payload': {
                            'type': 'string',
                            'description': 'Message payload as string'
                        },
                        'qos': {
                            'type': 'integer',
                            'description': 'Quality of Service level (0, 1, or 2)',
                            'enum': [0, 1, 2],
                            'default': 0
                        },
                        'retain': {
                            'type': 'boolean',
                            'description': 'Whether broker should retain message for new subscribers',
                            'default': False
                        }
                    },
                    'required': ['session_id', 'topic', 'payload']
                }
            },
            'mqtt_get_topic_schema': {
                'name': 'mqtt_get_topic_schema',
                'description': 'Analyzes message structures for a topic pattern to detect schema patterns',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'session_id': {
                            'type': 'string',
                            'description': 'Session ID of an active MQTT connection'
                        },
                        'topic_pattern': {
                            'type': 'string',
                            'description': 'MQTT topic pattern to analyze'
                        }
                    },
                    'required': ['session_id', 'topic_pattern']
                }
            },
            'mqtt_debug_device': {
                'name': 'mqtt_debug_device',
                'description': 'Device-specific monitoring and debugging for MQTT IoT devices',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'session_id': {
                            'type': 'string',
                            'description': 'Session ID of an active MQTT connection'
                        },
                        'device_id': {
                            'type': 'string',
                            'description': 'Device identifier to debug'
                        }
                    },
                    'required': ['session_id', 'device_id']
                }
            },
            'mqtt_monitor_performance': {
                'name': 'mqtt_monitor_performance',
                'description': 'Monitors MQTT connection and broker performance metrics',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'session_id': {
                            'type': 'string',
                            'description': 'Session ID of an active MQTT connection'
                        }
                    },
                    'required': ['session_id']
                }
            },
            'mqtt_test_connection': {
                'name': 'mqtt_test_connection',
                'description': 'Comprehensive connection health check and diagnostics for MQTT broker',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'session_id': {
                            'type': 'string',
                            'description': 'Session ID of an active MQTT connection'
                        }
                    },
                    'required': ['session_id']
                }
            }
        }
        
        logger.info(f"SimpleMCPServer initialized with {len(self.tools)} tools (Phase 4)")
        
        # Log server startup
        mqtt_logger.log_system_event("server_startup", "MQTT MCP Server starting", "INFO")
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSON-RPC 2.0 Request Handler
        
        Args:
            request: JSON-RPC 2.0 request
            
        Returns:
            JSON-RPC 2.0 response
        """
        request_id = request.get("id") if isinstance(request, dict) else None
        
        try:
            # Validate JSON-RPC 2.0 format
            if not isinstance(request, dict):
                return self._error_response(None, -32700, "Parse error")
            
            if request.get("jsonrpc") != "2.0":
                return self._error_response(request_id, -32600, "Invalid Request")
            
            method = request.get("method")
            params = request.get("params", {})
            
            if not method:
                return self._error_response(request_id, -32600, "Invalid Request")
            
            # Log API request
            mqtt_logger.log_system_event("api_request", f"Method: {method}", "INFO", 
                                       {"method": method, "request_id": request_id})
            
            # MCP Protocol methods
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "experimental": {},
                            "tools": {"listChanged": False}
                        },
                        "serverInfo": {
                            "name": "simple-mqtt-mcp",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "notifications/initialized":
                # Notifications should not have responses per JSON-RPC 2.0 spec
                logger.debug("Received initialized notification")
                # Return None to indicate no response should be sent
                return None
                
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "tools": list(self.tool_definitions.values())
                    },
                    "id": request_id
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_arguments = params.get("arguments", {})
                
                if tool_name in self.tools:
                    try:
                        start_time = time.time()
                        result = await self.tools[tool_name](**tool_arguments)
                        success = result.get('status') == 'success' if result else False
                        duration = time.time() - start_time
                        
                        # Log tool call to MongoDB
                        mqtt_logger.log_tool_call(tool_name, tool_arguments, success, duration, result)
                        
                        # Log performance metric
                        mqtt_logger.log_performance_metric(f"tool_call_{tool_name}_duration", duration, "seconds")
                        
                        return {
                            "jsonrpc": "2.0",
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(result, indent=2)
                                    }
                                ]
                            },
                            "id": request_id
                        }
                    except Exception as e:
                        logger.error(f"Tool execution error: {e}")
                        # Log failed tool call
                        duration = time.time() - start_time if 'start_time' in locals() else 0
                        mqtt_logger.log_tool_call(tool_name, tool_arguments, False, duration, None, str(e))
                        
                        return self._error_response(
                            request_id, -32000, f"Tool execution failed: {str(e)}"
                        )
                else:
                    return self._error_response(
                        request_id, -32601, f"Tool not found: {tool_name}"
                    )
            
            # Legacy direct tool calls (backward compatibility)
            elif method in self.tools:
                try:
                    result = await self.tools[method](**params)
                    return {
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": request_id
                    }
                except TypeError as e:
                    # Handle missing parameter errors
                    error_msg = str(e)
                    if "missing" in error_msg and "required" in error_msg:
                        logger.error(f"Missing parameter error: {e}")
                        return self._error_response(
                            request_id, -32602, f"Invalid params: {error_msg}"
                        )
                    else:
                        logger.error(f"Tool execution error: {e}")
                        return self._error_response(
                            request_id, -32000, f"Tool execution failed: {str(e)}"
                        )
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    return self._error_response(
                        request_id, -32000, f"Tool execution failed: {str(e)}"
                    )
            else:
                return self._error_response(
                    request_id, -32601, f"Method not found: {method}"
                )
                
        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return self._error_response(request_id, -32603, "Internal error")
    
    def _error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create JSON-RPC 2.0 error response"""
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            },
            "id": request_id
        }
    
    async def run(self):
        """
        Main server loop - STDIO communication
        
        Liest JSON-RPC requests von STDIN und sendet responses zu STDOUT
        """
        logger.info("MCP Server starting - Phase 4 with MongoDB Logging")
        mqtt_logger.log_system_event("server_start", "MQTT MCP Server started successfully", "INFO")
        
        try:
            while True:
                # Read line from STDIN
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse JSON request
                    request = json.loads(line)
                    logger.debug(f"Received request: {request}")
                    
                    # Handle request
                    response = await self.handle_request(request)
                    
                    # Send response to stdout (same as MongoDB MCP)
                    if response:
                        print(json.dumps(response), flush=True)
                        logger.debug(f"Sent response: {response}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    error_response = self._error_response(None, -32700, "Parse error")
                    print(json.dumps(error_response), flush=True)
                    
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
            mqtt_logger.log_system_event("server_shutdown", "Server shutdown requested", "INFO")
        except Exception as e:
            logger.error(f"Server error: {e}")
            mqtt_logger.log_system_event("server_error", f"Server error: {e}", "ERROR")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down MCP Server")
        mqtt_logger.log_system_event("server_shutdown", "MQTT MCP Server shutting down", "INFO")
        await self.connection_manager.cleanup_all_sessions()
        logger.info("MCP Server shutdown complete")


async def main():
    """Main entry point"""
    server = SimpleMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 