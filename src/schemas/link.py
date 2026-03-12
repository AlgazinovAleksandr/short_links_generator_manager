import uuid
from pydantic import BaseModel, Field # We love pydantic, I am building my AI agents with pydantic it helps me define the structured output!
from datetime import datetime, timezone
from typing import Optional

class LinkCreate(BaseModel):
    original_url: str
    custom_alias: Optional[str] = None
    expires_at: datetime = Field(default=datetime(2555, 7, 15, tzinfo=timezone.utc))
class LinkUpdate(BaseModel):
    original_url: Optional[str] = None
    new_short_code: Optional[str] = None
class LinkResponse(BaseModel):
    id: uuid.UUID
    original_url: str
    short_code: str
    short_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime]
    click_count: int
    model_config = {"from_attributes": True}
class LinkStats(BaseModel):
    original_url: str
    short_code: str
    created_at: datetime
    click_count: int
    last_accessed_at: Optional[datetime]
    expires_at: Optional[datetime]
    model_config = {"from_attributes": True}
