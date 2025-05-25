"""
Health Check API Endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

from app.database import database
from app.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health Check Response Schema"""
    status: str
    version: str
    database: str
    message: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Beacon Health Check"""
    try:
        # Prüfe Database Verbindung
        db_healthy = await database.health_check()
        
        if db_healthy:
            return HealthResponse(
                status="healthy",
                version="1.0.0",
                database="connected",
                message="Bitsperity Beacon ist gesund und bereit"
            )
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "version": "1.0.0",
                    "database": "disconnected",
                    "message": "Database Verbindung fehlgeschlagen"
                }
            )
            
    except Exception as e:
        logger.error("Health Check fehlgeschlagen", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "version": "1.0.0",
                "database": "error",
                "message": f"Health Check Fehler: {str(e)}"
            }
        )


@router.get("/ready")
async def readiness_check():
    """Readiness Check für Kubernetes/Docker"""
    try:
        # Prüfe ob alle Services bereit sind
        db_healthy = await database.health_check()
        
        if db_healthy:
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail={"status": "not ready"})
            
    except Exception as e:
        logger.error("Readiness Check fehlgeschlagen", error=str(e))
        raise HTTPException(status_code=503, detail={"status": "not ready"})


@router.get("/live")
async def liveness_check():
    """Liveness Check für Kubernetes/Docker"""
    return {"status": "alive"} 