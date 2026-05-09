from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from services.ai_service import generate_insight
from models.user import User
from core.dependencies import get_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    symbol: Optional[str] = None
    context: Optional[dict] = None

@router.post("/message")
def chat(req: ChatRequest, current_user: User = Depends(get_current_user)):
    # Build context string — accept symbol as direct field or inside context dict
    symbol = req.symbol
    if not symbol and req.context:
        symbol = req.context.get("symbol")

    if symbol:
        context_str = f"User is analyzing stock: {symbol.upper()}"
    elif req.context and req.context.get("dataset_id"):
        context_str = f"User is analyzing dataset ID: {req.context['dataset_id']}"
    else:
        context_str = ""

    response = generate_insight(context_str, req.message)
    return {"response": response, "symbol": symbol}
