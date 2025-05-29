"""
Service Model für Bitsperity Beacon
"""
from datetime import datetime, timedelta, timezone
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
    last_heartbeat: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Status
    status: ServiceStatus = Field(default=ServiceStatus.ACTIVE)
    health_check_url: Optional[str] = None
    health_check_interval: Optional[int] = Field(default=60, ge=30, le=3600)
    
    # 🆕 NEW: Health Check Enhancement (minimal, optional fields)
    health_check_timeout: Optional[int] = Field(default=10, ge=1, le=60)
    health_check_retries: Optional[int] = Field(default=3, ge=1, le=10)
    last_health_check: Optional[datetime] = None
    consecutive_health_failures: int = Field(default=0)
    health_check_enabled: bool = Field(default=True)  # Can disable health checks
    fallback_to_health_check: bool = Field(default=True)  # Use health check before expiry
    
    # mDNS Information
    mdns_service_type: Optional[str] = None
    mdns_txt_records: Dict[str, str] = Field(default_factory=dict)
    
    @validator('expires_at', pre=True, always=True)
    def set_expires_at(cls, v, values):
        """Setze expires_at basierend auf TTL"""
        if v is None:
            ttl = values.get('ttl', 300)  # Default TTL falls nicht gesetzt
            return datetime.now(timezone.utc) + timedelta(seconds=ttl)
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
        return datetime.now(timezone.utc) > self.expires_at
    
    # 🆕 NEW: Health Check Helper Methods
    def needs_health_check(self) -> bool:
        """Check if service needs a health check"""
        if not self.health_check_url or not self.health_check_enabled:
            return False
            
        if not self.last_health_check:
            return True
            
        interval = timedelta(seconds=self.health_check_interval)
        return datetime.now(timezone.utc) > (self.last_health_check + interval)
    
    def is_near_expiry(self) -> bool:
        """Check if service is near TTL expiry (within 1.5 health check intervals)"""
        if not self.health_check_url or not self.fallback_to_health_check:
            return False
            
        grace_period = timedelta(seconds=int(self.health_check_interval * 1.5))
        return datetime.now(timezone.utc) > (self.expires_at - grace_period)
    
    def can_use_health_check_fallback(self) -> bool:
        """Check if health check can be used as TTL fallback"""
        return (
            self.health_check_url is not None and 
            self.health_check_enabled and 
            self.fallback_to_health_check and
            self.consecutive_health_failures < self.health_check_retries
        )
    
    def extend_ttl(self, ttl: Optional[int] = None) -> None:
        """Verlängere TTL des Services"""
        if ttl is None:
            ttl = self.ttl
        
        self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        self.last_heartbeat = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        if self.status == ServiceStatus.EXPIRED:
            self.status = ServiceStatus.ACTIVE
    
    def mark_expired(self) -> None:
        """Markiere Service als abgelaufen"""
        self.status = ServiceStatus.EXPIRED
        self.updated_at = datetime.now(timezone.utc)
    
    # 🆕 NEW: Health Check Status Methods
    def update_health_check_success(self) -> None:
        """Update service after successful health check"""
        self.last_health_check = datetime.now(timezone.utc)
        self.consecutive_health_failures = 0
        self.updated_at = datetime.now(timezone.utc)
        
        # Extend TTL like a heartbeat!
        self.extend_ttl()
        
        # Restore to active if was unhealthy
        if self.status == ServiceStatus.UNHEALTHY:
            self.status = ServiceStatus.ACTIVE
    
    def update_health_check_failure(self) -> None:
        """Update service after failed health check"""
        self.last_health_check = datetime.now(timezone.utc)
        self.consecutive_health_failures += 1
        self.updated_at = datetime.now(timezone.utc)
        
        # Mark as unhealthy after retries exhausted
        if self.consecutive_health_failures >= self.health_check_retries:
            self.status = ServiceStatus.UNHEALTHY
    
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
                "health_check_interval": 60,
                "health_check_timeout": 10,
                "health_check_enabled": True,
                "fallback_to_health_check": True
            }
        } 