"""
Abstract Base Class für mDNS Server
"""
from abc import ABC, abstractmethod
from typing import List
from app.models.service import Service


class MDNSServerBase(ABC):
    """Abstract Base Class für mDNS Server"""
    
    @abstractmethod
    async def start(self) -> None:
        """Starte mDNS Server"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stoppe mDNS Server"""
        pass
    
    @abstractmethod
    async def register_service(self, service: Service) -> bool:
        """Registriere Service via mDNS"""
        pass
    
    @abstractmethod
    async def unregister_service(self, service_id: str) -> bool:
        """Deregistriere Service von mDNS"""
        pass
    
    @abstractmethod
    async def update_service(self, service: Service) -> bool:
        """Aktualisiere Service in mDNS"""
        pass
    
    @abstractmethod
    def get_registered_services(self) -> List[str]:
        """Hole Liste der registrierten Service IDs"""
        pass
    
    @abstractmethod
    def is_service_registered(self, service_id: str) -> bool:
        """Prüfe ob Service registriert ist"""
        pass 