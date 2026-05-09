"""Stock screener routes for US + A-share markets."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import yfinance as yf
from core.redis_client import cache_get, cache_set, TTL_SCREENER
import hashlib

router = APIRouter(prefix="/api/screener", tags=["screener"])

# Common US stocks pool for screening
US_SCREEN_POOL = [
    "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","BRK-B","JPM","V",
    "UNH","XOM","LLY","AVGO","JNJ","MA","PG","HD","MRK","COST",
    "ABBV","CVX","ADBE","CRM","PEP","KO","TMO","ACN","MCD","CSCO",
    "ABT","WMT","BAC","LIN","TXN","DHR","NEE","CMCSA","NKE","ORCL",
    "PM","RTX","QCOM","AMD","AMGN","T","INTU","LOW","SPGI","GS",
]


class ScreenRequest(BaseModel):
    market: str = "US"          # US | CN
    min_pe: Optional[float] = None
    max_pe: Optional[float] = None
    min_market_cap: Optional[float] = None   # in billions
    max_market_cap: Optional[float] = None
    min_beta: Optional[float] = None
    max_beta: Optional[float] = None
    sector: Optional[str] = None
    min_ytd_return: Optional[float] = None
    max_ytd_return: Optional[float] = None
    limit: int = 30


@router.post("/screen")
async def screen_stocks(req: ScreenRequest):
    if req.market == "CN":
        from services.ashare_service import screen_ashare
        return await screen_ashare(req.min_pe, req.max_pe, req.sector, req.limit)

    # Cache key based on request
    cache_key = f"screener:US:{hashlib.md5(req.model_dump_json().encode()).hexdigest()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    results = []
    for sym in US_SCREEN_POOL:
        try:
            info = yf.Ticker(sym).info
            if not info:
                continue

            pe       = info.get("trailingPE")
            market_cap_b = (info.get("marketCap") or 0) / 1e9
            beta     = info.get("beta")
            sector   = info.get("sector", "")

            # Apply filters
            if req.min_pe is not None and (pe is None or pe < req.min_pe): continue
            if req.max_pe is not None and (pe is None or pe > req.max_pe): continue
            if req.min_market_cap is not None and market_cap_b < req.min_market_cap: continue
            if req.max_market_cap is not None and market_cap_b > req.max_market_cap: continue
            if req.min_beta is not None and (beta is None or beta < req.min_beta): continue
            if req.max_beta is not None and (beta is None or beta > req.max_beta): continue
            if req.sector and sector.lower() != req.sector.lower(): continue

            ytd_return = round((info.get("52WeekChange") or 0) * 100, 2)
            if req.min_ytd_return is not None and ytd_return < req.min_ytd_return: continue
            if req.max_ytd_return is not None and ytd_return > req.max_ytd_return: continue

            results.append({
                "symbol":     sym,
                "name":       info.get("shortName", sym),
                "sector":     sector,
                "price":      round(info.get("currentPrice") or info.get("regularMarketPrice") or 0, 2),
                "pe_ratio":   round(pe, 2) if pe else None,
                "market_cap_b": round(market_cap_b, 2),
                "beta":       round(beta, 2) if beta else None,
                "ytd_return": ytd_return,
                "forward_pe": round(info.get("forwardPE") or 0, 2),
            })
            if len(results) >= req.limit:
                break
        except Exception:
            continue

    await cache_set(cache_key, results, TTL_SCREENER)
    return results


@router.get("/sectors")
async def get_sectors():
    return {
        "US": ["Technology","Healthcare","Financials","Consumer Discretionary",
                "Communication Services","Industrials","Consumer Staples",
                "Energy","Materials","Real Estate","Utilities"],
        "CN": ["银行","非银金融","医药生物","计算机","电子","食品饮料",
                "汽车","房地产","机械设备","化工","传媒","军工"],
    }
