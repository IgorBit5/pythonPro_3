from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class LinkCreate(BaseModel):
    original_url: str
    custom_url: Optional[str] = None
    expires_at: Optional[str] = Field(None, description="Дата в формате YYYY-MM-DD или YYYY-MM-DD HH:MM:SS")
    project: Optional[str] = None
    
    @validator('expires_at', pre=True, always=True)
    def validate_expires_at(cls, v):
        if v is None or v == "":
            return None
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except (ValueError, TypeError):
            raise ValueError('expires_at должен быть валидной датой в формате ISO (например, 2024-12-31T23:59:59)')

class LinkUpdate(BaseModel):
    original_url: str