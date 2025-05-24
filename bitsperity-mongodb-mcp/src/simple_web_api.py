#!/usr/bin/env python3
"""
Simple Web API to serve MCP logs and statistics
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="MongoDB MCP Web API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="/app/web"), name="static")

# In-memory storage for MCP calls (in production, use a proper database)
mcp_calls: List[Dict[str, Any]] = []
stats = {
    "total_calls": 0,
    "successful_calls": 0,
    "failed_calls": 0,
    "start_time": time.time()
}

def log_mcp_call(method: str, params: Dict[str, Any], success: bool, duration: float, result: Any = None, error: str = None):
    """Log an MCP call for the web interface."""
    call = {
        "timestamp": datetime.now().isoformat(),
        "method": method,
        "params": params,
        "success": success,
        "duration_ms": round(duration * 1000, 2),
        "result": str(result)[:500] if result else None,  # Truncate long results
        "error": error
    }
    
    mcp_calls.append(call)
    # Keep only last 100 calls
    if len(mcp_calls) > 100:
        mcp_calls.pop(0)
    
    # Update stats
    stats["total_calls"] += 1
    if success:
        stats["successful_calls"] += 1
    else:
        stats["failed_calls"] += 1

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    try:
        with open("/app/web/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>MongoDB MCP Server</h1><p>Web interface not found</p>")

@app.get("/api/calls")
async def get_recent_calls():
    """Get recent MCP calls."""
    return {
        "calls": list(reversed(mcp_calls[-50:])),  # Last 50 calls, newest first
        "total": len(mcp_calls)
    }

@app.get("/api/stats")
async def get_statistics():
    """Get server statistics."""
    uptime = time.time() - stats["start_time"]
    uptime_hours = uptime / 3600
    
    success_rate = 0
    if stats["total_calls"] > 0:
        success_rate = (stats["successful_calls"] / stats["total_calls"]) * 100
    
    # Get container info
    container_id = "unknown"
    try:
        import subprocess
        result = subprocess.run(['hostname'], capture_output=True, text=True)
        container_id = result.stdout.strip()[:12]  # First 12 chars
    except:
        pass
    
    return {
        "total_calls": stats["total_calls"],
        "successful_calls": stats["successful_calls"],
        "failed_calls": stats["failed_calls"],
        "success_rate": f"{success_rate:.1f}%",
        "uptime_hours": f"{uptime_hours:.1f}h",
        "container_id": container_id,
        "active_connections": 0  # TODO: Get from connection manager
    }

@app.get("/api/tools")
async def get_available_tools():
    """Get list of available MCP tools."""
    tools = [
        {
            "name": "establish_connection",
            "description": "Connect to a MongoDB instance using connection string",
            "usage_count": len([c for c in mcp_calls if c.get("method") == "establish_connection"])
        },
        {
            "name": "list_databases",
            "description": "List all databases in the MongoDB connection",
            "usage_count": len([c for c in mcp_calls if c.get("method") == "list_databases"])
        },
        {
            "name": "list_collections",
            "description": "List collections in a specific database",
            "usage_count": len([c for c in mcp_calls if c.get("method") == "list_collections"])
        },
        {
            "name": "query_collection",
            "description": "Query documents from a collection with filters",
            "usage_count": len([c for c in mcp_calls if c.get("method") == "query_collection"])
        },
        {
            "name": "get_collection_schema",
            "description": "Analyze and return collection schema structure",
            "usage_count": len([c for c in mcp_calls if c.get("method") == "get_collection_schema"])
        },
        {
            "name": "aggregate_collection",
            "description": "Run complex aggregation pipelines",
            "usage_count": len([c for c in mcp_calls if c.get("method") == "aggregate_collection"])
        },
        {
            "name": "get_sample_documents",
            "description": "Get sample documents from collections",
            "usage_count": len([c for c in mcp_calls if c.get("method") == "get_sample_documents"])
        }
    ]
    return {"tools": tools}

@app.post("/api/log-call")
async def log_call(call_data: Dict[str, Any]):
    """Endpoint for MCP server to log calls."""
    try:
        log_mcp_call(
            method=call_data.get("method", "unknown"),
            params=call_data.get("params", {}),
            success=call_data.get("success", False),
            duration=call_data.get("duration", 0),
            result=call_data.get("result"),
            error=call_data.get("error")
        )
        return {"status": "logged"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mongodb-mcp-web-api",
        "calls_logged": len(mcp_calls)
    }

# Add some demo data for testing
def add_demo_data():
    """Add some demo MCP calls for testing."""
    demo_calls = [
        {
            "method": "establish_connection",
            "params": {"connection_string": "mongodb://localhost:27017"},
            "success": True,
            "duration": 0.15,
            "result": {"session_id": "sess_123", "status": "connected"}
        },
        {
            "method": "list_databases",
            "params": {"session_id": "sess_123"},
            "success": True,
            "duration": 0.08,
            "result": {"databases": ["myapp", "test", "admin"]}
        },
        {
            "method": "query_collection",
            "params": {"session_id": "sess_123", "database_name": "myapp", "collection_name": "users"},
            "success": True,
            "duration": 0.23,
            "result": {"documents": [{"_id": "...", "name": "John"}], "count": 1}
        }
    ]
    
    for call in demo_calls:
        log_mcp_call(**call)

if __name__ == "__main__":
    # Add demo data on startup
    add_demo_data()
    
    uvicorn.run(
        app,
        host=os.getenv('WEB_HOST', '0.0.0.0'),
        port=int(os.getenv('WEB_PORT', '8080')),
        log_level="info"
    ) 