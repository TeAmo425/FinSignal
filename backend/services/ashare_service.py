"""A-share (Chinese stock market) data service using AKShare."""
import logging
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from core.redis_client import cache_set, cache_get, TTL_ASHARE_PRICE

logger = logging.getLogger(__name__)


def _normalize_symbol(symbol: str) -> str:
    """Normalize A-share symbol: 600519 or sh600519 → 600519."""
    s = symbol.strip().lower().replace("sh", "").replace("sz", "").replace(".", "")
    return s.zfill(6)


def _to_float(val, default=None):
    """Safely convert a value to float."""
    try:
        return float(str(val).replace(",", "").replace("亿", "").strip())
    except Exception:
        return default


PERIOD_DAYS = {
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y":  365,
    "2y":  730,
}


async def get_ashare_stock(symbol: str, period: str = "1y") -> Dict[str, Any]:
    """Get A-share stock data (price history + basic info)."""
    sym = _normalize_symbol(symbol)
    cache_key = f"stock:CN:{sym}:{period}:price"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        # Determine exchange prefix and name
        prefix = "sh" if sym.startswith(("6", "9")) else "sz"
        exchange = "上交所" if prefix == "sh" else "深交所"
        full_sym = f"{prefix}{sym}"

        # Date range based on period
        days = PERIOD_DAYS.get(period, 365)
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        df = ak.stock_zh_a_hist(symbol=sym, period="daily", start_date=start, end_date=end, adjust="qfq")

        if df is None or df.empty:
            return {"error": f"No data found for {sym}"}

        # Normalize column names
        df = df.rename(columns={
            "日期": "date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume",
            "成交额": "amount", "涨跌幅": "pct_change",
        })
        df["date"] = df["date"].astype(str).str[:10]

        data = df[["date", "open", "high", "low", "close", "volume"]].to_dict("records")
        for row in data:
            for k in ["open", "high", "low", "close"]:
                row[k] = round(float(row[k]), 2)
            row["volume"] = int(row["volume"])

        # Get basic info from Eastmoney
        info = {}
        try:
            info_df = ak.stock_individual_info_em(symbol=sym)
            if info_df is not None and not info_df.empty:
                info_dict = dict(zip(info_df.iloc[:, 0], info_df.iloc[:, 1]))
                # Market cap: AKShare returns in yuan, convert to float
                mc_raw = info_dict.get("总市值", "") or info_dict.get("总市值(元)", "")
                lmc_raw = info_dict.get("流通市值", "") or info_dict.get("流通市值(元)", "")
                # Shares: AKShare may return in shares count or 亿股
                ts_raw = info_dict.get("总股本", "") or info_dict.get("总股本(股)", "")
                fs_raw = info_dict.get("流通股", "") or info_dict.get("流通股本", "")

                info = {
                    "name":          str(info_dict.get("股票简称", sym)),
                    "sector":        str(info_dict.get("行业", "")),
                    "exchange_name": str(info_dict.get("上市交易所", exchange)),
                    "listing_date":  str(info_dict.get("上市时间", "")),
                    # Numeric fields — convert safely
                    "market_cap":    _to_float(mc_raw),        # yuan
                    "float_mktcap":  _to_float(lmc_raw),       # yuan
                    "pe_ratio":      _to_float(info_dict.get("市盈率-动态") or info_dict.get("市盈率(动)")),
                    "pb_ratio":      _to_float(info_dict.get("市净率")),
                    "total_shares":  _to_float(ts_raw),        # shares
                    "float_shares":  _to_float(fs_raw),        # shares
                    "eps":           _to_float(info_dict.get("每股收益") or info_dict.get("每股收益(TTM)")),
                    "roe":           _to_float(info_dict.get("净资产收益率") or info_dict.get("ROE")),
                }
        except Exception as e:
            logger.warning(f"Failed to get A-share info for {sym}: {e}")

        last = data[-1] if data else {}
        prev = data[-2] if len(data) > 1 else {}
        change = last.get("close", 0) - prev.get("close", 0) if prev else 0
        change_pct = (change / prev["close"] * 100) if prev.get("close") else 0

        result = {
            "symbol":        sym,
            "market":        "CN",
            "full_symbol":   full_sym,
            "exchange":      exchange,
            "exchange_name": info.get("exchange_name", exchange),
            "listing_date":  info.get("listing_date", ""),
            "name":          info.get("name", sym),
            "sector":        info.get("sector", ""),
            "current_price": last.get("close", 0),
            "change":        round(change, 2),
            "change_pct":    round(change_pct, 2),
            # Numeric fundamental fields
            "market_cap":    info.get("market_cap"),    # yuan, may be None
            "float_mktcap":  info.get("float_mktcap"),
            "pe_ratio":      info.get("pe_ratio"),      # already float or None
            "pb_ratio":      info.get("pb_ratio"),
            "total_shares":  info.get("total_shares"),
            "float_shares":  info.get("float_shares"),
            "eps":           info.get("eps"),
            "roe":           info.get("roe"),
            "data":          data,
        }

        await cache_set(cache_key, result, TTL_ASHARE_PRICE)
        return result

    except Exception as e:
        logger.error(f"AKShare error for {sym}: {e}")
        return {"error": str(e)}


async def search_ashare(query: str) -> list:
    """Search A-share stocks by name or code."""
    try:
        df = ak.stock_info_a_code_name()
        if df is None or df.empty:
            return []
        mask = df["name"].str.contains(query, na=False) | df["code"].str.contains(query, na=False)
        results = df[mask].head(10)
        return [{"symbol": row["code"], "name": row["name"]} for _, row in results.iterrows()]
    except Exception as e:
        logger.warning(f"A-share search failed: {e}")
        return []


async def screen_ashare(
    min_pe: Optional[float] = None, max_pe: Optional[float] = None,
    sector: Optional[str] = None, limit: int = 50
) -> list:
    """Screen A-share stocks by basic criteria."""
    try:
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return []

        df = df.rename(columns={
            "代码": "symbol", "名称": "name", "最新价": "price",
            "涨跌幅": "pct_change", "市盈率-动态": "pe",
            "总市值": "market_cap", "所属行业": "sector",
        })

        if "pe" in df.columns:
            if min_pe is not None:
                df = df[pd.to_numeric(df["pe"], errors="coerce") >= min_pe]
            if max_pe is not None:
                df = df[pd.to_numeric(df["pe"], errors="coerce") <= max_pe]

        return df.head(limit)[["symbol", "name", "price", "pct_change", "pe", "market_cap"]].to_dict("records")
    except Exception as e:
        logger.warning(f"A-share screening failed: {e}")
        return []
