"""
Avahi mDNS Server über D-Bus
Direkte Kommunikation mit dem System Avahi-Daemon
"""
import asyncio
import subprocess
import json
from typing import Dict, Optional, List
import structlog
import os

from app.config import settings
from app.models.service import Service

logger = structlog.get_logger(__name__)


class AvahiMDNSServer:
    """mDNS Server über Avahi D-Bus"""
    
    def __init__(self):
        self.registered_services: Dict[str, dict] = {}
        self.domain = settings.mdns_domain
        self._running = False
        self._avahi_available = False
    
    async def start(self) -> None:
        """Starte Avahi mDNS Server"""
        if self._running:
            logger.warning("Avahi mDNS Server bereits gestartet")
            return
        
        try:
            # Prüfe ob Avahi-Daemon verfügbar ist
            # Versuche zuerst über D-Bus zu prüfen
            if os.path.exists("/var/run/dbus/system_bus_socket"):
                result = await self._run_command(["avahi-daemon", "--check"])
                if result.returncode == 0:
                    self._avahi_available = True
                    logger.info("Avahi-Daemon verfügbar")
                else:
                    # Versuche Avahi zu starten
                    logger.info("Versuche Avahi-Daemon zu starten")
                    start_result = await self._run_command(["avahi-daemon", "-D"])
                    if start_result.returncode == 0:
                        self._avahi_available = True
                        logger.info("Avahi-Daemon erfolgreich gestartet")
                    else:
                        logger.warning("Avahi-Daemon konnte nicht gestartet werden", 
                                     stderr=start_result.stderr.decode() if start_result.stderr else "")
            else:
                logger.warning("D-Bus System Socket nicht gefunden")
            
            if not self._avahi_available:
                logger.warning("Avahi-Daemon nicht verfügbar, mDNS-Funktionalität deaktiviert")
            
            self._running = True
            logger.info("Avahi mDNS Server gestartet", 
                       domain=self.domain, 
                       avahi_available=self._avahi_available)
            
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
        
        if not self._avahi_available:
            logger.debug("Avahi nicht verfügbar, überspringe mDNS-Registrierung", 
                        service_id=service.service_id)
            return True  # Return True, damit der Service trotzdem registriert wird
        
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
            
            # Prüfe ob der Prozess erfolgreich gestartet wurde
            await asyncio.sleep(0.5)  # Kurz warten
            if process.returncode is not None and process.returncode != 0:
                stderr = await process.stderr.read()
                logger.error("Avahi-publish-service fehlgeschlagen",
                           service_id=service.service_id,
                           returncode=process.returncode,
                           stderr=stderr.decode() if stderr else "")
                return False
            
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
        
        if not self._avahi_available:
            return True  # Return True wenn Avahi nicht verfügbar
        
        try:
            if service_id not in self.registered_services:
                logger.debug("Service nicht in Avahi registriert", service_id=service_id)
                return True
            
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
        if not self._avahi_available:
            return True  # Return True wenn Avahi nicht verfügbar
            
        # Für Updates: erst deregistrieren, dann neu registrieren
        await self.unregister_service(service.service_id)
        return await self.register_service(service)
    
    async def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Führe Command aus"""
        try:
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
        except Exception as e:
            logger.error("Fehler beim Ausführen von Command", cmd=cmd, error=str(e))
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout=b"",
                stderr=str(e).encode()
            )
    
    def get_registered_services(self) -> List[str]:
        """Hole Liste der registrierten Service IDs"""
        return list(self.registered_services.keys())
    
    def is_service_registered(self, service_id: str) -> bool:
        """Prüfe ob Service registriert ist"""
        return service_id in self.registered_services 