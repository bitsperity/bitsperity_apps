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


def jsonable_encoder(obj: Any, by_alias: bool = True, **kwargs) -> Any:
    """
    Konvertiere ein Objekt in ein JSON-serialisierbares Format
    Kompatibel mit FastAPI's jsonable_encoder Signatur
    """
    # Handle PyObjectId specifically
    if hasattr(obj, '__class__') and obj.__class__.__name__ == 'PyObjectId':
        return str(obj)
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, BaseModel):
        # Use model_dump with mode='json' to ensure proper serialization
        return obj.model_dump(mode='json', by_alias=by_alias)
    if isinstance(obj, dict):
        return {k: jsonable_encoder(v, by_alias=by_alias) for k, v in obj.items()}
    if isinstance(obj, list):
        return [jsonable_encoder(item, by_alias=by_alias) for item in obj]
    if hasattr(obj, '__dict__'):
        return jsonable_encoder(obj.__dict__, by_alias=by_alias)
    return obj 