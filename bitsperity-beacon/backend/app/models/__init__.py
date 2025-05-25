"""
Datenmodelle für Bitsperity Beacon
"""

from .service import Service, ServiceStatus
from .health_check import HealthCheck, HealthStatus
from .base import BaseModel

__all__ = [
    "Service",
    "ServiceStatus", 
    "HealthCheck",
    "HealthStatus",
    "BaseModel"
] 