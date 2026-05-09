import asyncio
import yfinance as yf
import pandas as pd
from core.redis_client import cache_get, cache_set, TTL_STOCK_PRICE, TTL_FUNDAMENTALS

# ─── Sync yfinance helpers (run in thread pool) ──────────────────────────────

def _fetch_stock_sync(symbol: str, period: str, interval: str) -> dict:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            return {"error": f"No data found for symbol {symbol}"}

        hist = hist.reset_index()
        hist["Date"] = hist["Date"].astype(str)

        data = []
        for _, row in hist.iterrows():
            data.append({
                "date": str(row["Date"])[:10],
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        current_price = data[-1]["close"] if data else 0
        highs = [d["high"] for d in data]
        lows = [d["low"] for d in data]
        volumes = [d["volume"] for d in data]

        info = {}
        try:
            info = ticker.info or {}
        except Exception:
            pass

        return {
            "symbol": symbol.upper(),
            "name": info.get("longName", symbol),
            "current_price": current_price,
            "high_52w": round(max(highs), 2) if highs else 0,
            "low_52w": round(min(lows), 2) if lows else 0,
            "avg_volume": int(sum(volumes) / len(volumes)) if volumes else 0,
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "data": data,
        }
    except Exception as e:
        return {"error": str(e)}


def _fetch_fundamentals_sync(symbol: str) -> dict:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        return {
            "symbol": symbol.upper(),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "price_to_book": info.get("priceToBook"),
            "market_cap": info.get("marketCap"),
            "revenue": info.get("totalRevenue"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "gross_margin": info.get("grossMargins"),
            "operating_margin": info.get("operatingMargins"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "eps": info.get("trailingEps"),
            "analyst_target": info.get("targetMeanPrice"),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
            "net_income": info.get("netIncomeToCommon"),
            "pb_ratio": info.get("priceToBook"),
            "dividend_yield": info.get("dividendYield"),
        }
    except Exception as e:
        return {"error": str(e)}


# ─── Async public API (with Redis cache) ─────────────────────────────────────

async def get_stock_data(symbol: str, period: str = "1y", interval: str = "1d") -> dict:
    cache_key = f"stock:price:{symbol}:{period}:{interval}"
    cached = await cache_get(cache_key)
    if cached:
        return cached
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _fetch_stock_sync, symbol, period, interval)
    if "error" not in result:
        await cache_set(cache_key, result, TTL_STOCK_PRICE)
    return result


async def get_stock_fundamentals(symbol: str) -> dict:
    cache_key = f"stock:fundamentals:{symbol}"
    cached = await cache_get(cache_key)
    if cached:
        return cached
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _fetch_fundamentals_sync, symbol)
    if "error" not in result:
        await cache_set(cache_key, result, TTL_FUNDAMENTALS)
    return result


def get_stock_peers(symbol: str) -> list:
    PEER_GROUPS = {
        "AAPL": ["MSFT", "GOOGL", "META"],
        "MSFT": ["AAPL", "GOOGL", "AMZN"],
        "GOOGL": ["MSFT", "META", "AMZN"],
        "TSLA": ["F", "GM", "RIVN"],
        "NVDA": ["AMD", "INTC", "AVGO"],
        "AMZN": ["MSFT", "GOOGL", "WMT"],
        "META": ["GOOGL", "SNAP", "PINS"],
    }
    peers = PEER_GROUPS.get(symbol.upper(), [])
    result = []
    for peer in peers:
        try:
            t = yf.Ticker(peer)
            info = t.info or {}
            hist = t.history(period="5d")
            current_price = None
            change_pct = None
            ytd_return = None
            if not hist.empty:
                current_price = round(float(hist["Close"].iloc[-1]), 2)
                if len(hist) > 1:
                    prev = float(hist["Close"].iloc[-2])
                    if prev > 0:
                        change_pct = round((current_price - prev) / prev * 100, 2)
                start_p = float(hist["Close"].iloc[0])
                if start_p > 0:
                    ytd_return = round((current_price - start_p) / start_p * 100, 2)
            result.append({
                "symbol": peer,
                "name": info.get("longName", peer),
                "current_price": current_price,
                "change_pct": change_pct,
                "pe_ratio": info.get("trailingPE"),
                "market_cap": info.get("marketCap", 0),
                "ytd_return": ytd_return,
                "sector": info.get("sector", ""),
            })
        except Exception:
            pass
    return result


def search_stocks(query: str) -> list:
    common_stocks = [
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "GOOGL", "name": "Alphabet Inc."},
        {"symbol": "MSFT", "name": "Microsoft Corporation"},
        {"symbol": "TSLA", "name": "Tesla Inc."},
        {"symbol": "NVDA", "name": "NVIDIA Corporation"},
        {"symbol": "AMZN", "name": "Amazon.com Inc."},
        {"symbol": "META", "name": "Meta Platforms Inc."},
        {"symbol": "NFLX", "name": "Netflix Inc."},
    ]
    q = query.upper()
    return [s for s in common_stocks if q in s["symbol"] or q.lower() in s["name"].lower()]
