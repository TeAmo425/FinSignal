"""Redis connection manager."""
import logging
import json
import os
from typing import Optional, Any
import redis.asyncio as redis_async

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_client: Optional[redis_async.Redis] = None


async def init_redis():
    global _client
    try:
        pool = redis_async.ConnectionPool.from_url(
            REDIS_URL, max_connections=20, decode_responses=True
        )
        _client = redis_async.Redis(connection_pool=pool)
        await _client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}. Caching disabled.")
        _client = None


async def close_redis():
    global _client
    if _client:
        await _client.aclose()
        _client = None


def get_redis() -> Optional[redis_async.Redis]:
    return _client


async def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set a JSON-serializable value in Redis with TTL."""
    if _client is None:
        return False
    try:
        await _client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.warning(f"Redis set failed for {key}: {e}")
        return False


async def cache_get(key: str) -> Optional[Any]:
    """Get and JSON-deserialize a value from Redis."""
    if _client is None:
        return None
    try:
        raw = await _client.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning(f"Redis get failed for {key}: {e}")
        return None


async def cache_delete(key: str) -> bool:
    if _client is None:
        return False
    try:
        await _client.delete(key)
        return True
    except Exception:
        return False


# TTL constants (seconds)
TTL_STOCK_PRICE      = 7_200    # 2 hours
TTL_FUNDAMENTALS     = 86_400   # 24 hours
TTL_FORECAST         = 43_200   # 12 hours
TTL_SCREENER         = 1_800    # 30 minutes
TTL_ASHARE_PRICE     = 7_200    # 2 hours
