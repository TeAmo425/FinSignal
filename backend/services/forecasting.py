"""
LSTM + Fundamentals Stock Price Forecasting
============================================
Architecture:
  - LSTM(input=8 price/technical features, hidden=64, layers=2, dropout=0.2)
  - Concat LSTM final hidden state with 8 fundamental scalars
  - Dense head: Linear(72→48) → GELU → Dropout → Linear(48→MAX_HORIZON)

Price features per timestep:
  close_norm, log_volume_norm, daily_range, daily_return,
  rsi14, macd_hist_norm, close_sma20_ratio, close_sma50_ratio

Fundamental features (fetched from yfinance .info):
  pe_ratio, forward_pe, revenue_growth, profit_margin,
  roe, debt_equity, ev_ebitda, beta

Uncertainty: MC-Dropout (100 passes) → mean ± 1.65σ confidence interval
Caching: trained models cached in memory by (symbol, last_date) to avoid re-training
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

SEQ_LEN = 40          # lookback window (trading days)
MAX_HORIZON = 90      # max forecast horizon
PRICE_FEAT = 8        # features per timestep
FUND_FEAT = 8         # fundamental scalar features
HIDDEN = 32
LSTM_LAYERS = 1
EPOCHS = 15
BATCH_SIZE = 64
LR = 2e-3
MC_PASSES = 20        # Monte Carlo dropout runs for uncertainty

# In-memory model cache: (symbol, last_date) → (model, price_scaler, fund_vec)
_model_cache: dict = {}


# ─── Neural Network ─────────────────────────────────────────────────────────

class LSTMForecaster(nn.Module):
    def __init__(self, price_feat=PRICE_FEAT, fund_feat=FUND_FEAT,
                 hidden=HIDDEN, layers=LSTM_LAYERS, out=MAX_HORIZON):
        super().__init__()
        self.lstm = nn.LSTM(
            price_feat, hidden, layers,
            batch_first=True, dropout=0.2 if layers > 1 else 0.0
        )
        self.head = nn.Sequential(
            nn.Linear(hidden + fund_feat, 48),
            nn.GELU(),
            nn.Dropout(0.25),
            nn.Linear(48, out),
        )

    def forward(self, x_seq, x_fund):
        # x_seq: (B, SEQ_LEN, PRICE_FEAT)  x_fund: (B, FUND_FEAT)
        _, (h, _) = self.lstm(x_seq)
        h_last = h[-1]                          # (B, hidden)
        combined = torch.cat([h_last, x_fund], dim=1)
        return self.head(combined)              # (B, MAX_HORIZON)


# ─── Feature Engineering ────────────────────────────────────────────────────

def _ema(series: np.ndarray, span: int) -> np.ndarray:
    return pd.Series(series).ewm(span=span, adjust=False).mean().values

def _rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    delta = np.diff(prices, prepend=prices[0])
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = pd.Series(gain).ewm(alpha=1/period, adjust=False).mean().values
    avg_loss = pd.Series(loss).ewm(alpha=1/period, adjust=False).mean().values
    rs = np.where(avg_loss == 0, 100.0, avg_gain / (avg_loss + 1e-10))
    return 100 - 100 / (1 + rs)

def _macd_hist(prices: np.ndarray) -> np.ndarray:
    fast = _ema(prices, 12)
    slow = _ema(prices, 26)
    macd = fast - slow
    signal = _ema(macd, 9)
    return macd - signal

def _sma(prices: np.ndarray, window: int) -> np.ndarray:
    return pd.Series(prices).rolling(window, min_periods=1).mean().values

def _safe_log_vol(volume: np.ndarray) -> np.ndarray:
    v = np.where(volume <= 0, 1.0, volume)
    return np.log(v)

def build_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """
    Returns array of shape (N, PRICE_FEAT):
    [close_norm, log_vol_norm, daily_range, daily_return,
     rsi14, macd_hist_norm, close_sma20_ratio, close_sma50_ratio]
    """
    close  = df["close"].values.astype(float)
    high   = df["high"].values.astype(float)
    low    = df["low"].values.astype(float)
    volume = df["volume"].values.astype(float)
    N = len(close)

    close_scaler = MinMaxScaler()
    close_norm = close_scaler.fit_transform(close.reshape(-1, 1)).ravel()

    log_vol = _safe_log_vol(volume)
    log_vol_norm = MinMaxScaler().fit_transform(log_vol.reshape(-1, 1)).ravel()

    daily_range = np.where(close > 0, (high - low) / close, 0.0)

    returns = np.zeros(N)
    returns[1:] = close[1:] / (close[:-1] + 1e-10) - 1
    returns = np.clip(returns, -0.2, 0.2)

    rsi_raw  = _rsi(close) / 100.0

    macd_h   = _macd_hist(close)
    macd_std = np.std(macd_h) + 1e-10
    macd_norm = np.clip(macd_h / macd_std, -3, 3) / 3.0

    sma20 = _sma(close, 20)
    sma50 = _sma(close, 50)
    r20   = np.where(sma20 > 0, close / sma20 - 1, 0.0)
    r50   = np.where(sma50 > 0, close / sma50 - 1, 0.0)
    r20   = np.clip(r20, -0.3, 0.3)
    r50   = np.clip(r50, -0.3, 0.3)

    features = np.column_stack([
        close_norm, log_vol_norm, daily_range, returns,
        rsi_raw, macd_norm, r20, r50,
    ]).astype(np.float32)

    return features, close_scaler   # also return scaler for inverse transform


# ─── Fundamentals ────────────────────────────────────────────────────────────

def _clamp_norm(val, lo, hi, default=0.5):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    return float(np.clip((val - lo) / (hi - lo + 1e-10), 0.0, 1.0))

def fetch_fundamentals_vector(symbol: str) -> np.ndarray:
    """Fetch 8 fundamental scalars from yfinance, normalised to [0,1]."""
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception:
        info = {}

    vec = np.array([
        _clamp_norm(info.get("trailingPE"),        0, 80,  default=0.3),
        _clamp_norm(info.get("forwardPE"),          0, 60,  default=0.3),
        _clamp_norm(info.get("revenueGrowth"),     -0.3, 0.8, default=0.3),
        _clamp_norm(info.get("profitMargins"),     -0.1, 0.5, default=0.3),
        _clamp_norm(info.get("returnOnEquity"),    -0.2, 0.8, default=0.3),
        _clamp_norm(info.get("debtToEquity"),        0, 300, default=0.3),
        _clamp_norm(info.get("enterpriseToEbitda"), 0, 50,  default=0.3),
        _clamp_norm(info.get("beta"),              -0.5, 3.0, default=0.4),
    ], dtype=np.float32)
    return vec


# ─── Training ────────────────────────────────────────────────────────────────

def _make_windows(features: np.ndarray, close_norm: np.ndarray):
    """Sliding window: input=SEQ_LEN days → target=next MAX_HORIZON days (norm prices)."""
    X, y = [], []
    total = MAX_HORIZON + SEQ_LEN
    for i in range(len(features) - total + 1):
        X.append(features[i : i + SEQ_LEN])
        y.append(close_norm[i + SEQ_LEN : i + SEQ_LEN + MAX_HORIZON])
    if not X:
        return None, None
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def train_model(features: np.ndarray, close_norm: np.ndarray,
                fund_vec: np.ndarray) -> LSTMForecaster:
    X, y = _make_windows(features, close_norm)
    if X is None:
        return None

    fund_tensor = torch.tensor(fund_vec).unsqueeze(0).expand(len(X), -1)

    dataset = TensorDataset(
        torch.tensor(X),
        fund_tensor.clone(),
        torch.tensor(y),
    )
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    model = LSTMForecaster()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    criterion = nn.HuberLoss()

    model.train()
    for _ in range(EPOCHS):
        for xb, fb, yb in loader:
            optimizer.zero_grad()
            pred = model(xb, fb)
            loss = criterion(pred, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        scheduler.step()

    return model


# ─── Inference with MC-Dropout ───────────────────────────────────────────────

def mc_predict(model: LSTMForecaster, seq: np.ndarray,
               fund_vec: np.ndarray, n_passes: int = MC_PASSES) -> tuple:
    """Returns (mean_norm, std_norm) both shape (MAX_HORIZON,)"""
    model.train()   # keep dropout active
    x = torch.tensor(seq[np.newaxis], dtype=torch.float32)   # (1, SEQ_LEN, FEAT)
    f = torch.tensor(fund_vec[np.newaxis], dtype=torch.float32)  # (1, FUND)

    with torch.no_grad():
        preds = torch.cat([model(x, f) for _ in range(n_passes)], dim=0)  # (N, H)

    return preds.mean(dim=0).numpy(), preds.std(dim=0).numpy()


# ─── Public API ──────────────────────────────────────────────────────────────

def forecast_stock(data: list, horizon: int = 30, symbol: str = "") -> dict:
    """
    Main entry point called by the forecast router.
    Falls back to statistical model on any error.
    """
    try:
        return _lstm_forecast(data, horizon, symbol)
    except Exception as e:
        logger.warning(f"LSTM forecast failed ({e}), falling back to statistical model")
        return _statistical_fallback(data, horizon)


def _lstm_forecast(data: list, horizon: int, symbol: str) -> dict:
    if not data or len(data) < SEQ_LEN + MAX_HORIZON + 10:
        raise ValueError(f"Need at least {SEQ_LEN + MAX_HORIZON + 10} data points")

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date")

    last_date = str(df["date"].iloc[-1].date())
    cache_key = (symbol.upper(), last_date)

    # ── Use cached model if available ──────────────────────────────────────
    if cache_key in _model_cache:
        model, price_scaler, fund_vec = _model_cache[cache_key]
        logger.info(f"Using cached LSTM model for {symbol}")
    else:
        logger.info(f"Training LSTM model for {symbol} ({len(df)} rows)…")
        features, price_scaler = build_feature_matrix(df)
        close_norm = price_scaler.transform(
            df["close"].values.reshape(-1, 1)
        ).ravel().astype(np.float32)

        fund_vec = fetch_fundamentals_vector(symbol) if symbol else np.full(FUND_FEAT, 0.3, dtype=np.float32)
        model = train_model(features, close_norm, fund_vec)
        if model is None:
            raise ValueError("Not enough windows to train")
        _model_cache[cache_key] = (model, price_scaler, fund_vec)

    # ── Inference ──────────────────────────────────────────────────────────
    features_full, _ = build_feature_matrix(df)
    # Re-normalise with the stored scaler
    close_norm_full = price_scaler.transform(
        df["close"].values.reshape(-1, 1)
    ).ravel().astype(np.float32)

    last_seq = features_full[-SEQ_LEN:]  # most recent window

    # Rebuild feature matrix with the price normalised using the cached scaler
    # (features already use their own internal scaler for close_norm slot)
    mean_norm, std_norm = mc_predict(model, last_seq, fund_vec)

    # Inverse-transform back to price space
    mean_price = price_scaler.inverse_transform(
        mean_norm[:MAX_HORIZON].reshape(-1, 1)
    ).ravel()
    # Propagate std through linear inverse (scale factor)
    scale = price_scaler.data_range_[0] if hasattr(price_scaler, "data_range_") else 1.0
    std_price = std_norm[:MAX_HORIZON] * scale

    last_close = float(df["close"].iloc[-1])
    last_dt    = df["date"].iloc[-1]

    # Generate business days only (skip Sat/Sun)
    bday_dates = pd.bdate_range(start=last_dt + pd.Timedelta(days=1), periods=horizon)

    forecast_list = []
    for i in range(horizon):
        future_dt = bday_dates[i]
        p = float(np.clip(mean_price[i], last_close * 0.5, last_close * 2.0))
        sigma = float(std_price[i])
        z = 1.65   # ~90% CI
        upper = round(p + z * sigma, 2)
        lower = round(max(p - z * sigma, 0.01), 2)
        forecast_list.append({
            "date": future_dt.strftime("%Y-%m-%d"),
            "forecast": round(p, 2),
            "upper": upper,
            "lower": lower,
        })

    last_forecast = forecast_list[-1]["forecast"]
    trend = "bullish" if last_forecast > last_close else "bearish"

    # Confidence: inverse of mean normalised std (lower uncertainty = higher confidence)
    mean_std_pct = float(np.mean(std_price[:horizon]) / (last_close + 1e-10))
    confidence = round(float(np.clip(88 - mean_std_pct * 400, 45, 92)), 1)

    # Fundamental summary for front-end
    fund_summary = _build_fund_summary(fund_vec)

    return {
        "trend": trend,
        "confidence": confidence,
        "model": "LSTM + Fundamentals",
        "price_range": [forecast_list[-1]["lower"], forecast_list[-1]["upper"]],
        "forecast": forecast_list,
        "fundamentals_used": fund_summary,
    }


def _build_fund_summary(fund_vec: np.ndarray) -> dict:
    """Human-readable summary of the fundamental inputs (for UI display)."""
    labels = ["P/E", "Forward P/E", "Revenue Growth", "Profit Margin",
              "ROE", "D/E", "EV/EBITDA", "Beta"]
    return {labels[i]: round(float(fund_vec[i]), 3) for i in range(len(labels))}


# ─── Statistical Fallback (original model) ───────────────────────────────────

def _statistical_fallback(data: list, horizon: int = 30) -> dict:
    """EMA trend + mean-reverting random walk — used when LSTM fails."""
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date").tail(90)
    prices = df["close"].values.astype(float)
    n = len(prices)
    if n < 10:
        return {"error": "Insufficient data"}

    span = min(20, n // 2)
    ema = pd.Series(prices).ewm(span=span, adjust=False).mean().values
    recent_slope = (ema[-1] - ema[-min(10, n)]) / min(10, n)
    long_slope   = (ema[-1] - ema[0]) / n
    base_slope   = recent_slope * 0.6 + long_slope * 0.4

    daily_returns = np.diff(prices) / prices[:-1]
    vol = float(np.std(daily_returns)) if len(daily_returns) > 1 else 0.015

    rng = np.random.default_rng(seed=int(prices[-1] * 100) % (2**31))
    last_price = float(prices[-1])
    last_ema   = float(ema[-1])
    last_date  = df["date"].iloc[-1]

    forecast_list = []
    price_sim = last_price
    ema_sim   = last_ema

    for i in range(1, horizon + 1):
        future_date = last_date + pd.Timedelta(days=i)
        ema_sim  += base_slope * np.exp(-i * 0.02)
        reversion = (ema_sim - price_sim) * 0.08
        noise     = rng.normal(0, vol * price_sim)
        price_sim = price_sim + reversion + noise
        margin    = price_sim * vol * np.sqrt(i) * 1.65
        forecast_list.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "forecast": round(float(price_sim), 2),
            "upper": round(float(price_sim + margin), 2),
            "lower": round(float(max(price_sim - margin, 0.01)), 2),
        })

    confidence = round(max(45.0, min(88.0, 82.0 - vol * 500)), 1)
    last_fp = forecast_list[-1]["forecast"]

    return {
        "trend": "bullish" if last_fp > last_price else "bearish",
        "confidence": confidence,
        "model": "EMA + Random Walk (fallback)",
        "price_range": [forecast_list[-1]["lower"], forecast_list[-1]["upper"]],
        "forecast": forecast_list,
        "fundamentals_used": {},
    }
