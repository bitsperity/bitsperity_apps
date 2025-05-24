#!/usr/bin/env python3
"""
MongoDB MCP Server for STDIO communication with Cursor IDE.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
    Tool,
    TextContent,
    CallToolResult,
    ListToolsResult
)

from connection_manager import ConnectionManager
from mongodb_tools import MongoDBTools

# Configure logging for STDIO mode
log_file = Path(os.getenv('DATA_DIR', './data')) / 'logs' / 'mcp-cursor.log'
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        # Don't add stdout handler in STDIO mode - it interferes with MCP communication
    ]
)

logger = logging.getLogger(__name__)

class MongoMCPStdioServer:
    """MongoDB MCP Server for STDIO communication."""
    
    def __init__(self):
        self.server = Server("mongodb-mcp")
        self.connection_manager = ConnectionManager(
            session_ttl=int(os.getenv('SESSION_TTL', '3600')),
            max_connections=int(os.getenv('MAX_CONNECTIONS', '10'))
        )
        self.mongodb_tools = MongoDBTools(self.connection_manager)
        
        self.setup_tools()
    
    def setup_tools(self):
        """Register MCP tools with proper error handling."""
        
        @self.server.list_tools()
        async def list_tools():
            """List available MongoDB tools."""
            try:
                tools = [
                    {
                        "name": "establish_connection",
                        "description": "Establish a connection to a MongoDB instance",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "connection_string": {
                                    "type": "string",
                                    "description": "MongoDB connection string (e.g., mongodb://user:pass@host:port/db)"
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
                                "session_id": {
                                    "type": "string",
                                    "description": "Connection session ID"
                                }
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
                                "session_id": {
                                    "type": "string",
                                    "description": "Connection session ID"
                                },
                                "database_name": {
                                    "type": "string", 
                                    "description": "Name of the database"
                                }
                            },
                            "required": ["session_id", "database_name"]
                        }
                    },
                    {
                        "name": "get_collection_schema",
                        "description": "Analyze and return the schema of a collection",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {
                                    "type": "string",
                                    "description": "Connection session ID"
                                },
                                "database_name": {
                                    "type": "string",
                                    "description": "Name of the database"
                                },
                                "collection_name": {
                                    "type": "string",
                                    "description": "Name of the collection"
                                }
                            },
                            "required": ["session_id", "database_name", "collection_name"]
                        }
                    },
                    {
                        "name": "query_collection",
                        "description": "Query a collection with find operation",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {
                                    "type": "string",
                                    "description": "Connection session ID"
                                },
                                "database_name": {
                                    "type": "string",
                                    "description": "Name of the database"
                                },
                                "collection_name": {
                                    "type": "string", 
                                    "description": "Name of the collection"
                                },
                                "query": {
                                    "type": "object",
                                    "description": "MongoDB query filter (default: {})"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of documents to return",
                                    "default": 10,
                                    "minimum": 1,
                                    "maximum": 100
                                },
                                "projection": {
                                    "type": "object",
                                    "description": "Fields to include/exclude"
                                },
                                "sort": {
                                    "type": "object", 
                                    "description": "Sort specification"
                                }
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
                                "session_id": {
                                    "type": "string",
                                    "description": "Connection session ID"
                                },
                                "database_name": {
                                    "type": "string",
                                    "description": "Name of the database"
                                },
                                "collection_name": {
                                    "type": "string",
                                    "description": "Name of the collection"
                                },
                                "pipeline": {
                                    "type": "array",
                                    "description": "Aggregation pipeline stages",
                                    "items": {"type": "object"}
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of documents to return",
                                    "default": 10,
                                    "minimum": 1,
                                    "maximum": 100
                                }
                            },
                            "required": ["session_id", "database_name", "collection_name", "pipeline"]
                        }
                    },
                    {
                        "name": "get_sample_documents",
                        "description": "Get sample documents from a collection",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {
                                    "type": "string",
                                    "description": "Connection session ID"
                                },
                                "database_name": {
                                    "type": "string",
                                    "description": "Name of the database"
                                },
                                "collection_name": {
                                    "type": "string",
                                    "description": "Name of the collection"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Number of sample documents",
                                    "default": 5,
                                    "minimum": 1,
                                    "maximum": 10
                                }
                            },
                            "required": ["session_id", "database_name", "collection_name"]
                        }
                    },
                    {
                        "name": "list_active_connections",
                        "description": "List all active database connections",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    },
                    {
                        "name": "close_connection",
                        "description": "Close a database connection",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {
                                    "type": "string",
                                    "description": "Connection session ID to close"
                                }
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
                                "session_id": {
                                    "type": "string", 
                                    "description": "Connection session ID to test"
                                }
                            },
                            "required": ["session_id"]
                        }
                    }
                ]
                
                logger.info(f"Listed {len(tools)} MongoDB tools")
                return tools
                
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                # Return empty tools list on error
                return []
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Handle tool calls with comprehensive error handling."""
            try:
                logger.info(f"Calling tool: {name} with arguments: {arguments}")
                
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
                elif name == "get_collection_schema":
                    result = self.mongodb_tools.get_collection_schema(
                        arguments["session_id"],
                        arguments["database_name"],
                        arguments["collection_name"]
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
                elif name == "aggregate_collection":
                    result = self.mongodb_tools.aggregate_collection(
                        arguments["session_id"],
                        arguments["database_name"],
                        arguments["collection_name"],
                        arguments["pipeline"],
                        arguments.get("limit", 10)
                    )
                elif name == "get_sample_documents":
                    result = self.mongodb_tools.get_sample_documents(
                        arguments["session_id"],
                        arguments["database_name"],
                        arguments["collection_name"],
                        arguments.get("limit", 5)
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
                    result = {
                        "success": False,
                        "error": f"Unknown tool: {name}"
                    }
                
                logger.info(f"Tool {name} completed with success: {result.get('success', False)}")
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
                
            except Exception as e:
                error_msg = f"Error calling tool {name}: {str(e)}"
                logger.error(error_msg)
                
                error_result = {
                    "success": False,
                    "error": str(e),
                    "tool": name,
                    "arguments": arguments
                }
                
                return {
                    "content": [
                        {
                            "type": "text", 
                            "text": json.dumps(error_result, indent=2)
                        }
                    ]
                }
    
    async def run(self):
        """Run the MCP server in STDIO mode."""
        logger.info("Starting MongoDB MCP Server in STDIO mode")
        async with stdio_server() as streams:
            await self.server.run(
                streams[0], streams[1], self.server.create_initialization_options()
            )

async def main():
    """Main entry point."""
    server = MongoMCPStdioServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main()) 