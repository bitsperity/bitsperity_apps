"""
Bitsperity Beacon - FastAPI Hauptanwendung
Enhanced with Health Check Manager Support
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
import structlog
import os
import json
from datetime import datetime
from bson import ObjectId

from app.config import settings
from app.database import database
from app.core import ServiceRegistry, TTLManager, WebSocketManager
from app.core.avahi_mdns import AvahiMDNSServer
from app.core.health_check_manager import HealthCheckManager
from app.api.v1 import services, discovery, health, websocket, debug
from app.api.v1.services import set_dependencies
from app.api.v1.websocket import set_websocket_manager

# Konfiguriere Logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global instances
service_registry: ServiceRegistry = None
ttl_manager: TTLManager = None
mdns_server: AvahiMDNSServer = None
websocket_manager: WebSocketManager = None
health_check_manager: HealthCheckManager = None


class CORSHeaderMiddleware(BaseHTTPMiddleware):
    """Custom CORS Middleware to ensure headers are always set"""
    
    async def dispatch(self, request: Request, call_next):
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Content-Length"] = "0"
            return response
        
        # Process normal requests
        response = await call_next(request)
        
        # Add CORS headers to all responses
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


async def bootstrap_self_registration():
    """Bootstrap: Register Beacon as service with health checks"""
    try:
        from app.schemas.service import ServiceCreate
        
        # Wait a bit for everything to be ready
        await asyncio.sleep(5)
        
        # Self-register Beacon service
        beacon_service = ServiceCreate(
            name="bitsperity-beacon",
            type="service-discovery",
            host="0.0.0.0",  # Internal host
            port=80,  # Internal port
            protocol="http",
            tags=["beacon", "service-discovery", "mdns", "umbrel"],
            metadata={
                "version": "1.0.0",
                "description": "Bitsperity Beacon Service Discovery Server",
                "umbrel_app": "true",
                "auto_registered": "true"
            },
            health_check_url="http://127.0.0.1:80/api/v1/health",  # Internal health check
            health_check_interval=60,
            health_check_timeout=10,
            health_check_enabled=True,
            fallback_to_health_check=True,
            ttl=300
        )
        
        beacon_service_obj = await service_registry.register_service(beacon_service)
        logger.info("Beacon self-registered successfully", 
                   service_id=beacon_service_obj.service_id,
                   name=beacon_service_obj.name)
        
    except Exception as e:
        logger.warning("Self-registration failed (non-critical)", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application Lifespan Manager"""
    global service_registry, ttl_manager, mdns_server, websocket_manager, health_check_manager
    
    logger.info("Starte Bitsperity Beacon", version="1.0.0")
    
    try:
        # 1. Verbinde zur Database
        await database.connect()
        logger.info("Database Verbindung hergestellt")
        
        # 2. Initialisiere Core Komponenten
        websocket_manager = WebSocketManager()
        mdns_server = AvahiMDNSServer()
        service_registry = ServiceRegistry(database, mdns_server)  # mDNS-Referenz für TTL-Cleanup
        
        # Initialize Health Check Manager
        health_check_manager = HealthCheckManager(service_registry, websocket_manager)
        
        # Initialize TTL Manager with health check support
        ttl_manager = TTLManager(service_registry, health_check_manager)
        
        # 3. Setze Dependencies für API Endpoints
        set_dependencies(service_registry, mdns_server, websocket_manager)
        set_websocket_manager(websocket_manager)
        
        # 4. Starte mDNS Server
        await mdns_server.start()
        logger.info("mDNS Server gestartet")
        
        # Start Health Check Manager
        try:
            await health_check_manager.start()
            logger.info("Health Check Manager gestartet")
        except Exception as hc_error:
            logger.warning("Health Check Manager failed to start", error=str(hc_error))
            # Continue without health checks - not critical
        
        # 5. Starte TTL Manager
        await ttl_manager.start()
        logger.info("TTL Manager gestartet")
        
        # 6. 🆕 Bootstrap self-registration (async)
        asyncio.create_task(bootstrap_self_registration())
        
        logger.info("Bitsperity Beacon erfolgreich gestartet")
        
        yield
        
    except Exception as e:
        logger.error("Fehler beim Starten von Bitsperity Beacon", error=str(e))
        raise
    
    finally:
        # Shutdown
        logger.info("Stoppe Bitsperity Beacon")
        
        try:
            # Stoppe TTL Manager
            if ttl_manager:
                await ttl_manager.stop()
                logger.info("TTL Manager gestoppt")
            
            # Stop Health Check Manager
            if health_check_manager:
                try:
                    await health_check_manager.stop()
                    logger.info("Health Check Manager gestoppt")
                except Exception as hc_error:
                    logger.warning("Error stopping Health Check Manager", error=str(hc_error))
            
            # Stoppe mDNS Server
            if mdns_server:
                await mdns_server.stop()
                logger.info("mDNS Server gestoppt")
            
            # Schließe Database Verbindung
            await database.disconnect()
            logger.info("Database Verbindung geschlossen")
            
        except Exception as e:
            logger.error("Fehler beim Stoppen von Bitsperity Beacon", error=str(e))
        
        logger.info("Bitsperity Beacon gestoppt")


