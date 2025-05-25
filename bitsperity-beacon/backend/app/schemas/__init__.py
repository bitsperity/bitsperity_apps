"""
API Schemas für Bitsperity Beacon
"""

from .service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
    HeartbeatResponse
)
from .health_check import HealthCheckResponse
from .discovery import DiscoveryResponse, ServiceDiscoveryFilter

__all__ = [
    "ServiceCreate",
    "ServiceUpdate", 
    "ServiceResponse",
    "ServiceListResponse",
    "HeartbeatResponse",
    "HealthCheckResponse",
    "DiscoveryResponse",
    "ServiceDiscoveryFilter"
] 