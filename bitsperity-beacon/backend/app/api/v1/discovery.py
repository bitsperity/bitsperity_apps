"""
Discovery API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
import structlog

from app.core.service_registry import ServiceRegistry
from app.schemas.discovery import DiscoveryResponse, ServiceDiscoveryFilter
from app.schemas.service import ServiceResponse

logger = structlog.get_logger(__name__)

router = APIRouter()

# Import global service_registry from services module
from app.api.v1.services import get_service_registry


@router.get("/discover", response_model=DiscoveryResponse)
async def discover_services(
    type: Optional[str] = Query(None, description="Filter by service type"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Limit results"),
    skip: int = Query(0, ge=0, description="Skip results"),
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Entdecke Services (Legacy/Backup API für mDNS)"""
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
        
        # Build filters applied dict
        filters_applied = {}
        if type:
            filters_applied["type"] = type
        if tags:
            filters_applied["tags"] = ",".join(tags)
        if protocol:
            filters_applied["protocol"] = protocol
        if status:
            filters_applied["status"] = status
        
        return DiscoveryResponse(
            services=service_responses,
            total=len(service_responses),
            filters_applied=filters_applied,
            discovery_method="api"
        )
        
    except Exception as e:
        logger.error("Fehler beim Service Discovery", error=str(e))
        raise HTTPException(status_code=500, detail=f"Service Discovery fehlgeschlagen: {str(e)}")


@router.post("/discover", response_model=DiscoveryResponse)
async def discover_services_with_filter(
    filter_data: ServiceDiscoveryFilter,
    limit: int = Query(50, ge=1, le=100, description="Limit results"),
    skip: int = Query(0, ge=0, description="Skip results"),
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Entdecke Services mit POST Filter"""
    try:
        services = await registry.discover_services(
            service_type=filter_data.type,
            tags=filter_data.tags,
            protocol=filter_data.protocol,
            status=filter_data.status,
            limit=limit,
            skip=skip
        )
        
        service_responses = [ServiceResponse(**service.dict()) for service in services]
        
        # Build filters applied dict
        filters_applied = {}
        if filter_data.type:
            filters_applied["type"] = filter_data.type
        if filter_data.tags:
            filters_applied["tags"] = ",".join(filter_data.tags)
        if filter_data.protocol:
            filters_applied["protocol"] = filter_data.protocol
        if filter_data.status:
            filters_applied["status"] = filter_data.status
        
        return DiscoveryResponse(
            services=service_responses,
            total=len(service_responses),
            filters_applied=filters_applied,
            discovery_method="api"
        )
        
    except Exception as e:
        logger.error("Fehler beim Service Discovery", error=str(e))
        raise HTTPException(status_code=500, detail=f"Service Discovery fehlgeschlagen: {str(e)}") 