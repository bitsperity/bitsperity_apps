#!/usr/bin/env python3
"""
Einfache Bitsperity Beacon App - Funktionsfähige Version ohne MongoDB
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
from datetime import datetime

app = FastAPI(
    title="Bitsperity Beacon",
    description="Service Discovery Server (Working Version)",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Service Registry (für Tests)
services_registry = {}

@app.get("/")
async def root():
    return {
        "name": "Bitsperity Beacon",
        "version": "1.0.0",
        "status": "running",
        "description": "Service Discovery Server",
        "timestamp": datetime.utcnow().isoformat(),
        "services_count": len(services_registry)
    }

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "service": "bitsperity-beacon",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time(),
        "database": "in-memory",
        "services_registered": len(services_registry)
    }

@app.get("/api/v1/services")
async def list_services():
    return {
        "services": list(services_registry.values()),
        "count": len(services_registry),
        "message": "Service registry is ready"
    }

@app.post("/api/v1/services/register")
async def register_service(service_data: dict):
    service_id = f"service_{len(services_registry) + 1}"
    service = {
        "service_id": service_id,
        "name": service_data.get("name", "unknown"),
        "type": service_data.get("type", "generic"),
        "host": service_data.get("host", "localhost"),
        "port": service_data.get("port", 8080),
        "registered_at": datetime.utcnow().isoformat(),
        "ttl": service_data.get("ttl", 300),
        "status": "active"
    }
    
    services_registry[service_id] = service
    
    return {
        "message": "Service registered successfully",
        "service": service
    }

@app.get("/api/v1/services/discover")
async def discover_services():
    return {
        "discovered_services": list(services_registry.values()),
        "count": len(services_registry),
        "discovery_method": "in-memory"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 