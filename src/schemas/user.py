import uuid
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    created_at: datetime
    favorite_word: Optional[str]
    model_config = {"from_attributes": True}
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
class LoginRequest(BaseModel):
    username: str
    password: str
class FavoriteWordRequest(BaseModel):
    word: str
