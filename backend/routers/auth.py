from fastapi import APIRouter, HTTPException, Depends, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from jose import jwt, JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timedelta
import bcrypt
import os
import json
import logging
from typing import Optional, Dict, Any, List
from database import get_db
from models.user import User
from core.dependencies import get_current_user
from core.mongodb import get_async_db

limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class LoginRequest(BaseModel):
    email: str
    password: str

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register")
@limiter.limit("5/minute")
def register(request: Request, req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=req.email, name=req.name, hashed_password=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.email), "user": {"id": user.id, "email": user.email, "name": user.name}}

@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": create_token(user.email), "user": {"id": user.id, "email": user.email, "name": user.name}}

@router.get("/me")
def get_me(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "name": user.name}


# ── API Keys (stored per user in SQLite) ─────────────────────────────────────

_KEY_FIELDS = {"openai_api_key", "anthropic_api_key", "google_api_key", "deepseek_api_key"}

class ApiKeysRequest(BaseModel):
    keys: Dict[str, str]

@router.get("/settings/keys")
def get_api_keys(current_user: User = Depends(get_current_user)):
    saved = {}
    if current_user.api_keys:
        try:
            saved = json.loads(current_user.api_keys)
        except Exception:
            pass
    # Only return allowed fields; mask values to show configured state
    return {k: ("***" if v else "") for k, v in saved.items() if k in _KEY_FIELDS}


@router.put("/settings/keys")
def save_api_keys(req: ApiKeysRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = {}
    if current_user.api_keys:
        try:
            existing = json.loads(current_user.api_keys)
        except Exception:
            pass
    for k, v in req.keys.items():
        if k in _KEY_FIELDS:
            if v:
                existing[k] = v
            else:
                existing.pop(k, None)
    current_user.api_keys = json.dumps(existing)
    db.commit()
    return {"ok": True}


@router.get("/settings/keys/values")
def get_api_key_values(current_user: User = Depends(get_current_user)):
    """Return actual key values (not masked) — used on login to populate sessionStorage."""
    saved = {}
    if current_user.api_keys:
        try:
            saved = json.loads(current_user.api_keys)
        except Exception:
            pass
    return {k: v for k, v in saved.items() if k in _KEY_FIELDS}


# ── Analysis History (stored in MongoDB) ─────────────────────────────────────

class HistoryEntry(BaseModel):
    ticker: str
    trade_date: str
    provider: str
    results: List[Dict[str, Any]]

@router.post("/history")
async def save_history(entry: HistoryEntry, current_user: User = Depends(get_current_user)):
    db = get_async_db()
    doc = {
        "user_id": current_user.id,
        "ticker": entry.ticker.upper(),
        "trade_date": entry.trade_date,
        "provider": entry.provider,
        "results": entry.results,
        "created_at": datetime.utcnow(),
    }
    await db["analysis_history"].insert_one(doc)
    return {"ok": True}


@router.get("/history")
async def get_history(current_user: User = Depends(get_current_user)):
    db = get_async_db()
    cursor = db["analysis_history"].find(
        {"user_id": current_user.id},
        {"_id": 0, "user_id": 0},
        sort=[("created_at", -1)],
        limit=50,
    )
    items = []
    async for doc in cursor:
        doc["created_at"] = doc["created_at"].isoformat()
        items.append(doc)
    return items
