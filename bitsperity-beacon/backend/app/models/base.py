"""
Base Model für gemeinsame Felder
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel as PydanticBaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId für Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        field_schema.update(type="string")
        return field_schema
    
    def __str__(self) -> str:
        """String representation für JSON Serialisierung"""
        return str(super().__str__())
    
    def __repr__(self) -> str:
        """Representation für Debugging"""
        return f"PyObjectId('{str(super().__str__())}')"


class BaseModel(PydanticBaseModel):
    """Base Model mit gemeinsamen Feldern"""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: lambda v: str(v),
            PyObjectId: lambda v: str(v),
            datetime: lambda v: v.isoformat() if v else None
        },
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439011"
            }
        }
    }
        
    def dict(self, **kwargs):
        """Override dict method to handle ObjectId"""
        d = super().model_dump(**kwargs)
        if "_id" in d and d["_id"] is not None:
            d["_id"] = str(d["_id"])
        if "id" in d and d["id"] is not None:
            d["id"] = str(d["id"])
        return d
    
    def model_dump(self, **kwargs):
        """Override model_dump for Pydantic v2"""
        d = super().model_dump(**kwargs)
        if "_id" in d and d["_id"] is not None:
            d["_id"] = str(d["_id"])
        if "id" in d and d["id"] is not None:
            d["id"] = str(d["id"])
        return d 