"""
Health Check Model für Bitsperity Beacon
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import Field

from .base import BaseModel


class HealthStatus(str, Enum):
    """Health Check Status Enum"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TIMEOUT = "timeout"
    ERROR = "error"
    UNKNOWN = "unknown"


class HealthCheck(BaseModel):
    """Health Check Model"""
    
    service_id: str = Field(..., description="Service ID")
    status: HealthStatus = Field(..., description="Health Check Status")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    status_code: Optional[int] = Field(None, description="HTTP Status Code")
    error_message: Optional[str] = Field(None, description="Error message if check failed")
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of check")
    check_url: Optional[str] = Field(None, description="URL that was checked")
    
    class Config:
        schema_extra = {
            "example": {
                "service_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "healthy",
                "response_time": 0.123,
                "status_code": 200,
                "checked_at": "2024-01-01T12:00:00Z",
                "check_url": "http://192.168.1.100:8080/health"
            }
        } 