"""Paper trading simulation routes."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from core.mongodb import get_async_db
from models.user import User
from core.dependencies import get_current_user
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/paper-trading", tags=["paper-trading"])

DEFAULT_CASH = 100_000.0


async def _get_or_create_portfolio(user_id: str) -> dict:
    db = get_async_db()
    port = await db["paper_portfolios"].find_one({"user_id": user_id})
    if not port:
        port = {
            "user_id": user_id,
            "cash": DEFAULT_CASH,
            "holdings": {},
            "created_at": datetime.now(timezone.utc),
        }
        await db["paper_portfolios"].insert_one(port)
        port = await db["paper_portfolios"].find_one({"user_id": user_id})
    return port


@router.get("/portfolio")
async def get_portfolio(current_user: User = Depends(get_current_user)):
    user_id = str(current_user.id)
    port = await _get_or_create_portfolio(user_id)
    port["_id"] = str(port["_id"])

    enriched_holdings = {}
    total_value = port["cash"]
    for symbol, holding in port.get("holdings", {}).items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            current_price = float(hist["Close"].iloc[-1]) if not hist.empty else holding["avg_cost"]
        except Exception:
            current_price = holding["avg_cost"]
        market_value = current_price * holding["shares"]
        pnl = market_value - holding["avg_cost"] * holding["shares"]
        pnl_pct = (pnl / (holding["avg_cost"] * holding["shares"])) * 100 if holding["avg_cost"] > 0 else 0
        enriched_holdings[symbol] = {
            **holding,
            "current_price": round(current_price, 2),
            "market_value": round(market_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
        }
        total_value += market_value

    db = get_async_db()
    trades = []
    async for t in db["paper_trades"].find({"user_id": user_id}).sort("timestamp", -1).limit(50):
        t["_id"] = str(t["_id"])
        trades.append(t)

    holdings_list = [{"symbol": sym, **data} for sym, data in enriched_holdings.items()]

    return {
        "cash": round(port["cash"], 2),
        "holdings": holdings_list,
        "total_value": round(total_value, 2),
        "pnl_total": round(total_value - DEFAULT_CASH, 2),
        "pnl_pct": round((total_value - DEFAULT_CASH) / DEFAULT_CASH * 100, 2),
        "trades": trades,
    }


class TradeRequest(BaseModel):
    symbol: str
    action: str
    shares: float
    note: Optional[str] = None


@router.post("/trade")
async def execute_trade(req: TradeRequest, current_user: User = Depends(get_current_user)):
    user_id = str(current_user.id)
    symbol = req.symbol.upper()
    action = req.action.upper()

    if action not in ("BUY", "SELL"):
        raise HTTPException(400, "action must be BUY or SELL")
    if req.shares <= 0:
        raise HTTPException(400, "shares must be positive")

    try:
        hist = yf.Ticker(symbol).history(period="1d")
        if hist.empty:
            raise HTTPException(404, f"No price data for {symbol}")
        price = float(hist["Close"].iloc[-1])
    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to get stock price", exc_info=True)
        raise HTTPException(500, "Failed to get price")

    db = get_async_db()
    port = await _get_or_create_portfolio(user_id)
    holdings = dict(port.get("holdings", {}))
    cash = float(port["cash"])

    if action == "BUY":
        cost = price * req.shares * 1.001
        if cost > cash:
            raise HTTPException(400, f"Insufficient cash: need ${cost:.2f}, have ${cash:.2f}")
        cash -= cost
        if symbol in holdings:
            h = holdings[symbol]
            total_shares = h["shares"] + req.shares
            avg_cost = (h["avg_cost"] * h["shares"] + price * req.shares) / total_shares
            holdings[symbol] = {"shares": total_shares, "avg_cost": round(avg_cost, 4)}
        else:
            holdings[symbol] = {"shares": req.shares, "avg_cost": round(price, 4)}

    elif action == "SELL":
        if symbol not in holdings:
            raise HTTPException(400, f"No holdings for {symbol}")
        h = holdings[symbol]
        if req.shares > h["shares"]:
            raise HTTPException(400, f"Only {h['shares']} shares held, cannot sell {req.shares}")
        proceeds = price * req.shares * 0.999
        cash += proceeds
        remaining = h["shares"] - req.shares
        if remaining < 0.0001:
            del holdings[symbol]
        else:
            holdings[symbol] = {**h, "shares": round(remaining, 4)}

    await db["paper_portfolios"].update_one(
        {"user_id": user_id},
        {"$set": {"cash": round(cash, 2), "holdings": holdings}}
    )

    trade_record = {
        "user_id": user_id, "symbol": symbol, "action": action,
        "shares": req.shares, "price": round(price, 4),
        "total": round(price * req.shares, 2),
        "timestamp": datetime.now(timezone.utc),
        "note": req.note,
    }
    await db["paper_trades"].insert_one(trade_record)

    return {"status": "ok", "trade": {**trade_record, "_id": None}}


@router.delete("/portfolio/reset")
async def reset_portfolio(current_user: User = Depends(get_current_user)):
    user_id = str(current_user.id)
    db = get_async_db()
    await db["paper_portfolios"].delete_one({"user_id": user_id})
    await db["paper_trades"].delete_many({"user_id": user_id})
    return {"status": "reset"}
