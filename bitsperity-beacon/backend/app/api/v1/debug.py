"""
Debug API Endpoints für Bitsperity Beacon
"""
from fastapi import APIRouter, Depends
from typing import Any, Dict
import structlog
from bson import ObjectId
from datetime import datetime

from app.core.json_encoder import jsonable_encoder
from app.models.base import PyObjectId
from app.database import get_database, Database

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/test-time")
async def test_time():
    """Test Server Time and Timezone"""
    try:
        now_utc = datetime.utcnow()
        now_local = datetime.now()
        
        # Test Service Query Time
        from app.database import get_database
        db = await get_database().__anext__()
        
        # Test MongoDB query with current time
        test_query = {"expires_at": {"$gt": now_utc}}
        services_count = await db.services.count_documents(test_query)
        
        return {
            "server_time_utc": now_utc.isoformat(),
            "server_time_local": now_local.isoformat(),
            "timezone_offset_hours": (now_local - now_utc).total_seconds() / 3600,
            "mongodb_query_time": now_utc.isoformat(),
            "services_found_with_current_time": services_count,
            "test_successful": True
        }
    except Exception as e:
        logger.error("Time test failed", error=str(e), exc_info=True)
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "test_successful": False
        }


@router.get("/test-objectid")
async def test_objectid():
    """Test PyObjectId Serialization"""
    try:
        # Test verschiedene ObjectId Szenarien
        obj1 = PyObjectId()
        obj2 = ObjectId()
        
        test_data = {
            "pyobjectid_instance": obj1,
            "pyobjectid_str": str(obj1),
            "pyobjectid_repr": repr(obj1),
            "objectid_instance": obj2,
            "objectid_str": str(obj2),
            "test_dict": {
                "_id": obj1,
                "other_id": obj2
            }
        }
        
        # Test jsonable_encoder
        encoded = jsonable_encoder(test_data)
        
        return {
            "raw_types": {
                "pyobjectid_type": str(type(obj1)),
                "objectid_type": str(type(obj2)),
                "pyobjectid_class": obj1.__class__.__name__,
                "objectid_class": obj2.__class__.__name__
            },
            "encoded_result": encoded,
            "test_successful": True
        }
    except Exception as e:
        logger.error("ObjectId test failed", error=str(e), exc_info=True)
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "test_successful": False
        }


@router.get("/test-service-creation")
async def test_service_creation():
    """Test Service Model Creation"""
    try:
        from app.models.service import Service
        from app.schemas.service import ServiceCreate
        
        # Test Service Creation
        service_data = ServiceCreate(
            name="debug-test-service",
            type="http",
            host="192.168.1.100",
            port=8080,
            protocol="tcp",
            ttl=300
        )
        
        # Create Service Model
        service = Service(**service_data.model_dump())
        
        # Test verschiedene Serialization Methoden
        results = {
            "service_id": service.service_id,
            "model_dump": service.model_dump(),
            "model_dump_by_alias": service.model_dump(by_alias=True),
            "jsonable_encoder": jsonable_encoder(service),
            "jsonable_encoder_model_dump": jsonable_encoder(service.model_dump()),
            "id_field_type": str(type(service.id)),
            "id_field_value": str(service.id) if service.id else None
        }
        
        return {
            "test_successful": True,
            "results": results
        }
    except Exception as e:
        logger.error("Service creation test failed", error=str(e), exc_info=True)
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "test_successful": False
        }


@router.get("/test-database-insert")
async def test_database_insert(db: Database = Depends(get_database)):
    """Test Database Insert with Service"""
    try:
        from app.models.service import Service
        
        # Create test service
        service = Service(
            name="debug-db-test",
            type="test",
            host="127.0.0.1",
            port=9999
        )
        
        # Prepare for database
        service_dict = jsonable_encoder(service.model_dump(by_alias=True))
        
        # Insert into database
        result = await db.services.insert_one(service_dict)
        
        # Read back from database
        saved_doc = await db.services.find_one({"_id": result.inserted_id})
        
        # Clean up
        await db.services.delete_one({"_id": result.inserted_id})
        
        return {
            "test_successful": True,
            "inserted_id": str(result.inserted_id),
            "service_dict_keys": list(service_dict.keys()),
            "saved_doc_keys": list(saved_doc.keys()) if saved_doc else None,
            "saved_doc_id_type": str(type(saved_doc.get("_id"))) if saved_doc else None
        }
    except Exception as e:
        logger.error("Database insert test failed", error=str(e), exc_info=True)
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "test_successful": False
        }


@router.get("/system-info")
async def get_system_info():
    """Get System Information"""
    import sys
    import pydantic
    import pymongo
    
    return {
        "python_version": sys.version,
        "pydantic_version": pydantic.__version__,
        "pymongo_version": pymongo.__version__,
        "encoding": sys.getdefaultencoding()
    } 