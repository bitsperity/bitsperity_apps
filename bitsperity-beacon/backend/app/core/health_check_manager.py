"""
Health Check Manager für Bitsperity Beacon
Minimal invasive Implementierung als separater Service
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta, timezone
import structlog

if TYPE_CHECKING:
    from app.core.service_registry import ServiceRegistry
    from app.core.websocket_manager import WebSocketManager

logger = structlog.get_logger(__name__)


class HealthCheckResult:
    """Result of a health check operation"""
    
    def __init__(self, success: bool, response_time_ms: int, 
                 status_code: Optional[int] = None, error: Optional[str] = None):
        self.success = success
        self.response_time_ms = response_time_ms
        self.status_code = status_code
        self.error = error
        self.timestamp = datetime.now(timezone.utc)


class HealthCheckManager:
    """
    Manages health checks for services with health_check_url
    Works alongside existing heartbeat system without interference
    """
    
    def __init__(self, service_registry: "ServiceRegistry", websocket_manager: "WebSocketManager"):
        self.service_registry = service_registry
        self.websocket_manager = websocket_manager
        self._running = False
        self._session: Optional[aiohttp.ClientSession] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start health check manager"""
        if self._running:
            logger.warning("Health Check Manager already running")
            return
            
        try:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )
            self._running = True
            
            # Start health check loop
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info("Health Check Manager started")
            
        except Exception as e:
            logger.error("Failed to start Health Check Manager", error=str(e))
            raise
    
    async def stop(self):
        """Stop health check manager"""
        if not self._running:
            return
            
        try:
            self._running = False
            
            # Cancel health check task
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Close HTTP session
            if self._session:
                await self._session.close()
                self._session = None
                
            logger.info("Health Check Manager stopped")
            
        except Exception as e:
            logger.error("Error stopping Health Check Manager", error=str(e))
    
    async def _health_check_loop(self):
        """Main health check loop - checks services periodically"""
        while self._running:
            try:
                # Get all services that need health checks
                services = await self._get_services_needing_health_check()
                
                # Process health checks concurrently (but with limits)
                if services:
                    await self._process_health_checks(services)
                
                # Wait before next round (check every 30 seconds)
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check loop error", error=str(e))
                await asyncio.sleep(10)  # Brief pause on error
    
    async def _get_services_needing_health_check(self) -> List:
        """Get services that need health checks"""
        try:
            # Get all active services
            services = await self.service_registry.get_all_active_services()
            
            needs_check = []
            for service in services:
                # Only check services with health check configuration
                if not service.health_check_url or not service.health_check_enabled:
                    continue
                
                # Check if health check is due OR service is near expiry
                if service.needs_health_check() or service.is_near_expiry():
                    needs_check.append(service)
            
            if needs_check:
                logger.debug("Services needing health check", 
                           count=len(needs_check),
                           services=[s.name for s in needs_check])
            
            return needs_check
            
        except Exception as e:
            logger.error("Error getting services for health check", error=str(e))
            return []
    
    async def _process_health_checks(self, services: List):
        """Process health checks for multiple services concurrently"""
        # Limit concurrent health checks to avoid overwhelming
        semaphore = asyncio.Semaphore(5)
        
        async def check_service(service):
            async with semaphore:
                await self._check_service_health(service)
        
        # Run health checks concurrently
        tasks = [check_service(service) for service in services]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_service_health(self, service):
        """Perform health check for a single service"""
        try:
            logger.debug("Performing health check", 
                        service_id=service.service_id, 
                        url=service.health_check_url)
            
            result = await self._perform_http_health_check(service)
            await self._process_health_check_result(service, result)
            
        except Exception as e:
            logger.error("Error in service health check", 
                        service_id=service.service_id, error=str(e))
    
    async def _perform_http_health_check(self, service) -> HealthCheckResult:
        """Perform actual HTTP health check"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=service.health_check_timeout)
            
            async with self._session.get(
                service.health_check_url, 
                timeout=timeout
            ) as response:
                response_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
                
                # Consider 2xx status codes as healthy
                success = 200 <= response.status < 300
                
                return HealthCheckResult(
                    success=success,
                    response_time_ms=response_time,
                    status_code=response.status
                )
                
        except asyncio.TimeoutError:
            response_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return HealthCheckResult(
                success=False,
                response_time_ms=response_time,
                error="Health check timeout"
            )
        except Exception as e:
            response_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return HealthCheckResult(
                success=False,
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def _process_health_check_result(self, service, result: HealthCheckResult):
        """Process health check result and update service"""
        try:
            if result.success:
                # Health check successful!
                logger.info("Health check passed - extending TTL like heartbeat",
                           service_id=service.service_id,
                           name=service.name,
                           response_time=result.response_time_ms)
                
                # Update service health status
                service.update_health_check_success()
                
                # Save to database
                await self.service_registry.update_service_health_status(service)
                
                # Broadcast success via WebSocket (optional)
                try:
                    await self.websocket_manager.broadcast_health_status_changed({
                        "service_id": service.service_id,
                        "name": service.name,
                        "status": "healthy",
                        "response_time_ms": result.response_time_ms,
                        "method": "health_check"
                    })
                except Exception as ws_error:
                    logger.debug("WebSocket broadcast failed", error=str(ws_error))
                
            else:
                # Health check failed
                logger.warning("Health check failed",
                             service_id=service.service_id,
                             name=service.name,
                             consecutive_failures=service.consecutive_health_failures + 1,
                             error=result.error)
                
                # Update service health status
                service.update_health_check_failure()
                
                # Save to database
                await self.service_registry.update_service_health_status(service)
                
                # Broadcast failure if service becomes unhealthy
                if service.status.value == "unhealthy":
                    try:
                        await self.websocket_manager.broadcast_health_status_changed({
                            "service_id": service.service_id,
                            "name": service.name,
                            "status": "unhealthy",
                            "consecutive_failures": service.consecutive_health_failures,
                            "error": result.error
                        })
                    except Exception as ws_error:
                        logger.debug("WebSocket broadcast failed", error=str(ws_error))
                
        except Exception as e:
            logger.error("Error processing health check result",
                        service_id=service.service_id, error=str(e))
    
    async def check_service_now(self, service_id: str) -> Optional[HealthCheckResult]:
        """Manually trigger health check for a specific service"""
        try:
            service = await self.service_registry.get_service_by_id(service_id)
            if not service or not service.health_check_url:
                return None
            
            result = await self._perform_http_health_check(service)
            await self._process_health_check_result(service, result)
            
            return result
            
        except Exception as e:
            logger.error("Error in manual health check", service_id=service_id, error=str(e))
            return None 