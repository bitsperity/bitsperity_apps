#!/usr/bin/env python3
"""
Simple MongoDB MCP Server without Pydantic types.
"""

import asyncio
import json
import logging
import os
import sys
import time
import aiohttp
from pathlib import Path

from connection_manager import ConnectionManager
from mongodb_tools import MongoDBTools

# Configure logging
log_file = Path(os.getenv('DATA_DIR', './data')) / 'logs' / 'simple-mcp.log'

# Try to create log directory, but don't fail if not possible
try:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    # File logging if possible
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file)]
    )
except (PermissionError, OSError) as e:
    # Fallback to console logging only
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

logger = logging.getLogger(__name__)

# Web API logging
WEB_API_URL = os.getenv('WEB_API_URL', 'http://web:8080')

async def log_to_web_api(method: str, params: dict, success: bool, duration: float, result=None, error=None):
    """Log MCP call to the web API for frontend display."""
    try:
        call_data = {
            "method": method,
            "params": params,
            "success": success,
            "duration": duration,
            "result": result,
            "error": error
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{WEB_API_URL}/api/log-call", json=call_data, timeout=1) as response:
                if response.status == 200:
                    logger.debug(f"Logged call {method} to web API")
                else:
                    logger.warning(f"Failed to log to web API: {response.status}")
    except Exception as e:
        logger.debug(f"Could not log to web API: {e}")
        # Don't fail MCP operations if web logging fails

class SimpleMCPServer:
    """Simple MCP Server with direct JSON-RPC communication."""
    
    def __init__(self):
        self.connection_manager = ConnectionManager(
            session_ttl=int(os.getenv('SESSION_TTL', '3600')),
            max_connections=int(os.getenv('MAX_CONNECTIONS', '10'))
        )
        self.mongodb_tools = MongoDBTools(self.connection_manager)
    
    async def handle_request(self, request_data):
        """Handle a single MCP request."""
        try:
            request = json.loads(request_data)
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            logger.info(f"Handling request: {method}")
            
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
                            "name": "simple-mongodb-mcp",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "notifications/initialized":
                # No response needed for notifications
                return None
            
            elif method == "tools/list":
                tools = [
                    {
                        "name": "establish_connection",
                        "description": "Establish a connection to a MongoDB instance",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "connection_string": {
                                    "type": "string",
                                    "description": "MongoDB connection string"
                                }
                            },
                            "required": ["connection_string"]
                        }
                    },
                    {
                        "name": "list_databases",
                        "description": "List all databases for a connection session",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Connection session ID"}
                            },
                            "required": ["session_id"]
                        }
                    },
                    {
                        "name": "list_collections",
                        "description": "List all collections in a database",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Connection session ID"},
                                "database_name": {"type": "string", "description": "Name of the database"}
                            },
                            "required": ["session_id", "database_name"]
                        }
                    },
                    {
                        "name": "query_collection",
                        "description": "Query a collection with find operation",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Connection session ID"},
                                "database_name": {"type": "string", "description": "Name of the database"},
                                "collection_name": {"type": "string", "description": "Name of the collection"},
                                "query": {"type": "object", "description": "MongoDB query filter"},
                                "limit": {"type": "integer", "description": "Maximum documents to return", "default": 10},
                                "projection": {"type": "object", "description": "Fields to include/exclude"},
                                "sort": {"type": "object", "description": "Sort specification"}
                            },
                            "required": ["session_id", "database_name", "collection_name"]
                        }
                    },
                    {
                        "name": "get_sample_documents",
                        "description": "Get sample documents from a collection",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Connection session ID"},
                                "database_name": {"type": "string", "description": "Name of the database"},
                                "collection_name": {"type": "string", "description": "Name of the collection"},
                                "limit": {"type": "integer", "description": "Number of sample documents", "default": 5}
                            },
                            "required": ["session_id", "database_name", "collection_name"]
                        }
                    },
                    {
                        "name": "get_collection_schema",
                        "description": "Analyze and return the schema of a collection",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Connection session ID"},
                                "database_name": {"type": "string", "description": "Name of the database"},
                                "collection_name": {"type": "string", "description": "Name of the collection"}
                            },
                            "required": ["session_id", "database_name", "collection_name"]
                        }
                    },
                    {
                        "name": "aggregate_collection",
                        "description": "Run an aggregation pipeline on a collection",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Connection session ID"},
                                "database_name": {"type": "string", "description": "Name of the database"},
                                "collection_name": {"type": "string", "description": "Name of the collection"},
                                "pipeline": {"type": "array", "description": "Aggregation pipeline stages"},
                                "limit": {"type": "integer", "description": "Maximum documents to return", "default": 10}
                            },
                            "required": ["session_id", "database_name", "collection_name", "pipeline"]
                        }
                    },
                    {
                        "name": "list_active_connections",
                        "description": "List all active database connections",
                        "inputSchema": {"type": "object", "properties": {}, "required": []}
                    },
                    {
                        "name": "close_connection",
                        "description": "Close a database connection",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Connection session ID"}
                            },
                            "required": ["session_id"]
                        }
                    },
                    {
                        "name": "test_connection",
                        "description": "Test if a connection is still working",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Connection session ID"}
                            },
                            "required": ["session_id"]
                        }
                    }
                ]
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tools}
                }
            
            elif method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments", {})
                
                start_time = time.time()
                result = None
                error = None
                success = False
                
                try:
                    # Call the appropriate MongoDB tool
                    if name == "establish_connection":
                        result = await self.mongodb_tools.establish_connection(
                            arguments["connection_string"]
                        )
                    elif name == "list_databases":
                        result = self.mongodb_tools.list_databases(
                            arguments["session_id"]
                        )
                    elif name == "list_collections":
                        result = self.mongodb_tools.list_collections(
                            arguments["session_id"],
                            arguments["database_name"]
                        )
                    elif name == "query_collection":
                        result = self.mongodb_tools.query_collection(
                            arguments["session_id"],
                            arguments["database_name"],
                            arguments["collection_name"],
                            arguments.get("query"),
                            arguments.get("limit", 10),
                            arguments.get("projection"),
                            arguments.get("sort")
                        )
                    elif name == "get_sample_documents":
                        result = self.mongodb_tools.get_sample_documents(
                            arguments["session_id"],
                            arguments["database_name"],
                            arguments["collection_name"],
                            arguments.get("limit", 5)
                        )
                    elif name == "get_collection_schema":
                        result = self.mongodb_tools.get_collection_schema(
                            arguments["session_id"],
                            arguments["database_name"],
                            arguments["collection_name"]
                        )
                    elif name == "aggregate_collection":
                        result = self.mongodb_tools.aggregate_collection(
                            arguments["session_id"],
                            arguments["database_name"],
                            arguments["collection_name"],
                            arguments["pipeline"],
                            arguments.get("limit", 10)
                        )
                    elif name == "list_active_connections":
                        result = self.mongodb_tools.list_active_connections()
                    elif name == "close_connection":
                        result = await self.mongodb_tools.close_connection(
                            arguments["session_id"]
                        )
                    elif name == "test_connection":
                        result = await self.mongodb_tools.test_connection(
                            arguments["session_id"]
                        )
                    else:
                        result = {"success": False, "error": f"Unknown tool: {name}"}
                        error = f"Unknown tool: {name}"
                    
                    success = True
                except Exception as e:
                    error = str(e)
                    result = {"success": False, "error": error}
                    success = False
                
                duration = time.time() - start_time
                
                # Log to web API (async, don't block on failure)
                asyncio.create_task(log_to_web_api(
                    method=name,
                    params=arguments,
                    success=success,
                    duration=duration,
                    result=result,
                    error=error
                ))
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
        
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
    
    async def run(self):
        """Run the server with STDIO communication."""
        logger.info("Starting Simple MongoDB MCP Server")
        
        while True:
            try:
                # Read from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Handle the request
                response = await self.handle_request(line)
                
                # Send response to stdout
                if response:
                    print(json.dumps(response))
                    sys.stdout.flush()
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                break

async def main():
    """Main entry point."""
    server = SimpleMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main()) 