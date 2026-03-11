from typing import Optional
import redis.asyncio as aioredis
from src.config import settings
_redis_client: Optional[aioredis.Redis] = None

async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client

async def cache_link(short_code: str, original_url: str, ttl: int) -> None:
    r = await get_redis()
    await r.setex(f"link:{short_code}", ttl, original_url)

async def get_cached_link(short_code: str) -> Optional[str]:
    r = await get_redis()
    return await r.get(f"link:{short_code}")

async def delete_cached_link(short_code: str) -> None:
    r = await get_redis()
    await r.delete(f"link:{short_code}")
