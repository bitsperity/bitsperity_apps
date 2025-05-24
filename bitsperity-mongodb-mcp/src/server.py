#!/usr/bin/env python3

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolResult,
    ListToolsResult
)

from connection_manager import ConnectionManager
from mongodb_tools import MongoDBTools

# Configure logging
log_handlers = [
    logging.FileHandler('/app/logs/mongodb-mcp.log') if os.path.exists('/app/logs') else logging.NullHandler()
]

# Only add stdout handler in web mode, not stdio mode
mode = os.getenv('MCP_MODE', 'web')
if len(sys.argv) > 1:
    mode = sys.argv[1]

if mode != 'stdio':
    log_handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)

logger = logging.getLogger(__name__)

class MongoMCPServer:
    """MongoDB MCP Server with Web Interface."""
    
    def __init__(self):
        self.app = FastAPI(title="MongoDB MCP Server", version="1.0.0")
        self.mcp_server = Server("mongodb-mcp")
        self.connection_manager = ConnectionManager(
            session_ttl=int(os.getenv('SESSION_TTL', '3600')),
            max_connections=int(os.getenv('MAX_CONNECTIONS', '10'))
        )
        self.mongodb_tools = MongoDBTools(self.connection_manager)
        self.websocket_connections: List[WebSocket] = []
        self.query_history: List[Dict[str, Any]] = []
        self.start_time = time.time()
        
        self.setup_mcp_tools()
        self.setup_web_routes()
    
    def setup_mcp_tools(self):
        """Register MCP tools."""
        
        @self.mcp_server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available MongoDB tools."""
            tools = [
                Tool(
                    name="establish_connection",
                    description="Establish a connection to a MongoDB instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_string": {
                                "type": "string",
                                "description": "MongoDB connection string (e.g., mongodb://user:pass@host:port/db)"
                            }
                        },
                        "required": ["connection_string"]
                    }
                ),
                Tool(
                    name="list_databases", 
                    description="List all databases for a connection session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Connection session ID"
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="list_collections",
                    description="List all collections in a database", 
                    inputSchema={
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
                ),
                Tool(
                    name="get_collection_schema",
                    description="Analyze and return the schema of a collection",
                    inputSchema={
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
                ),
                Tool(
                    name="query_collection",
                    description="Query a collection with find operation",
                    inputSchema={
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
                                "description": "MongoDB query filter (default: {})",
                                "default": {}
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
                                "description": "Fields to include/exclude",
                                "default": None
                            },
                            "sort": {
                                "type": "object", 
                                "description": "Sort specification",
                                "default": None
                            }
                        },
                        "required": ["session_id", "database_name", "collection_name"]
                    }
                ),
                Tool(
                    name="aggregate_collection",
                    description="Run an aggregation pipeline on a collection",
                    inputSchema={
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
                ),
                Tool(
                    name="get_sample_documents",
                    description="Get sample documents from a collection",
                    inputSchema={
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
                ),
                Tool(
                    name="list_active_connections",
                    description="List all active database connections",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="close_connection",
                    description="Close a database connection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Connection session ID to close"
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="test_connection",
                    description="Test if a connection is still working",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string", 
                                "description": "Connection session ID to test"
                            }
                        },
                        "required": ["session_id"]
                    }
                )
            ]
            
            return ListToolsResult(tools=tools)
        
        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool calls."""
            start_time = time.time()
            
            try:
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
                
                # Record query in history
                duration = int((time.time() - start_time) * 1000)
                self.record_query(name, arguments, duration, result.get("success", False))
                
                # Broadcast update to web clients
                await self.broadcast_to_websockets({
                    "type": "query_executed",
                    "query": {
                        "operation": name,
                        "arguments": arguments,
                        "timestamp": time.time(),
                        "duration": duration,
                        "success": result.get("success", False)
                    }
                })
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                )
                
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                duration = int((time.time() - start_time) * 1000)
                self.record_query(name, arguments, duration, False)
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2))]
                )
    
    def setup_web_routes(self):
        """Setup FastAPI web routes."""
        
        # Serve static files
        self.app.mount("/static", StaticFiles(directory="/app/web"), name="static")
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve the main web interface."""
            try:
                with open("/app/web/index.html", "r", encoding="utf-8") as f:
                    content = f.read()
                return HTMLResponse(content=content)
            except FileNotFoundError:
                return HTMLResponse("<h1>MongoDB MCP Server</h1><p>Web interface not found</p>")
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "uptime": time.time() - self.start_time,
                "active_connections": len(self.connection_manager.connections),
                "mcp_server": "running"
            }
        
        @self.app.get("/api/connections")
        async def get_connections():
            """Get active connections and stats."""
            connections = self.connection_manager.list_active_connections()
            stats = self.connection_manager.get_stats()
            stats.update({
                "uptime": time.time() - self.start_time,
                "total_queries": len(self.query_history)
            })
            
            return {
                "active_connections": connections,
                "stats": stats
            }
        
        @self.app.delete("/api/connections/{session_id}")
        async def close_connection(session_id: str):
            """Close a specific connection."""
            success = await self.connection_manager.close_connection(session_id)
            if success:
                await self.broadcast_to_websockets({
                    "type": "connection_closed",
                    "session_id": session_id
                })
                return {"success": True, "message": "Connection closed"}
            else:
                raise HTTPException(status_code=404, detail="Connection not found")
        
        @self.app.get("/api/recent-queries")
        async def get_recent_queries():
            """Get recent query history."""
            # Return last 50 queries
            recent_queries = self.query_history[-50:] if len(self.query_history) > 50 else self.query_history
            return {"queries": recent_queries}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                # Send initial data
                connections = self.connection_manager.list_active_connections()
                stats = self.connection_manager.get_stats()
                stats.update({
                    "uptime": time.time() - self.start_time,
                    "total_queries": len(self.query_history)
                })
                
                await websocket.send_text(json.dumps({
                    "type": "initial_data",
                    "connections": connections,
                    "stats": stats,
                    "recent_queries": self.query_history[-10:]
                }))
                
                # Keep connection alive
                while True:
                    await websocket.receive_text()
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
    
    async def broadcast_to_websockets(self, message: Dict[str, Any]):
        """Broadcast message to all connected websockets."""
        if not self.websocket_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for ws in self.websocket_connections:
            try:
                await ws.send_text(message_str)
            except Exception:
                disconnected.append(ws)
        
        # Remove disconnected websockets
        for ws in disconnected:
            self.websocket_connections.remove(ws)
    
    def record_query(self, operation: str, arguments: Dict[str, Any], duration: int, success: bool):
        """Record a query in the history."""
        query_record = {
            "operation": operation,
            "arguments": arguments,
            "timestamp": time.time(),
            "duration": duration,
            "success": success,
            "database": arguments.get("database_name"),
            "collection": arguments.get("collection_name")
        }
        
        self.query_history.append(query_record)
        
        # Keep only last 1000 queries
        if len(self.query_history) > 1000:
            self.query_history = self.query_history[-1000:]
    
    async def run_mcp_server(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.mcp_server.run(
                read_stream, 
                write_stream,
                self.mcp_server.create_initialization_options()
            )
    
    async def run_web_server(self):
        """Run the web server."""
        config = uvicorn.Config(
            app=self.app,
            host=os.getenv('WEB_HOST', '0.0.0.0'),
            port=int(os.getenv('WEB_PORT', '8080')),
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def shutdown(self):
        """Shutdown the server."""
        logger.info("Shutting down MongoDB MCP Server...")
        await self.connection_manager.shutdown()

async def main():
    """Main entry point."""
    server = MongoMCPServer()
    
    # Check if we should run in stdio mode (for MCP clients like Cursor)
    mode = os.getenv('MCP_MODE', 'web')
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    try:
        if mode == 'stdio':
            logger.info("Starting MongoDB MCP Server in stdio mode (for Cursor/MCP clients)")
            await server.run_mcp_server()
        else:
            logger.info("Starting MongoDB MCP Server in web mode")
            await server.run_web_server()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await server.shutdown()

if __name__ == "__main__":
    asyncio.run(main()) 