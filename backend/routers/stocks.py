from fastapi import APIRouter, Query, HTTPException
import numpy as np
import re
from services.stock_service import get_stock_data, search_stocks, get_stock_fundamentals, get_stock_peers

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

_SYMBOL_RE = re.compile(r'^[A-Z0-9.\-]{1,10}$')
_VALID_PERIODS   = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"}
_VALID_INTERVALS = {"1d", "1wk", "1mo"}


def _validate_symbol(symbol: str) -> str:
    s = symbol.upper()
    if not _SYMBOL_RE.match(s):
        raise HTTPException(status_code=400, detail="Invalid symbol")
    return s


@router.get("/search/{query}")
def search(query: str):
    return search_stocks(query)


@router.get("/{symbol}")
async def get_stock(
    symbol: str,
    period: str = Query("1y"),
    interval: str = Query("1d"),
):
    if period not in _VALID_PERIODS:
        raise HTTPException(status_code=400, detail="Invalid period")
    if interval not in _VALID_INTERVALS:
        raise HTTPException(status_code=400, detail="Invalid interval")
    return await get_stock_data(_validate_symbol(symbol), period, interval)


@router.get("/{symbol}/metrics")
async def get_metrics(symbol: str):
    data = await get_stock_data(_validate_symbol(symbol), period="1y")
    if "error" in data:
        return data
    prices = [d["close"] for d in data.get("data", [])]
    volumes = [d["volume"] for d in data.get("data", [])]
    if not prices or len(prices) < 2:
        return {"error": "Insufficient price data"}
    prices_arr = np.array(prices, dtype=float)
    prev_prices = prices_arr[:-1]
    prev_prices_safe = np.where(prev_prices == 0, np.nan, prev_prices)
    returns = np.diff(prices_arr) / prev_prices_safe
    returns = returns[~np.isnan(returns)]
    return {
        "symbol": symbol.upper(),
        "current_price": data["current_price"],
        "high_52w": data["high_52w"],
        "low_52w": data["low_52w"],
        "avg_volume": data["avg_volume"],
        "volatility": round(float(np.std(returns) * np.sqrt(252) * 100), 2),
        "price_change_1y": round(((prices[-1] - prices[0]) / prices[0]) * 100, 2) if len(prices) > 1 else 0,
    }


@router.get("/{symbol}/fundamentals")
async def get_fundamentals(symbol: str):
    return await get_stock_fundamentals(_validate_symbol(symbol))


@router.get("/{symbol}/peers")
async def get_peers(symbol: str):
    return get_stock_peers(_validate_symbol(symbol))
