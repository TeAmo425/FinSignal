"""MongoDB connection manager using Motor (async)."""
import logging
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = "finagent"

# Async clients (for FastAPI routes)
_async_client: Optional[AsyncIOMotorClient] = None
_async_db: Optional[AsyncIOMotorDatabase] = None

# Sync client (for startup tasks)
_sync_client: Optional[MongoClient] = None
_sync_db: Optional[Database] = None


async def init_mongodb():
    global _async_client, _async_db, _sync_client, _sync_db
    try:
        _async_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _async_db = _async_client[MONGO_DB_NAME]
        await _async_client.admin.command("ping")
        logger.info("✅ MongoDB connected (async)")

        _sync_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _sync_db = _sync_client[MONGO_DB_NAME]

        await _ensure_indexes()
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


async def _ensure_indexes():
    """Create indexes for performance."""
    db = get_async_db()
    await db["stock_cache"].create_index([("symbol", ASCENDING), ("market", ASCENDING)], unique=True)
    await db["stock_cache"].create_index([("cached_at", DESCENDING)])
    await db["analysis_results"].create_index([("symbol", ASCENDING), ("created_at", DESCENDING)])
    await db["analysis_results"].create_index([("user_id", ASCENDING)])
    await db["paper_trades"].create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
    await db["forecast_cache"].create_index([("symbol", ASCENDING), ("horizon", ASCENDING)], unique=True)
    await db["ashare_stocks"].create_index([("symbol", ASCENDING)], unique=True)
    await db["ashare_stocks"].create_index([("sector", ASCENDING)])
    logger.info("✅ MongoDB indexes created")


async def close_mongodb():
    global _async_client, _sync_client
    if _async_client:
        _async_client.close()
    if _sync_client:
        _sync_client.close()
    logger.info("MongoDB connections closed")


def get_async_db() -> AsyncIOMotorDatabase:
    if _async_db is None:
        raise RuntimeError("MongoDB not initialized. Call init_mongodb() first.")
    return _async_db


def get_sync_db() -> Database:
    if _sync_db is None:
        raise RuntimeError("MongoDB sync client not initialized.")
    return _sync_db
