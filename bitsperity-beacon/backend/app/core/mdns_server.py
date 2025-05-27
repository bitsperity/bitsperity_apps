"""
mDNS Server für Service Discovery
"""
import asyncio
import socket
from typing import Dict, Optional, List
from zeroconf import ServiceInfo, Zeroconf, IPVersion
from zeroconf.asyncio import AsyncZeroconf
import structlog
import netifaces

from app.config import settings
from app.models.service import Service
from app.core.mdns_base import MDNSServerBase

logger = structlog.get_logger(__name__)


class MDNSServer(MDNSServerBase):
    """mDNS Server für Service Discovery"""
    
    def __init__(self):
        self.zeroconf: Optional[AsyncZeroconf] = None
        self.registered_services: Dict[str, ServiceInfo] = {}
        self.domain = settings.mdns_domain
        self._running = False
    
    async def start(self) -> None:
        """Starte mDNS Server"""
        if self._running:
            logger.warning("mDNS Server bereits gestartet")
            return
        
        try:
            # Erstelle AsyncZeroconf Instanz
            self.zeroconf = AsyncZeroconf(ip_version=IPVersion.V4Only)
            self._running = True
            
            logger.info("mDNS Server gestartet", domain=self.domain)
            
        except Exception as e:
            logger.error("Fehler beim Starten des mDNS Servers", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stoppe mDNS Server"""
        if not self._running:
            return
        
        try:
            # Unregister alle Services
            for service_id in list(self.registered_services.keys()):
                await self.unregister_service(service_id)
            
            # Schließe Zeroconf
            if self.zeroconf:
                await self.zeroconf.async_close()
                self.zeroconf = None
            
            self._running = False
            logger.info("mDNS Server gestoppt")
            
        except Exception as e:
            logger.error("Fehler beim Stoppen des mDNS Servers", error=str(e))
    
    async def register_service(self, service: Service) -> bool:
        """Registriere Service via mDNS"""
        if not self._running or not self.zeroconf:
            logger.warning("mDNS Server nicht gestartet")
            return False
        
        try:
            # Erstelle Service Name
            service_name = f"{service.name}.{service.mdns_service_type}.{self.domain}."
            
            # Hole lokale IP Adresse
            local_ip = self._get_local_ip()
            if not local_ip:
                logger.error("Keine lokale IP Adresse gefunden")
                return False
            
            # Erstelle TXT Records
            txt_records = service.get_mdns_txt_records()
            
            # Konvertiere TXT Records zu bytes
            properties = {}
            for key, value in txt_records.items():
                if isinstance(value, str):
                    properties[key.encode('utf-8')] = value.encode('utf-8')
                else:
                    properties[key.encode('utf-8')] = str(value).encode('utf-8')
            
            # Erstelle ServiceInfo - verwende lokale IP statt service.host
            service_info = ServiceInfo(
                type_=f"{service.mdns_service_type}.{self.domain}.",
                name=service_name,
                addresses=[socket.inet_aton(local_ip)],
                port=service.port,
                properties=properties,
                server=f"{socket.gethostname()}.{self.domain}."
            )
            
            # Registriere Service
            await self.zeroconf.async_register_service(service_info)
            
            # Speichere Service Info
            self.registered_services[service.service_id] = service_info
            
            logger.info("Service via mDNS registriert",
                       service_id=service.service_id,
                       service_name=service_name,
                       service_type=service.mdns_service_type,
                       host=service.host,
                       port=service.port)
            
            return True
            
        except Exception as e:
            logger.error("Fehler bei mDNS Service Registrierung",
                        service_id=service.service_id,
                        error=str(e))
            return False
    
    async def unregister_service(self, service_id: str) -> bool:
        """Deregistriere Service von mDNS"""
        if not self._running or not self.zeroconf:
            return False
        
        try:
            if service_id not in self.registered_services:
                logger.warning("Service nicht in mDNS registriert", service_id=service_id)
                return False
            
            service_info = self.registered_services[service_id]
            
            # Unregister Service
            await self.zeroconf.async_unregister_service(service_info)
            
            # Entferne aus Registry
            del self.registered_services[service_id]
            
            logger.info("Service von mDNS deregistriert",
                       service_id=service_id,
                       service_name=service_info.name)
            
            return True
            
        except Exception as e:
            logger.error("Fehler bei mDNS Service Deregistrierung",
                        service_id=service_id,
                        error=str(e))
            return False
    
    async def update_service(self, service: Service) -> bool:
        """Aktualisiere Service in mDNS"""
        # Für Updates: erst deregistrieren, dann neu registrieren
        await self.unregister_service(service.service_id)
        return await self.register_service(service)
    
    def _get_local_ip(self) -> Optional[str]:
        """Hole lokale IP Adresse"""
        try:
            # Versuche spezifisches Interface wenn konfiguriert
            if settings.mdns_interface:
                try:
                    addrs = netifaces.ifaddresses(settings.mdns_interface)
                    if netifaces.AF_INET in addrs:
                        return addrs[netifaces.AF_INET][0]['addr']
                except Exception:
                    pass
            
            # Fallback: automatische Erkennung
            # Erstelle temporäre Socket Verbindung um lokale IP zu ermitteln
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
                
        except Exception as e:
            logger.error("Fehler beim Ermitteln der lokalen IP", error=str(e))
            return None
    
    def get_registered_services(self) -> List[str]:
        """Hole Liste der registrierten Service IDs"""
        return list(self.registered_services.keys())
    
    def is_service_registered(self, service_id: str) -> bool:
        """Prüfe ob Service registriert ist"""
        return service_id in self.registered_services 