# Custom JSON Encoder für ObjectId und datetime
def custom_json_encoder(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Erstelle FastAPI App
app = FastAPI(
    title="Bitsperity Beacon",
    description="Service Discovery Server mit mDNS/Bonjour-Unterstützung",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    redirect_slashes=False  # Verhindere automatische Redirects für trailing slashes
)

# Setze custom JSON encoder für FastAPI
from fastapi.encoders import jsonable_encoder as fastapi_jsonable_encoder
from app.core.json_encoder import jsonable_encoder

# Custom CORS Middleware (first)
app.add_middleware(CORSHeaderMiddleware)

# Standard CORS Middleware (backup)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests für 1 Stunde
)

# API Routes
app.include_router(
    services.router,
    prefix=f"{settings.api_prefix}/services",
    tags=["Services"]
)

app.include_router(
    discovery.router,
    prefix=f"{settings.api_prefix}/services",
    tags=["Discovery"]
)

app.include_router(
    health.router,
    prefix=settings.api_prefix,
    tags=["Health"]
)

app.include_router(
    websocket.router,
    prefix=settings.api_prefix,
    tags=["WebSocket"]
)

app.include_router(
    debug.router,
    prefix=f"{settings.api_prefix}/debug",
    tags=["Debug"]
)

# Static Files (Frontend)
frontend_path = "/app/frontend/dist"
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    # Serve specific frontend assets
    @app.get("/assets/{file_path:path}")
    async def serve_assets(file_path: str):
        """Serve Frontend Assets"""
        asset_path = os.path.join(frontend_path, "assets", file_path)
        if os.path.isfile(asset_path):
            return FileResponse(asset_path)
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Asset not found")
    
    @app.get("/logo.svg")
    async def serve_logo():
        """Serve Logo"""
        logo_path = os.path.join(frontend_path, "logo.svg")
        if os.path.isfile(logo_path):
            return FileResponse(logo_path)
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Logo not found")


@app.get("/")
async def root():
    """Root Endpoint - Serve Frontend"""
    # Serve frontend if available
    if os.path.exists(frontend_path):
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
    
    # Fallback to API info
    return {
        "name": "Bitsperity Beacon",
        "version": "1.0.0",
        "description": "Service Discovery Server mit mDNS/Bonjour-Unterstützung",
        "docs": "/api/docs",
        "health": f"{settings.api_prefix}/health"
    }


@app.get("/api")
async def api_info():
    """API Info Endpoint"""
    return {
        "name": "Bitsperity Beacon API",
        "version": "1.0.0",
        "prefix": settings.api_prefix,
        "endpoints": {
            "services": f"{settings.api_prefix}/services",
            "discovery": f"{settings.api_prefix}/services/discover",
            "health": f"{settings.api_prefix}/health",
            "websocket": f"{settings.api_prefix}/ws"
        }
    }


# Frontend SPA Routing - specific routes only
if os.path.exists(frontend_path):
    # Serve index.html for common SPA routes
    @app.get("/dashboard")
    @app.get("/services")
    @app.get("/discovery")
    @app.get("/settings")
    async def serve_spa_routes():
        """Serve SPA Routes"""
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Frontend not found")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.beacon_host,
        port=settings.beacon_port,
        log_level=settings.beacon_log_level.lower(),
        reload=False
    ) 