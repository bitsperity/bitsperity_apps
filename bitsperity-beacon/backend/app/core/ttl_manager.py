"""
TTL Manager für automatische Service-Cleanup
"""
import asyncio
from datetime import datetime
from typing import Optional
import structlog

from app.config import settings
from app.core.service_registry import ServiceRegistry

logger = structlog.get_logger(__name__)


class TTLManager:
    """TTL Manager für automatische Service-Cleanup"""
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self.cleanup_interval = settings.beacon_ttl_cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Starte TTL Manager"""
        if self._running:
            logger.warning("TTL Manager bereits gestartet")
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("TTL Manager gestartet", cleanup_interval=self.cleanup_interval)
    
    async def stop(self) -> None:
        """Stoppe TTL Manager"""
        if not self._running:
            return
        
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("TTL Manager gestoppt")
    
    async def _cleanup_loop(self) -> None:
        """Cleanup Loop"""
        while self._running:
            try:
                await self._perform_cleanup()
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Fehler im TTL Cleanup Loop", error=str(e))
                await asyncio.sleep(self.cleanup_interval)
    
    async def _perform_cleanup(self) -> None:
        """Führe Cleanup durch"""
        try:
            start_time = datetime.utcnow()
            
            # Cleanup abgelaufene Services
            removed_count = await self.service_registry.cleanup_expired_services()
            
            cleanup_duration = (datetime.utcnow() - start_time).total_seconds()
            
            if removed_count > 0:
                logger.info("TTL Cleanup durchgeführt", 
                           removed_services=removed_count,
                           duration_seconds=cleanup_duration)
            else:
                logger.debug("TTL Cleanup durchgeführt - keine abgelaufenen Services",
                            duration_seconds=cleanup_duration)
                
        except Exception as e:
            logger.error("Fehler beim TTL Cleanup", error=str(e))
    
    async def force_cleanup(self) -> int:
        """Erzwinge sofortigen Cleanup"""
        logger.info("Erzwinge TTL Cleanup")
        await self._perform_cleanup()
        return await self.service_registry.cleanup_expired_services() 