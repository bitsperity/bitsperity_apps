"""
Service Model für Bitsperity Beacon
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from pydantic import Field, validator
import uuid

from .base import BaseModel


class ServiceStatus(str, Enum):
    """Service Status Enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    UNHEALTHY = "unhealthy"


class Service(BaseModel):
    """Service Model"""
    
    service_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    protocol: str = Field(default="http", max_length=20)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    # TTL Management
    ttl: int = Field(default=300, ge=10, le=86400)  # 10 seconds to 24 hours
    expires_at: datetime = Field(default=None)
    last_heartbeat: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Status
    status: ServiceStatus = Field(default=ServiceStatus.ACTIVE)
    health_check_url: Optional[str] = None
    health_check_interval: Optional[int] = Field(default=60, ge=30, le=3600)
    
    # mDNS Information
    mdns_service_type: Optional[str] = None
    mdns_txt_records: Dict[str, str] = Field(default_factory=dict)
    
    @validator('expires_at', pre=True, always=True)
    def set_expires_at(cls, v, values):
        """Setze expires_at basierend auf TTL"""
        if v is None:
            ttl = values.get('ttl', 300)  # Default TTL falls nicht gesetzt
            return datetime.utcnow() + timedelta(seconds=ttl)
        return v
    
    @validator('mdns_service_type', pre=True, always=True)
    def set_mdns_service_type(cls, v, values):
        """Automatische mDNS Service Type Zuordnung"""
        if v is None and 'type' in values:
            service_type = values['type'].lower()
            
            # Standard mDNS Service Type Mappings
            type_mappings = {
                'mqtt': '_mqtt._tcp',
                'http': '_http._tcp',
                'https': '_https._tcp',
                'iot': '_iot._tcp',
                'api': '_http._tcp',
                'web': '_http._tcp',
                'database': '_db._tcp',
                'cache': '_cache._tcp',
                'message_queue': '_mq._tcp'
            }
            
            return type_mappings.get(service_type, f'_{service_type}._tcp')
        return v
    
    def is_expired(self) -> bool:
        """Prüfe ob Service abgelaufen ist"""
        return datetime.utcnow() > self.expires_at
    
    def extend_ttl(self, ttl: Optional[int] = None) -> None:
        """Verlängere TTL des Services"""
        if ttl is None:
            ttl = self.ttl
        
        self.expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self.last_heartbeat = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if self.status == ServiceStatus.EXPIRED:
            self.status = ServiceStatus.ACTIVE
    
    def mark_expired(self) -> None:
        """Markiere Service als abgelaufen"""
        self.status = ServiceStatus.EXPIRED
        self.updated_at = datetime.utcnow()
    
    def get_mdns_txt_records(self) -> Dict[str, str]:
        """Erstelle TXT Records für mDNS"""
        txt_records = {
            'service_id': self.service_id,
            'name': self.name,
            'type': self.type,
            'protocol': self.protocol,
            'version': '1.0.0'
        }
        
        # Tags hinzufügen
        if self.tags:
            txt_records['tags'] = ','.join(self.tags)
        
        # Custom metadata hinzufügen
        txt_records.update(self.mdns_txt_records)
        txt_records.update(self.metadata)
        
        return txt_records
    
    class Config:
        json_schema_extra = {
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
                "health_check_url": "http://192.168.1.100:8080/health",
                "health_check_interval": 60
            }
        } 