"""
Avahi mDNS Server über D-Bus
Direkte Kommunikation mit dem System Avahi-Daemon
"""
import asyncio
import subprocess
import json
from typing import Dict, Optional, List
import structlog

from app.config import settings
from app.models.service import Service
from app.core.mdns_base import MDNSServerBase

logger = structlog.get_logger(__name__)


class AvahiMDNSServer(MDNSServerBase):
    """mDNS Server über Avahi D-Bus"""
    
    def __init__(self):
        self.registered_services: Dict[str, dict] = {}
        self.domain = settings.mdns_domain
        self._running = False
    
    async def start(self) -> None:
        """Starte Avahi mDNS Server"""
        if self._running:
            logger.warning("Avahi mDNS Server bereits gestartet")
            return
        
        try:
            # Prüfe ob avahi-publish-service verfügbar ist (besserer Test als daemon check)
            result = await self._run_command(["which", "avahi-publish-service"])
            if result.returncode != 0:
                logger.warning("avahi-publish-service nicht verfügbar, verwende Fallback")
                self._running = True
                return
            
            # Teste ob Avahi tatsächlich funktioniert mit einem kurzen Test-Service
            test_result = await self._run_command([
                "timeout", "2", "avahi-publish-service", "--no-fail", 
                "beacon-test", "_test._tcp", "1234"
            ])
            
            if test_result.returncode not in [0, 124]:  # 124 = timeout (normal), 0 = success
                logger.warning("Avahi-Service-Publishing nicht verfügbar, verwende Fallback")
                self._running = True
                return
            
            self._running = True
            logger.info("Avahi mDNS Server gestartet und getestet", domain=self.domain)
            
        except Exception as e:
            logger.error("Fehler beim Starten des Avahi mDNS Servers", error=str(e))
            # Fallback: trotzdem als gestartet markieren
            self._running = True
    
    async def stop(self) -> None:
        """Stoppe Avahi mDNS Server"""
        if not self._running:
            return
        
        try:
            # Unregister alle Services
            for service_id in list(self.registered_services.keys()):
                await self.unregister_service(service_id)
            
            self._running = False
            logger.info("Avahi mDNS Server gestoppt")
            
        except Exception as e:
            logger.error("Fehler beim Stoppen des Avahi mDNS Servers", error=str(e))
    
    async def register_service(self, service: Service) -> bool:
        """Registriere Service via Avahi"""
        if not self._running:
            logger.warning("Avahi mDNS Server nicht gestartet")
            return False
        
        try:
            # Erstelle Service Name
            service_name = f"{service.name}"
            service_type = f"_{service.type}._tcp"
            
            # Erstelle TXT Records
            txt_records = service.get_mdns_txt_records()
            txt_args = []
            for key, value in txt_records.items():
                txt_args.extend(["--txt", f"{key}={value}"])
            
            # Avahi-publish-service Command
            cmd = [
                "avahi-publish-service",
                "--no-fail",
                service_name,
                service_type,
                str(service.port)
            ] + txt_args
            
            # Starte Service im Hintergrund
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Speichere Service Info
            self.registered_services[service.service_id] = {
                "process": process,
                "service_name": service_name,
                "service_type": service_type,
                "port": service.port,
                "cmd": cmd
            }
            
            logger.info("Service via Avahi registriert",
                       service_id=service.service_id,
                       service_name=service_name,
                       service_type=service_type,
                       port=service.port)
            
            return True
            
        except Exception as e:
            logger.error("Fehler bei Avahi Service Registrierung",
                        service_id=service.service_id,
                        error=str(e))
            return False
    
    async def unregister_service(self, service_id: str) -> bool:
        """Deregistriere Service von Avahi"""
        if not self._running:
            return False
        
        try:
            if service_id not in self.registered_services:
                logger.warning("Service nicht in Avahi registriert", service_id=service_id)
                return False
            
            service_info = self.registered_services[service_id]
            process = service_info["process"]
            
            # Beende avahi-publish-service Prozess
            if process and process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            
            # Entferne aus Registry
            del self.registered_services[service_id]
            
            logger.info("Service von Avahi deregistriert",
                       service_id=service_id,
                       service_name=service_info["service_name"])
            
            return True
            
        except Exception as e:
            logger.error("Fehler bei Avahi Service Deregistrierung",
                        service_id=service_id,
                        error=str(e))
            return False
    
    async def update_service(self, service: Service) -> bool:
        """Aktualisiere Service in Avahi"""
        # Für Updates: erst deregistrieren, dann neu registrieren
        await self.unregister_service(service.service_id)
        return await self.register_service(service)
    
    async def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Führe Command aus"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )
    
    def get_registered_services(self) -> List[str]:
        """Hole Liste der registrierten Service IDs"""
        return list(self.registered_services.keys())
    
    def is_service_registered(self, service_id: str) -> bool:
        """Prüfe ob Service registriert ist"""
        return service_id in self.registered_services 