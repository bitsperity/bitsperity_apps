"""
Service Registry für Bitsperity Beacon
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import structlog
from bson import ObjectId

from app.database import Database
from app.models.service import Service, ServiceStatus
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.config import settings
from app.core.json_encoder import jsonable_encoder

logger = structlog.get_logger(__name__)


def prepare_service_doc(doc: dict) -> dict:
    """Bereite Service Document für Pydantic Model vor"""
    # Convert MongoDB _id to string if present
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    
    # Ensure expires_at is datetime object for comparison
    if "expires_at" in doc and isinstance(doc["expires_at"], str):
        doc["expires_at"] = datetime.fromisoformat(doc["expires_at"].replace('Z', '+00:00'))
    
    # Ensure last_heartbeat is datetime object if present
    if "last_heartbeat" in doc and isinstance(doc["last_heartbeat"], str):
        doc["last_heartbeat"] = datetime.fromisoformat(doc["last_heartbeat"].replace('Z', '+00:00'))
    
    # FIX: Recalculate mdns_service_type for legacy services that may have wrong values
    if "type" in doc:
        service_type = doc["type"].lower()
        
        # Standard mDNS Service Type Mappings (same as in Service model)
        type_mappings = {
            'mqtt': '_mqtt._tcp',
            'http': '_http._tcp',
            'https': '_https._tcp',
            'iot': '_iot._tcp',
            'api': '_http._tcp',
            'web': '_http._tcp',
            'database': '_db._tcp',
            'cache': '_cache._tcp',
            'message_queue': '_mq._tcp'
        }
        
        correct_mdns_type = type_mappings.get(service_type, f'_{service_type}._tcp')
        
        # Always set the correct mdns_service_type (overwrites any legacy wrong values)
        doc["mdns_service_type"] = correct_mdns_type
    
    return doc


class ServiceRegistry:
    """Service Registry Manager"""
    
    def __init__(self, database: Database, mdns_server=None):
        self.database = database
        self.mdns_server = mdns_server  # Optional mDNS Server für Cleanup
        self._services_cache: Dict[str, Service] = {}
        self._cache_ttl = 60  # Cache TTL in seconds
        self._last_cache_update = datetime.now(timezone.utc)
    
    async def register_service(self, service_data: ServiceCreate) -> Service:
        """Registriere einen neuen Service"""
        try:
            logger.info("=== REGISTRY: Creating Service Model ===")
            # Erstelle Service Model
            service = Service(**service_data.model_dump())
            logger.info("Service model created", service_id=service.service_id)
            
            # Prüfe ob Service bereits existiert
            existing = await self.get_service_by_name_and_host(service.name, service.host, service.port)
            if existing:
                logger.info("Service bereits registriert, aktualisiere", 
                           service_id=existing.service_id, name=service.name)
                return await self.update_service(existing.service_id, service_data)
            
            # Speichere in Database
            logger.info("=== REGISTRY: Saving to Database ===")
            service_dict = jsonable_encoder(service.model_dump(by_alias=True))
            logger.info("Service dict created for database", dict_keys=list(service_dict.keys()))
            result = await self.database.services.insert_one(service_dict)
            logger.info("Service saved to database", inserted_id=str(result.inserted_id))
            
            # Update Cache
            self._services_cache[service.service_id] = service
            
            logger.info("Service registriert", 
                       service_id=service.service_id, 
                       name=service.name,
                       type=service.type,
                       host=service.host,
                       port=service.port,
                       expires_at=service.expires_at)
            
            return service
            
        except Exception as e:
            logger.error("Fehler bei Service Registrierung", error=str(e))
            raise
    
    async def get_service_by_id(self, service_id: str) -> Optional[Service]:
        """Hole Service by ID"""
        try:
            # Prüfe Cache zuerst
            if service_id in self._services_cache:
                service = self._services_cache[service_id]
                if not service.is_expired():
                    return service
                else:
                    # Entferne abgelaufenen Service aus Cache
                    del self._services_cache[service_id]
            
            # Hole aus Database
            service_doc = await self.database.services.find_one({"service_id": service_id})
            if not service_doc:
                return None
            
            # Bereite Dokument vor
            service_doc = prepare_service_doc(service_doc)
            service = Service(**service_doc)
            
            # Prüfe ob abgelaufen
            if service.is_expired():
                await self.deregister_service(service_id)
                return None
            
            # Update Cache
            self._services_cache[service_id] = service
            return service
            
        except Exception as e:
            logger.error("Fehler beim Laden des Services", service_id=service_id, error=str(e))
            return None
    
    async def get_service_by_name_and_host(self, name: str, host: str, port: int) -> Optional[Service]:
        """Hole Service by Name, Host und Port"""
        try:
            service_doc = await self.database.services.find_one({
                "name": name,
                "host": host,
                "port": port,
                "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
            })
            
            if not service_doc:
                return None
            
            # Bereite Dokument vor
            service_doc = prepare_service_doc(service_doc)
            service = Service(**service_doc)
            self._services_cache[service.service_id] = service
            return service
            
        except Exception as e:
            logger.error("Fehler beim Laden des Services", name=name, host=host, port=port, error=str(e))
            return None
    
    async def update_service(self, service_id: str, update_data: ServiceUpdate) -> Optional[Service]:
        """Aktualisiere Service"""
        try:
            service = await self.get_service_by_id(service_id)
            if not service:
                return None
            
            # Update Felder
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(service, field, value)
            
            service.updated_at = datetime.now(timezone.utc)
            
            # Speichere in Database
            service_dict = jsonable_encoder(service.model_dump(by_alias=True, exclude={"_id"}))
            await self.database.services.update_one(
                {"service_id": service_id},
                {"$set": service_dict}
            )
            
            # Update Cache
            self._services_cache[service_id] = service
            
            logger.info("Service aktualisiert", service_id=service_id)
            return service
            
        except Exception as e:
            logger.error("Fehler beim Aktualisieren des Services", service_id=service_id, error=str(e))
            return None
    
    async def extend_service_ttl(self, service_id: str, ttl: Optional[int] = None) -> Optional[Service]:
        """Verlängere Service TTL (Heartbeat)"""
        try:
            service = await self.get_service_by_id(service_id)
            if not service:
                return None
            
            # Verlängere TTL
            service.extend_ttl(ttl)
            
            # Speichere in Database
            update_dict = {
                "expires_at": service.expires_at,
                "last_heartbeat": service.last_heartbeat,
                "updated_at": service.updated_at,
                "status": service.status.value
            }
            update_dict = jsonable_encoder(update_dict)
            await self.database.services.update_one(
                {"service_id": service_id},
                {"$set": update_dict}
            )
            
            # Update Cache
            self._services_cache[service_id] = service
            
            # ⚡ Re-register to mDNS for robustness (ensures service stays in mDNS)
            if self.mdns_server and service.status.value == "active":
                try:
                    print(f"🔥 DEBUG: TTL-Extend - Re-registering service {service.name} to mDNS for robustness...")
                    mdns_success = await self.mdns_server.register_service(service)
                    if mdns_success:
                        print(f"🔥 DEBUG: TTL-Extend - mDNS re-registration SUCCESS for {service.name}")
                    else:
                        print(f"🔥 DEBUG: TTL-Extend - mDNS re-registration FAILED for {service.name}")
                except Exception as mdns_error:
                    logger.warning("mDNS re-registration failed during TTL extend", 
                                 service_id=service_id, error=str(mdns_error))
            
            print(f"🔥 DEBUG: Service TTL extended! service_id={service_id}, expires_at={service.expires_at}")
            logger.warning("🔥 MYSTERY: Service TTL verlängert", service_id=service_id, expires_at=service.expires_at)
            return service
            
        except Exception as e:
            logger.error("Fehler beim Verlängern der Service TTL", service_id=service_id, error=str(e))
            return None
    
    async def deregister_service(self, service_id: str) -> bool:
        """Deregistriere Service"""
        try:
            # Entferne aus Database
            result = await self.database.services.delete_one({"service_id": service_id})
            
            # Entferne aus Cache
            if service_id in self._services_cache:
                del self._services_cache[service_id]
            
            logger.info("Service deregistriert", service_id=service_id)
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error("Fehler beim Deregistrieren des Services", service_id=service_id, error=str(e))
            return False
    
    async def discover_services(self, 
                              service_type: Optional[str] = None,
                              tags: Optional[List[str]] = None,
                              protocol: Optional[str] = None,
                              status: Optional[str] = None,
                              limit: int = 50,
                              skip: int = 0) -> List[Service]:
        """Entdecke Services mit Filtern"""
        try:
            # Build query - convert datetime to ISO string for MongoDB comparison
            current_time = datetime.now(timezone.utc)
            query = {"expires_at": {"$gt": current_time.isoformat()}}
            
            if service_type:
                query["type"] = service_type
            
            if protocol:
                query["protocol"] = protocol
                
            if status:
                query["status"] = status
            
            if tags:
                query["tags"] = {"$in": tags}
            
            # Query Database
            cursor = self.database.services.find(query).skip(skip).limit(limit)
            services_docs = await cursor.to_list(length=limit)
            
            # Prepare documents and create Service objects
            services = []
            for doc in services_docs:
                try:
                    prepared_doc = prepare_service_doc(doc)
                    service = Service(**prepared_doc)
                    services.append(service)
                except Exception as e:
                    logger.error("Fehler beim Erstellen des Service-Objekts", 
                               doc_id=str(doc.get("_id", "unknown")), error=str(e))
                    continue
            
            # Update Cache
            for service in services:
                self._services_cache[service.service_id] = service
            
            logger.debug("Services entdeckt", count=len(services), filters=query)
            return services
            
        except Exception as e:
            logger.error("Fehler beim Entdecken der Services", error=str(e))
            return []
    
    async def get_all_active_services(self) -> List[Service]:
        """Hole alle aktiven Services"""
        return await self.discover_services(status=ServiceStatus.ACTIVE.value)
    
    async def get_all_services(self) -> List[Service]:
        """Hole alle Services (unabhängig vom Status) für Startup Re-Registration"""
        try:
            cursor = self.database.services.find({})
            services_docs = await cursor.to_list(length=None)
            
            # Prepare documents and create Service objects
            services = []
            for doc in services_docs:
                try:
                    prepared_doc = prepare_service_doc(doc)
                    service = Service(**prepared_doc)
                    services.append(service)
                except Exception as e:
                    logger.error("Fehler beim Erstellen des Service-Objekts", 
                               doc_id=str(doc.get("_id", "unknown")), error=str(e))
                    continue
            
            # Update Cache für aktive Services
            for service in services:
                if not service.is_expired():
                    self._services_cache[service.service_id] = service
            
            logger.debug("Alle Services geladen für Startup", count=len(services))
            return services
            
        except Exception as e:
            logger.error("Fehler beim Laden aller Services", error=str(e))
            return []
    
    async def get_expired_services(self) -> List[Service]:
        """Hole alle abgelaufenen Services"""
        try:
            cursor = self.database.services.find({
                "expires_at": {"$lt": datetime.now(timezone.utc).isoformat()}
            })
            services_docs = await cursor.to_list(length=None)
            
            # Prepare documents and create Service objects
            services = []
            for doc in services_docs:
                try:
                    prepared_doc = prepare_service_doc(doc)
                    service = Service(**prepared_doc)
                    services.append(service)
                except Exception as e:
                    logger.error("Fehler beim Erstellen des Service-Objekts für abgelaufenen Service", 
                               doc_id=str(doc.get("_id", "unknown")), error=str(e))
                    continue
            
            return services
            
        except Exception as e:
            logger.error("Fehler beim Laden abgelaufener Services", error=str(e))
            return []
    
    async def cleanup_expired_services(self) -> int:
        """Entferne abgelaufene Services"""
        try:
            # Hole abgelaufene Services
            expired_services = await self.get_expired_services()
            
            if not expired_services:
                return 0
            
            service_ids = [service.service_id for service in expired_services]
            
            # 1. Entferne aus mDNS (falls verfügbar)
            mdns_cleanup_count = 0
            if self.mdns_server:
                for service in expired_services:
                    try:
                        print(f"DEBUG: TTL-Cleanup - Deregistering mDNS service {service.service_id}")
                        mdns_success = await self.mdns_server.unregister_service(service.service_id)
                        if mdns_success:
                            mdns_cleanup_count += 1
                            print(f"DEBUG: TTL-Cleanup - mDNS deregistration SUCCESS for {service.service_id}")
                        else:
                            print(f"DEBUG: TTL-Cleanup - mDNS deregistration FAILED for {service.service_id}")
                    except Exception as mdns_error:
                        logger.error("Fehler beim mDNS Cleanup", 
                                   service_id=service.service_id, 
                                   error=str(mdns_error))
            
            # 2. Entferne aus Database
            result = await self.database.services.delete_many({
                "service_id": {"$in": service_ids}
            })
            
            # 3. Entferne aus Cache
            for service_id in service_ids:
                if service_id in self._services_cache:
                    del self._services_cache[service_id]
            
            logger.info("Abgelaufene Services entfernt", 
                       count=result.deleted_count,
                       mdns_cleanup_count=mdns_cleanup_count)
            print(f"DEBUG: TTL-Cleanup completed - DB: {result.deleted_count}, mDNS: {mdns_cleanup_count}")
            return result.deleted_count
            
        except Exception as e:
            logger.error("Fehler beim Cleanup abgelaufener Services", error=str(e))
            return 0
    
    async def get_service_types(self) -> List[str]:
        """Hole alle verfügbaren Service Types"""
        try:
            types = await self.database.services.distinct("type", {
                "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
            })
            return sorted(types)
            
        except Exception as e:
            logger.error("Fehler beim Laden der Service Types", error=str(e))
            return []
    
    async def get_service_tags(self) -> List[str]:
        """Hole alle verfügbaren Tags"""
        try:
            # Aggregation Pipeline für alle Tags
            pipeline = [
                {"$match": {"expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}}},
                {"$unwind": "$tags"},
                {"$group": {"_id": "$tags"}},
                {"$sort": {"_id": 1}}
            ]
            
            cursor = self.database.services.aggregate(pipeline)
            tags_docs = await cursor.to_list(length=None)
            
            return [doc["_id"] for doc in tags_docs]
            
        except Exception as e:
            logger.error("Fehler beim Laden der Service Tags", error=str(e))
            return []
    
    # 🆕 NEW: Health Check Support Methods (minimal addition)
    async def update_service_health_status(self, service: Service) -> bool:
        """Update service health status in database (minimal invasive)"""
        try:
            # Only update health-related fields to avoid conflicts
            update_dict = {
                "last_health_check": service.last_health_check,
                "consecutive_health_failures": service.consecutive_health_failures,
                "status": service.status.value,
                "updated_at": service.updated_at,
                # Also update TTL fields if health check was successful
                "expires_at": service.expires_at,
                "last_heartbeat": service.last_heartbeat
            }
            
            update_dict = jsonable_encoder(update_dict)
            
            result = await self.database.services.update_one(
                {"service_id": service.service_id},
                {"$set": update_dict}
            )
            
            # Update cache
            if service.service_id in self._services_cache:
                self._services_cache[service.service_id] = service
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error("Error updating service health status", 
                        service_id=service.service_id, error=str(e))
            return False
    
    async def get_services_needing_health_check(self) -> List[Service]:
        """Get services that need health checks (new method)"""
        try:
            services = await self.get_all_active_services()
            
            needs_check = []
            for service in services:
                if (service.health_check_url and 
                    service.health_check_enabled and 
                    (service.needs_health_check() or service.is_near_expiry())):
                    needs_check.append(service)
            
            return needs_check
            
        except Exception as e:
            logger.error("Error getting services needing health check", error=str(e))
            return []
    
    async def get_services_near_expiry(self) -> List[Service]:
        """Get services approaching TTL expiry that could use health check fallback"""
        try:
            # Get services expiring in the next 5 minutes
            near_expiry_time = datetime.now(timezone.utc) + timedelta(minutes=5)
            
            cursor = self.database.services.find({
                "expires_at": {
                    "$lt": near_expiry_time.isoformat(),
                    "$gt": datetime.now(timezone.utc).isoformat()
                },
                "health_check_url": {"$exists": True, "$ne": None},
                "fallback_to_health_check": {"$ne": False}
            })
            
            services_docs = await cursor.to_list(length=None)
            
            services = []
            for doc in services_docs:
                try:
                    prepared_doc = prepare_service_doc(doc)
                    service = Service(**prepared_doc)
                    if service.can_use_health_check_fallback():
                        services.append(service)
                except Exception as e:
                    logger.error("Error creating service object for near expiry", 
                               doc_id=str(doc.get("_id", "unknown")), error=str(e))
                    continue
            
            return services
            
        except Exception as e:
            logger.error("Error getting services near expiry", error=str(e))
            return []
    
    async def mark_service_unhealthy(self, service_id: str) -> bool:
        """Mark service as unhealthy (minimal helper method)"""
        try:
            result = await self.database.services.update_one(
                {"service_id": service_id},
                {"$set": {
                    "status": ServiceStatus.UNHEALTHY.value,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            
            # Update cache
            if service_id in self._services_cache:
                self._services_cache[service_id].status = ServiceStatus.UNHEALTHY
                self._services_cache[service_id].updated_at = datetime.now(timezone.utc)
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error("Error marking service as unhealthy", service_id=service_id, error=str(e))
            return False
    
    async def expire_service(self, service_id: str) -> bool:
        """Mark service as expired and handle cleanup"""
        try:
            service = await self.get_service_by_id(service_id)
            if not service:
                return False
            
            # Mark as expired
            service.mark_expired()
            
            # Update in database
            await self.update_service_health_status(service)
            
            # Remove from mDNS if available
            if self.mdns_server:
                try:
                    await self.mdns_server.unregister_service(service_id)
                except Exception as mdns_error:
                    logger.warning("mDNS cleanup failed during service expiry", 
                                 service_id=service_id, error=str(mdns_error))
            
            # Remove from database (cleanup)
            await self.deregister_service(service_id)
            
            logger.info("Service expired and cleaned up", service_id=service_id)
            return True
            
        except Exception as e:
            logger.error("Error expiring service", service_id=service_id, error=str(e))
            return False 