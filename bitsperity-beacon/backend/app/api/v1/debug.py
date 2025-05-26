"""
Debug API Endpoints für Troubleshooting
"""
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import structlog

from app.core.json_encoder import jsonable_encoder
from app.models.service import Service, ServiceStatus
from app.schemas.service import ServiceCreate

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/test-serialization")
async def test_serialization():
    """Teste JSON Serialisierung"""
    try:
        # Erstelle Test Service
        service_data = ServiceCreate(
            name="Test Service",
            type="api",
            host="192.168.1.100",
            port=8080,
            protocol="http",
            description="Test Service für Serialisierung",
            tags=["test"],
            metadata={"version": "1.0.0"}
        )
        
        # Erstelle Service Model
        service = Service(**service_data.model_dump())
        
        # Teste verschiedene Serialisierungsmethoden
        result = {
            "service_data_dump": service_data.model_dump(),
            "service_model_dump": service.model_dump(),
            "jsonable_encoder_result": jsonable_encoder(service),
            "current_time": datetime.utcnow(),
            "service_status": service.status,
            "service_status_value": service.status.value
        }
        
        return JSONResponse(content=jsonable_encoder(result))
        
    except Exception as e:
        logger.error("Serialization test failed", error=str(e))
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": str(type(e))}
        )


@router.get("/test-simple")
async def test_simple():
    """Einfacher Test ohne komplexe Objekte"""
    return {"message": "Debug endpoint works", "status": "ok"}


@router.get("/test-datetime")
async def test_datetime():
    """Teste datetime Serialisierung"""
    try:
        result = {
            "message": "Testing datetime",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ok"
        }
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": str(type(e))}
        ) 