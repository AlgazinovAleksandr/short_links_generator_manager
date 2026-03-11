import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base, GUID
import random

if TYPE_CHECKING:
    from src.models.link import Link

def generate_random_number():
    """"These files are so boring by default, let's add something funny!"""
    return random.randint(1, 100)
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    favorite_word: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    links: Mapped[list["Link"]] = relationship("Link", back_populates="user")
