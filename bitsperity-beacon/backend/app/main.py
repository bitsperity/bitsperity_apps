"""
Bitsperity Beacon - FastAPI Hauptanwendung
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import settings
from app.database import database
from app.core import ServiceRegistry, TTLManager, MDNSServer, WebSocketManager
from app.api.v1 import services, discovery, health, websocket
from app.api.v1.services import set_dependencies

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
mdns_server: MDNSServer = None
websocket_manager: WebSocketManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application Lifespan Manager"""
    global service_registry, ttl_manager, mdns_server, websocket_manager
    
    logger.info("Starte Bitsperity Beacon", version="1.0.0")
    
    try:
        # 1. Verbinde zur Database
        await database.connect()
        logger.info("Database Verbindung hergestellt")
        
        # 2. Initialisiere Core Komponenten
        service_registry = ServiceRegistry(database)
        websocket_manager = WebSocketManager()
        mdns_server = MDNSServer()
        ttl_manager = TTLManager(service_registry)
        
        # 3. Setze Dependencies für API Endpoints
        set_dependencies(service_registry, mdns_server, websocket_manager)
        
        # 4. Starte mDNS Server
        await mdns_server.start()
        logger.info("mDNS Server gestartet")
        
        # 5. Starte TTL Manager
        await ttl_manager.start()
        logger.info("TTL Manager gestartet")
        
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


# Erstelle FastAPI App
app = FastAPI(
    title="Bitsperity Beacon",
    description="Service Discovery Server mit mDNS/Bonjour-Unterstützung",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/")
async def root():
    """Root Endpoint"""
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


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.beacon_host,
        port=settings.beacon_port,
        log_level=settings.beacon_log_level.lower(),
        reload=False
    ) 