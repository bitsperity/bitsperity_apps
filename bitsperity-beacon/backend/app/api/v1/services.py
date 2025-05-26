"""
Services API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
import structlog

from app.core.json_encoder import jsonable_encoder

from app.database import get_database, Database
from app.core.service_registry import ServiceRegistry
from app.core.mdns_server import MDNSServer
from app.core.websocket_manager import WebSocketManager
from app.schemas.service import (
    ServiceCreate, 
    ServiceUpdate, 
    ServiceResponse, 
    ServiceListResponse,
    HeartbeatResponse
)
from app.models.service import ServiceStatus

logger = structlog.get_logger(__name__)

router = APIRouter()

# Global instances (werden in main.py initialisiert)
service_registry: Optional[ServiceRegistry] = None
mdns_server: Optional[MDNSServer] = None
websocket_manager: Optional[WebSocketManager] = None


def get_service_registry() -> ServiceRegistry:
    """Dependency für Service Registry"""
    if service_registry is None:
        raise HTTPException(status_code=500, detail="Service Registry nicht initialisiert")
    return service_registry


def get_mdns_server() -> MDNSServer:
    """Dependency für mDNS Server"""
    if mdns_server is None:
        raise HTTPException(status_code=500, detail="mDNS Server nicht initialisiert")
    return mdns_server


def get_websocket_manager() -> WebSocketManager:
    """Dependency für WebSocket Manager"""
    if websocket_manager is None:
        raise HTTPException(status_code=500, detail="WebSocket Manager nicht initialisiert")
    return websocket_manager


@router.post("/register", status_code=201)
async def register_service(
    service_data: ServiceCreate,
    registry: ServiceRegistry = Depends(get_service_registry),
    mdns: MDNSServer = Depends(get_mdns_server),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """Registriere einen neuen Service"""
    try:
        # Registriere Service
        service = await registry.register_service(service_data)
        
        # Registriere in mDNS
        mdns_success = await mdns.register_service(service)
        if not mdns_success:
            logger.warning("mDNS Registrierung fehlgeschlagen", service_id=service.service_id)
        
        # Broadcast WebSocket Update
        service_dict = jsonable_encoder(service)
        await ws_manager.broadcast_service_registered(service_dict)
        
        logger.info("Service erfolgreich registriert",
                   service_id=service.service_id,
                   name=service.name,
                   mdns_registered=mdns_success)
        
        # Konvertiere Service zu Response
        return JSONResponse(content=jsonable_encoder(service))
        
    except Exception as e:
        logger.error("Fehler bei Service Registrierung", error=str(e))
        raise HTTPException(status_code=500, detail=f"Service Registrierung fehlgeschlagen: {str(e)}")


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Hole Service Details"""
    service = await registry.get_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service nicht gefunden")
    
    return ServiceResponse(**service.dict())


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    update_data: ServiceUpdate,
    registry: ServiceRegistry = Depends(get_service_registry),
    mdns: MDNSServer = Depends(get_mdns_server),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """Aktualisiere Service"""
    try:
        # Update Service
        service = await registry.update_service(service_id, update_data)
        if not service:
            raise HTTPException(status_code=404, detail="Service nicht gefunden")
        
        # Update mDNS
        mdns_success = await mdns.update_service(service)
        if not mdns_success:
            logger.warning("mDNS Update fehlgeschlagen", service_id=service_id)
        
        # Broadcast WebSocket Update
        service_dict = service.dict()
        await ws_manager.broadcast_service_updated(service_dict)
        
        logger.info("Service erfolgreich aktualisiert", service_id=service_id)
        
        return ServiceResponse(**service.model_dump())
        
    except Exception as e:
        logger.error("Fehler bei Service Update", service_id=service_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Service Update fehlgeschlagen: {str(e)}")


@router.put("/{service_id}/heartbeat", response_model=HeartbeatResponse)
async def service_heartbeat(
    service_id: str,
    ttl: Optional[int] = Query(None, description="TTL in Sekunden"),
    registry: ServiceRegistry = Depends(get_service_registry),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """Service Heartbeat - verlängere TTL"""
    try:
        service = await registry.extend_service_ttl(service_id, ttl)
        if not service:
            raise HTTPException(status_code=404, detail="Service nicht gefunden")
        
        # Broadcast WebSocket Update
        await ws_manager.broadcast_service_heartbeat(
            service_id, 
            service.expires_at.isoformat()
        )
        
        logger.debug("Service Heartbeat empfangen", service_id=service_id)
        
        return HeartbeatResponse(
            service_id=service.service_id,
            status=service.status,
            expires_at=service.expires_at,
            last_heartbeat=service.last_heartbeat
        )
        
    except Exception as e:
        logger.error("Fehler bei Service Heartbeat", service_id=service_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Heartbeat fehlgeschlagen: {str(e)}")


@router.delete("/{service_id}", status_code=204)
async def deregister_service(
    service_id: str,
    registry: ServiceRegistry = Depends(get_service_registry),
    mdns: MDNSServer = Depends(get_mdns_server),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """Deregistriere Service"""
    try:
        # Hole Service Info für WebSocket Broadcast
        service = await registry.get_service_by_id(service_id)
        service_name = service.name if service else None
        
        # Deregistriere Service
        success = await registry.deregister_service(service_id)
        if not success:
            raise HTTPException(status_code=404, detail="Service nicht gefunden")
        
        # Deregistriere von mDNS
        mdns_success = await mdns.unregister_service(service_id)
        if not mdns_success:
            logger.warning("mDNS Deregistrierung fehlgeschlagen", service_id=service_id)
        
        # Broadcast WebSocket Update
        await ws_manager.broadcast_service_deregistered(service_id, service_name)
        
        logger.info("Service erfolgreich deregistriert", service_id=service_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Fehler bei Service Deregistrierung", service_id=service_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Service Deregistrierung fehlgeschlagen: {str(e)}")


@router.get("/{service_id}/status", response_model=ServiceResponse)
async def get_service_status(
    service_id: str,
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Hole Service Status und TTL Info"""
    service = await registry.get_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service nicht gefunden")
    
    return ServiceResponse(**service.dict())


@router.get("/", response_model=ServiceListResponse)
async def list_services(
    type: Optional[str] = Query(None, description="Filter by service type"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Limit results"),
    skip: int = Query(0, ge=0, description="Skip results"),
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Liste alle Services mit optionalen Filtern"""
    try:
        services = await registry.discover_services(
            service_type=type,
            tags=tags,
            protocol=protocol,
            status=status,
            limit=limit,
            skip=skip
        )
        
        service_responses = [ServiceResponse(**service.dict()) for service in services]
        
        return ServiceListResponse(
            services=service_responses,
            total=len(service_responses),
            page=skip // limit + 1,
            page_size=limit
        )
        
    except Exception as e:
        logger.error("Fehler beim Laden der Services", error=str(e))
        raise HTTPException(status_code=500, detail=f"Services laden fehlgeschlagen: {str(e)}")


@router.get("/types", response_model=List[str])
async def get_service_types(
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Hole alle verfügbaren Service Types"""
    try:
        types = await registry.get_service_types()
        return types
        
    except Exception as e:
        logger.error("Fehler beim Laden der Service Types", error=str(e))
        raise HTTPException(status_code=500, detail=f"Service Types laden fehlgeschlagen: {str(e)}")


@router.get("/tags", response_model=List[str])
async def get_service_tags(
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Hole alle verfügbaren Service Tags"""
    try:
        tags = await registry.get_service_tags()
        return tags
        
    except Exception as e:
        logger.error("Fehler beim Laden der Service Tags", error=str(e))
        raise HTTPException(status_code=500, detail=f"Service Tags laden fehlgeschlagen: {str(e)}")


@router.get("/expired", response_model=ServiceListResponse)
async def get_expired_services(
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Hole alle abgelaufenen Services"""
    try:
        expired_services = await registry.get_expired_services()
        service_responses = [ServiceResponse(**service.dict()) for service in expired_services]
        
        return ServiceListResponse(
            services=service_responses,
            total=len(service_responses)
        )
        
    except Exception as e:
        logger.error("Fehler beim Laden abgelaufener Services", error=str(e))
        raise HTTPException(status_code=500, detail=f"Abgelaufene Services laden fehlgeschlagen: {str(e)}")


# Setze globale Instanzen (wird von main.py aufgerufen)
def set_dependencies(
    registry: ServiceRegistry,
    mdns: MDNSServer,
    ws_manager: WebSocketManager
):
    """Setze globale Dependencies"""
    global service_registry, mdns_server, websocket_manager
    service_registry = registry
    mdns_server = mdns
    websocket_manager = ws_manager 