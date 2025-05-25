"""
MongoDB Datenbankverbindung für Bitsperity Beacon
"""
import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ServerSelectionTimeoutError
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class Database:
    """MongoDB Database Manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.services: Optional[AsyncIOMotorCollection] = None
        self.health_checks: Optional[AsyncIOMotorCollection] = None
        
    async def connect(self) -> None:
        """Verbindung zur MongoDB herstellen"""
        try:
            logger.info("Verbinde mit MongoDB", url=settings.beacon_mongodb_url)
            
            self.client = AsyncIOMotorClient(
                settings.beacon_mongodb_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.db = self.client[settings.database_name]
            self.services = self.db[settings.services_collection]
            self.health_checks = self.db[settings.health_checks_collection]
            
            # Create indexes
            await self._create_indexes()
            
            logger.info("MongoDB Verbindung erfolgreich")
            
        except ServerSelectionTimeoutError as e:
            logger.error("MongoDB Verbindung fehlgeschlagen", error=str(e))
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler bei MongoDB Verbindung", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Verbindung zur MongoDB schließen"""
        if self.client:
            logger.info("Schließe MongoDB Verbindung")
            self.client.close()
            self.client = None
            self.db = None
            self.services = None
            self.health_checks = None
    
    async def _create_indexes(self) -> None:
        """Erstelle notwendige Indexes"""
        try:
            # Services Collection Indexes
            await self.services.create_index("service_id", unique=True)
            await self.services.create_index("expires_at")
            await self.services.create_index("type")
            await self.services.create_index("host")
            await self.services.create_index([("type", 1), ("expires_at", 1)])
            
            # Health Checks Collection Indexes
            await self.health_checks.create_index("service_id")
            await self.health_checks.create_index("checked_at")
            await self.health_checks.create_index([("service_id", 1), ("checked_at", -1)])
            
            logger.info("MongoDB Indexes erstellt")
            
        except Exception as e:
            logger.error("Fehler beim Erstellen der Indexes", error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Prüfe Datenbankverbindung"""
        try:
            if not self.client:
                return False
            
            await self.client.admin.command('ping')
            return True
            
        except Exception as e:
            logger.error("Database Health Check fehlgeschlagen", error=str(e))
            return False


# Global database instance
database = Database()


async def get_database() -> Database:
    """Dependency für FastAPI"""
    return database 