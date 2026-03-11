import random
import string
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse, urlunparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.link import Link

SHORT_CODE_LENGTH = 8
ALPHABET = string.ascii_letters + string.digits


def generate_short_code() -> str:
    return "".join(random.choices(ALPHABET, k=SHORT_CODE_LENGTH))

# Ох уж эта асинхронщина я же так бэкендером стану
async def create_unique_short_code(db: AsyncSession) -> str:
    for _ in range(10):
        code = generate_short_code()
        result = await db.execute(select(Link).where(Link.short_code == code))
        if result.scalar_one_or_none() is None:
            return code
    raise RuntimeError("Что-то у нас даже за 10 попыток ничего не получилось сгенерировать(")

async def get_link_by_short_code(db: AsyncSession, short_code: str) -> Optional[Link]:
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    return result.scalar_one_or_none()

async def get_link_by_original_url(db: AsyncSession, original_url: str) -> Optional[Link]:
    result = await db.execute(select(Link).where(Link.original_url == original_url))
    return result.scalar_one_or_none()

def is_link_expired(link: Link) -> bool:
    if link.expires_at is None:
        return False
    now = datetime.now(timezone.utc)
    expires = link.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return now > expires

def apply_favorite_word(url: str, word: str) -> str:
    parsed = urlparse(url)
    new_netloc = word + parsed.netloc
    return urlunparse(parsed._replace(netloc=new_netloc))

def compute_cache_ttl(link: Link, default_ttl: int) -> int:
    if link.expires_at is None:
        return default_ttl
    now = datetime.now(timezone.utc)
    expires = link.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    remaining = int((expires - now).total_seconds())
    return max(1, min(default_ttl, remaining))
