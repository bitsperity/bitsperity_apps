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

from mqtt_connection_manager import MQTTConnectionManager
from mqtt_tools import MQTTTools

# Configure logging für development + production
log_handlers = [logging.StreamHandler(sys.stderr)]

# Only add file handler if directory exists (production)
if os.path.exists('/app/logs'):
    log_handlers.append(logging.FileHandler('/app/logs/mcp-server.log'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)


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
        
        # Phase 3: Register all 7 tools
        self.tools = {
            # Phase 1: Session Management Tools ✅
            'establish_connection': self.mqtt_tools.establish_connection,
            'list_active_connections': self.mqtt_tools.list_active_connections,
            'close_connection': self.mqtt_tools.close_connection,
            
            # Phase 2: MQTT Core Tools ✅
            'list_topics': self.mqtt_tools.list_topics,
            'subscribe_and_collect': self.mqtt_tools.subscribe_and_collect,
            'publish_message': self.mqtt_tools.publish_message,
            
            # Phase 3: Data Optimization Tools 🚀
            'get_topic_schema': self.mqtt_tools.get_topic_schema,
            
            # Phase 4: Advanced Tools (future)
            'debug_device': self.mqtt_tools.debug_device,
            'monitor_performance': self.mqtt_tools.monitor_performance,
            'test_connection': self.mqtt_tools.test_connection
        }
        
        logger.info(f"SimpleMCPServer initialized with {len(self.tools)} tools (Phase 3)")
    
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
            
            # Tool execution
            if method in self.tools:
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
        logger.info("MCP Server starting - Phase 3")
        
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
                    
                    # Send JSON response to STDOUT
                    response_json = json.dumps(response)
                    print(response_json, flush=True)
                    logger.debug(f"Sent response: {response}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    error_response = self._error_response(None, -32700, "Parse error")
                    print(json.dumps(error_response), flush=True)
                    
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down MCP Server")
        await self.connection_manager.cleanup_all_sessions()
        logger.info("MCP Server shutdown complete")


async def main():
    """Main entry point"""
    server = SimpleMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 