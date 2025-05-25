"""
Base Model für gemeinsame Felder
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel as PydanticBaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId für Pydantic"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class BaseModel(PydanticBaseModel):
    """Base Model mit gemeinsamen Feldern"""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        
    def dict(self, **kwargs):
        """Override dict method to handle ObjectId"""
        d = super().dict(**kwargs)
        if "_id" in d:
            d["_id"] = str(d["_id"])
        return d 