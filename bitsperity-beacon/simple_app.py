#!/usr/bin/env python3
"""
Einfache Bitsperity Beacon App - Temporäre Lösung
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(
    title="Bitsperity Beacon",
    description="Service Discovery Server (Simplified)",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "name": "Bitsperity Beacon",
        "version": "1.0.0",
        "status": "running",
        "description": "Service Discovery Server"
    }

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "service": "bitsperity-beacon",
        "version": "1.0.0"
    }

@app.get("/api/v1/services")
async def list_services():
    return {
        "services": [],
        "count": 0,
        "message": "Service registry is ready"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 