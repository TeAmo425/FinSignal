from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os

from services.trading_agents_service import stream_trading_analysis, PROVIDER_DEFAULTS
from models.user import User
from core.dependencies import get_current_user

router = APIRouter(prefix="/api/trading-agents", tags=["trading-agents"])


class TradingAnalysisRequest(BaseModel):
    ticker: str
    trade_date: str
    analysts: Optional[List[str]] = None
    # LLM provider
    llm_provider: str = "openai"          # openai | anthropic | google | openrouter | ollama
    deep_model: str = ""                  # empty → use provider default
    quick_model: str = ""
    # Provider-specific API keys (front-end sends whichever is relevant)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    backend_url: Optional[str] = None    # for OpenRouter / Ollama custom base URLs
    # Thinking / reasoning modes (v0.2.2)
    openai_reasoning_effort: Optional[str] = None   # "low" | "medium" | "high"
    anthropic_effort: Optional[str] = None          # "low" | "medium" | "high"
    google_thinking_level: Optional[str] = None     # "minimal" | "low" | "high"
    # Debate depth
    max_debate_rounds: int = 1
    max_risk_discuss_rounds: int = 1


@router.get("/providers")
def list_providers():
    """Return supported LLM providers and their default models."""
    return {
        provider: {
            "deep_model":  defaults["deep"],
            "quick_model": defaults["quick"],
        }
        for provider, defaults in PROVIDER_DEFAULTS.items()
    }


@router.post("/analyze")
async def analyze(req: TradingAnalysisRequest, current_user: User = Depends(get_current_user)):
    """
    Launch TradingAgents v0.2.2 multi-agent analysis.
    Returns a Server-Sent Events stream of per-agent results.
    """
    provider = req.llm_provider.lower()

    # Resolve API key: prefer request body, fall back to environment
    openai_key    = (req.openai_api_key    or "").strip() or os.getenv("OPENAI_API_KEY",    "")
    anthropic_key = (req.anthropic_api_key or "").strip() or os.getenv("ANTHROPIC_API_KEY", "")
    google_key    = (req.google_api_key    or "").strip() or os.getenv("GOOGLE_API_KEY",    "")

    deepseek_key  = (req.deepseek_api_key  or "").strip() or os.getenv("DEEPSEEK_API_KEY",  "")

    # Validate that required key is present for the selected provider
    key_required = {
        "openai":     openai_key,
        "anthropic":  anthropic_key,
        "google":     google_key,
        "openrouter": openai_key,   # OpenRouter uses OPENAI_API_KEY slot
        "ollama":     "no-key-needed",
        "deepseek":   deepseek_key,
    }
    if not key_required.get(provider, ""):
        raise HTTPException(
            status_code=400,
            detail=f"API key for '{provider}' is not configured. Please add it in Settings → API Keys."
        )

    if not req.ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty")
    if not req.trade_date:
        raise HTTPException(status_code=400, detail="Trade date cannot be empty")

    return StreamingResponse(
        stream_trading_analysis(
            ticker=req.ticker.strip().upper(),
            trade_date=req.trade_date,
            openai_api_key=openai_key,
            anthropic_api_key=anthropic_key,
            google_api_key=google_key,
            deepseek_api_key=deepseek_key,
            backend_url=req.backend_url or "",
            analysts=req.analysts,
            deep_model=req.deep_model,
            quick_model=req.quick_model,
            llm_provider=provider,
            max_debate_rounds=req.max_debate_rounds,
            max_risk_discuss_rounds=req.max_risk_discuss_rounds,
            openai_reasoning_effort=req.openai_reasoning_effort,
            anthropic_effort=req.anthropic_effort,
            google_thinking_level=req.google_thinking_level,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection":    "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class BatchRequest(BaseModel):
    tickers: List[str]
    trade_date: str
    analysts: Optional[List[str]] = None
    llm_provider: str = "openai"
    deep_model: str = ""
    quick_model: str = ""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    max_debate_rounds: int = 1


@router.post("/batch")
async def batch_analyze(req: BatchRequest, current_user: User = Depends(get_current_user)):
    """Batch analysis returning SSE stream with per-ticker events."""
    # Validate tickers
    tickers = [t.strip().upper() for t in req.tickers[:5]]  # max 5
    if not tickers:
        raise HTTPException(400, "At least one ticker required")

    async def generate():
        import asyncio
        import json

        async def run_single(ticker: str):
            async for chunk in stream_trading_analysis(
                ticker=ticker,
                trade_date=req.trade_date,
                openai_api_key=(req.openai_api_key or "").strip() or os.getenv("OPENAI_API_KEY", ""),
                anthropic_api_key=(req.anthropic_api_key or "").strip() or os.getenv("ANTHROPIC_API_KEY", ""),
                google_api_key=(req.google_api_key or "").strip() or os.getenv("GOOGLE_API_KEY", ""),
                deepseek_api_key=(req.deepseek_api_key or "").strip() or os.getenv("DEEPSEEK_API_KEY", ""),
                analysts=req.analysts,
                deep_model=req.deep_model,
                quick_model=req.quick_model,
                llm_provider=req.llm_provider,
                max_debate_rounds=req.max_debate_rounds,
            ):
                # Prefix each SSE event with ticker
                try:
                    data = json.loads(chunk[6:])
                    data["ticker"] = ticker
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                except Exception:
                    yield chunk

        # Run sequentially to avoid overwhelming the LLM API
        for ticker in tickers:
            yield f"data: {json.dumps({'type': 'ticker_start', 'ticker': ticker})}\n\n"
            async for event in run_single(ticker):
                yield event

        yield f"data: {json.dumps({'type': 'batch_done', 'tickers': tickers})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
