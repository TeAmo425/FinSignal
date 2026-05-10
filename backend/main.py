from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import os

load_dotenv()

from sqlalchemy import text
from database import engine, Base
import models.user
import models.dataset
import models.stock

Base.metadata.create_all(bind=engine)

# Auto-migrate: add new columns to existing tables if they don't exist
with engine.connect() as _conn:
    for _stmt in [
        "ALTER TABLE users ADD COLUMN api_keys TEXT",
    ]:
        try:
            _conn.execute(text(_stmt))
            _conn.commit()
        except Exception:
            pass  # column already exists

from routers import auth, datasets, stocks, forecast, anomalies, chat, reports, trading_agents
from routers.paper_trading import router as paper_router
from routers.screener import router as screener_router
from routers.ashare import router as ashare_router

from core.mongodb import init_mongodb, close_mongodb
from core.redis_client import init_redis, close_redis

limiter = Limiter(key_func=get_remote_address)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_mongodb()
    await init_redis()
    yield
    await close_mongodb()
    await close_redis()


app = FastAPI(
    title="FinAgent API",
    description="AI-powered financial analysis platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if ENVIRONMENT == "production" else "/docs",
    openapi_url=None if ENVIRONMENT == "production" else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(stocks.router)
app.include_router(forecast.router)
app.include_router(anomalies.router)
app.include_router(chat.router)
app.include_router(reports.router)
app.include_router(trading_agents.router)
app.include_router(paper_router)
app.include_router(screener_router)
app.include_router(ashare_router)

@app.get("/")
def root():
    return {"message": "FinAgent API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
