"""
Custom JSON Encoder für Bitsperity Beacon
"""
import json
from datetime import datetime, date
from typing import Any
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel


class BeaconJSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder für MongoDB ObjectId und datetime"""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


def jsonable_encoder(obj: Any) -> Any:
    """
    Konvertiere ein Objekt in ein JSON-serialisierbares Format
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, dict):
        return {k: jsonable_encoder(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [jsonable_encoder(item) for item in obj]
    if hasattr(obj, '__dict__'):
        return jsonable_encoder(obj.__dict__)
    return obj 