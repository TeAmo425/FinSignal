"""A-share (Chinese stock) API routes."""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional
from services.ashare_service import get_ashare_stock, search_ashare, screen_ashare
from models.user import User
from core.dependencies import get_current_user

router = APIRouter(prefix="/api/ashare", tags=["ashare"])


@router.get("/search")
async def search(q: str = Query(..., min_length=1), current_user: User = Depends(get_current_user)):
    return await search_ashare(q)


@router.get("/{symbol}")
async def get_stock(symbol: str, period: str = Query("1y", regex="^(1mo|3mo|6mo|1y|2y)$"),
                    current_user: User = Depends(get_current_user)):
    result = await get_ashare_stock(symbol, period=period)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


class ScreenRequest(BaseModel):
    min_pe: Optional[float] = None
    max_pe: Optional[float] = None
    sector: Optional[str] = None
    limit: int = 50


@router.post("/screen")
async def screen(req: ScreenRequest, current_user: User = Depends(get_current_user)):
    return await screen_ashare(req.min_pe, req.max_pe, req.sector, req.limit)
