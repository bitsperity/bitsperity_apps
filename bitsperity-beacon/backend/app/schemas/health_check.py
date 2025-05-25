"""
Health Check API Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.health_check import HealthStatus


class HealthCheckResponse(BaseModel):
    """Schema für Health Check Response"""
    
    service_id: str
    status: HealthStatus
    response_time: Optional[float]
    status_code: Optional[int]
    error_message: Optional[str]
    checked_at: datetime
    check_url: Optional[str]
    
    class Config:
        from_attributes = True 