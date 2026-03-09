from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LinkCreate(BaseModel):
    original_url: str
    custom_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    project: Optional[str] = None

class LinkUpdate(BaseModel):
    original_url: str