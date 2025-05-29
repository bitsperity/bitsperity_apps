"""
TTL Manager für automatische Service-Cleanup
Enhanced with Health Check Fallback Support
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import structlog

from app.config import settings
from app.core.service_registry import ServiceRegistry

if TYPE_CHECKING:
    from app.core.health_check_manager import HealthCheckManager

logger = structlog.get_logger(__name__)


class TTLManager:
    """TTL Manager für automatische Service-Cleanup mit Health Check Fallback"""
    
    def __init__(self, service_registry: ServiceRegistry, health_check_manager: Optional["HealthCheckManager"] = None):
        self.service_registry = service_registry
        self.health_check_manager = health_check_manager  # 🆕 Optional health check manager
        self.cleanup_interval = settings.beacon_ttl_cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    def set_health_check_manager(self, health_check_manager: "HealthCheckManager") -> None:
        """Set health check manager (can be called after initialization)"""
        self.health_check_manager = health_check_manager
    
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
        """Führe Cleanup durch mit Health Check Fallback"""
        try:
            start_time = datetime.now(timezone.utc)
            
            # 🆕 NEW: Health Check Fallback Strategy
            if self.health_check_manager:
                await self._try_health_check_fallback()
            
            # Regular cleanup abgelaufene Services
            removed_count = await self.service_registry.cleanup_expired_services()
            
            cleanup_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            if removed_count > 0:
                logger.info("TTL Cleanup durchgeführt", 
                           removed_services=removed_count,
                           duration_seconds=cleanup_duration)
            else:
                logger.debug("TTL Cleanup durchgeführt - keine abgelaufenen Services",
                            duration_seconds=cleanup_duration)
                
        except Exception as e:
            logger.error("Fehler beim TTL Cleanup", error=str(e))
    
    async def _try_health_check_fallback(self) -> None:
        """🆕 NEW: Try health check fallback for services near expiry"""
        try:
            # Get services approaching expiry that have health checks
            near_expiry_services = await self.service_registry.get_services_near_expiry()
            
            if not near_expiry_services:
                return
            
            logger.info("Trying health check fallback for services near expiry", 
                       count=len(near_expiry_services))
            
            # Try health checks concurrently (with limit)
            semaphore = asyncio.Semaphore(3)  # Max 3 concurrent health checks
            
            async def try_health_check_for_service(service):
                async with semaphore:
                    try:
                        result = await self.health_check_manager.check_service_now(service.service_id)
                        if result and result.success:
                            logger.info("Health check fallback saved service from expiry",
                                       service_id=service.service_id, 
                                       name=service.name)
                        else:
                            logger.warning("Health check fallback failed - service will expire",
                                         service_id=service.service_id,
                                         name=service.name)
                    except Exception as e:
                        logger.error("Error in health check fallback",
                                   service_id=service.service_id, error=str(e))
            
            # Execute health checks
            tasks = [try_health_check_for_service(service) for service in near_expiry_services]
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error("Error in health check fallback strategy", error=str(e))
    
    async def force_cleanup(self) -> int:
        """Erzwinge sofortigen Cleanup"""
        logger.info("Erzwinge TTL Cleanup")
        await self._perform_cleanup()
        return await self.service_registry.cleanup_expired_services() 