"""
Discovery API Schemas
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .service import ServiceResponse


class ServiceDiscoveryFilter(BaseModel):
    """Schema für Service Discovery Filter"""
    
    type: Optional[str] = Field(None, description="Filter by service type")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    protocol: Optional[str] = Field(None, description="Filter by protocol")
    status: Optional[str] = Field(None, description="Filter by status")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "iot",
                "tags": ["sensors", "agriculture"],
                "protocol": "http",
                "status": "active"
            }
        }


class DiscoveryResponse(BaseModel):
    """Schema für Discovery Response"""
    
    services: List[ServiceResponse]
    total: int
    filters_applied: Dict[str, str]
    discovery_method: str = "api"  # "api" or "mdns"
    
    class Config:
        schema_extra = {
            "example": {
                "services": [],
                "total": 0,
                "filters_applied": {"type": "iot"},
                "discovery_method": "api"
            }
        } 