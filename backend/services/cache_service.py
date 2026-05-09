"""Cache service: wraps stock/forecast data with Redis + MongoDB fallback."""
import logging
from datetime import datetime, timezone
from typing import Optional, Any
from core.redis_client import cache_set, cache_get, TTL_STOCK_PRICE, TTL_FUNDAMENTALS, TTL_FORECAST
from core.mongodb import get_async_db

logger = logging.getLogger(__name__)


async def get_stock_cache(symbol: str, market: str = "US") -> Optional[dict]:
    """Try Redis first, then MongoDB."""
    key = f"stock:{market}:{symbol}:price"
    cached = await cache_get(key)
    if cached:
        return cached
    # MongoDB fallback
    try:
        db = get_async_db()
        doc = await db["stock_cache"].find_one({"symbol": symbol, "market": market})
        if doc:
            doc.pop("_id", None)
            await cache_set(key, doc, TTL_STOCK_PRICE)
            return doc
    except Exception as e:
        logger.warning(f"MongoDB stock cache lookup failed: {e}")
    return None


async def set_stock_cache(symbol: str, data: dict, market: str = "US"):
    """Write to Redis and MongoDB."""
    key = f"stock:{market}:{symbol}:price"
    await cache_set(key, data, TTL_STOCK_PRICE)
    try:
        db = get_async_db()
        await db["stock_cache"].update_one(
            {"symbol": symbol, "market": market},
            {"$set": {**data, "symbol": symbol, "market": market, "cached_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
    except Exception as e:
        logger.warning(f"MongoDB stock cache write failed: {e}")


async def get_fundamentals_cache(symbol: str) -> Optional[dict]:
    key = f"fundamentals:US:{symbol}"
    return await cache_get(key)


async def set_fundamentals_cache(symbol: str, data: dict):
    key = f"fundamentals:US:{symbol}"
    await cache_set(key, data, TTL_FUNDAMENTALS)


async def save_analysis_result(symbol: str, trade_date: str, provider: str,
                               analysts: list, results: list, final_decision: str,
                               user_id: str = "anonymous"):
    """Persist analysis result to MongoDB."""
    try:
        db = get_async_db()
        await db["analysis_results"].insert_one({
            "symbol": symbol.upper(),
            "trade_date": trade_date,
            "provider": provider,
            "analysts": analysts,
            "results": results,
            "final_decision": final_decision,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.warning(f"Failed to save analysis result: {e}")


async def get_recent_analyses(symbol: str = None, limit: int = 20) -> list:
    """Get recent analysis results from MongoDB."""
    try:
        db = get_async_db()
        query = {"symbol": symbol.upper()} if symbol else {}
        cursor = db["analysis_results"].find(query).sort("created_at", -1).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except Exception as e:
        logger.warning(f"Failed to get analyses: {e}")
        return []
