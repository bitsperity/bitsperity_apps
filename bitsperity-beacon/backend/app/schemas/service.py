"""
Service API Schemas
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.service import ServiceStatus


class ServiceCreate(BaseModel):
    """Schema für Service Registrierung"""
    
    name: str = Field(..., min_length=1, max_length=100, description="Service Name")
    type: str = Field(..., min_length=1, max_length=50, description="Service Type")
    host: str = Field(..., min_length=1, max_length=255, description="Service Host/IP")
    port: int = Field(..., ge=1, le=65535, description="Service Port")
    protocol: str = Field(default="http", max_length=20, description="Service Protocol")
    tags: List[str] = Field(default_factory=list, description="Service Tags")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Service Metadata")
    ttl: int = Field(default=300, ge=60, le=86400, description="Time to Live in seconds")
    health_check_url: Optional[str] = Field(None, description="Health Check URL")
    health_check_interval: Optional[int] = Field(default=60, ge=30, le=3600, description="Health Check Interval")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "homegrow-client",
                "type": "iot",
                "host": "192.168.1.100",
                "port": 8080,
                "protocol": "http",
                "tags": ["iot", "agriculture", "sensors"],
                "metadata": {
                    "version": "1.0.0",
                    "description": "HomegrowClient für Pflanzenüberwachung"
                },
                "ttl": 300,
                "health_check_url": "http://192.168.1.100:8080/health"
            }
        }


class ServiceUpdate(BaseModel):
    """Schema für Service Update"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = Field(None, max_length=20)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None
    health_check_url: Optional[str] = None
    health_check_interval: Optional[int] = Field(None, ge=30, le=3600)


class ServiceResponse(BaseModel):
    """Schema für Service Response"""
    
    service_id: str
    name: str
    type: str
    host: str
    port: int
    protocol: str
    tags: List[str]
    metadata: Dict[str, str]
    status: ServiceStatus
    ttl: int
    expires_at: datetime
    last_heartbeat: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    health_check_url: Optional[str]
    health_check_interval: Optional[int]
    mdns_service_type: Optional[str]
    
    class Config:
        from_attributes = True


class ServiceListResponse(BaseModel):
    """Schema für Service List Response"""
    
    services: List[ServiceResponse]
    total: int
    page: int = 1
    page_size: int = 50


class HeartbeatResponse(BaseModel):
    """Schema für Heartbeat Response"""
    
    service_id: str
    status: ServiceStatus
    expires_at: datetime
    last_heartbeat: datetime
    message: str = "Heartbeat received successfully" 