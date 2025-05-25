"""
Konfiguration für Bitsperity Beacon
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App Konfiguration"""
    
    # Beacon Configuration
    beacon_port: int = Field(default=8000, env="BEACON_PORT")
    beacon_host: str = Field(default="0.0.0.0", env="BEACON_HOST")
    beacon_mongodb_url: str = Field(
        default="mongodb://umbrel:umbrel@bitsperity-mongodb:27017/beacon",
        env="BEACON_MONGODB_URL"
    )
    beacon_log_level: str = Field(default="INFO", env="BEACON_LOG_LEVEL")
    beacon_ttl_cleanup_interval: int = Field(default=30, env="BEACON_TTL_CLEANUP_INTERVAL")
    beacon_default_ttl: int = Field(default=300, env="BEACON_DEFAULT_TTL")
    
    # mDNS Configuration
    mdns_domain: str = Field(default="local", env="MDNS_DOMAIN")
    mdns_interface: Optional[str] = Field(default=None, env="MDNS_INTERFACE")
    
    # Database Configuration
    database_name: str = Field(default="beacon", env="DATABASE_NAME")
    services_collection: str = Field(default="services", env="SERVICES_COLLECTION")
    health_checks_collection: str = Field(default="health_checks", env="HEALTH_CHECKS_COLLECTION")
    
    # API Configuration
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    
    # Logging Configuration
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: str = Field(default="/app/logs/beacon.log", env="LOG_FILE")
    
    # Health Check Configuration
    health_check_timeout: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")
    health_check_interval: int = Field(default=60, env="HEALTH_CHECK_INTERVAL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 