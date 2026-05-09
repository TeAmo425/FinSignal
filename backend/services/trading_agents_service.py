"""
TradingAgents v0.2.2 streaming service
Supports: OpenAI, Anthropic (Claude), Google (Gemini), OpenRouter, Ollama
"""
import sys
import os
import io
import json
import asyncio
import threading
from typing import AsyncGenerator, List, Optional

# Add the cloned TradingAgents repo to Python path
_REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tradingagents_repo"))
if _REPO_PATH not in sys.path:
    sys.path.insert(0, _REPO_PATH)

# Force UTF-8 for cross-platform consistency (v0.2.2 fix)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.graph.propagation import Propagator
from tradingagents.default_config import DEFAULT_CONFIG


# ─── Field → display name mapping ─────────────────────────────────────────
WATCH_FIELDS = [
    ("market_report",           "Market Analyst",       "Technical & Price Action"),
    ("sentiment_report",        "Sentiment Analyst",    "Social Media Sentiment"),
    ("news_report",             "News Analyst",         "News & Insider Activity"),
    ("fundamentals_report",     "Fundamentals Analyst", "Earnings & Valuation"),
    ("investment_debate_state", "Bull / Bear Debate",   "Research Debate"),
    ("trader_investment_plan",  "Trader",               "Trading Decision"),
    ("risk_debate_state",       "Risk Panel",           "Risk Assessment"),
    ("investment_plan",         "Investment Committee", "Consolidated Plan"),
    ("final_trade_decision",    "Portfolio Manager",    "Final Trade Decision"),
]

# Provider → env var name
_API_KEY_ENV = {
    "openai":     "OPENAI_API_KEY",
    "anthropic":  "ANTHROPIC_API_KEY",
    "google":     "GOOGLE_API_KEY",
    "openrouter": "OPENAI_API_KEY",   # OpenRouter uses OpenAI-compat API
    "ollama":     None,               # No key needed
}

# Default models per provider
PROVIDER_DEFAULTS = {
    "openai":     {"deep": "gpt-4o",                   "quick": "gpt-4o-mini"},
    "anthropic":  {"deep": "claude-sonnet-4-6",        "quick": "claude-haiku-4-5-20251001"},
    "google":     {"deep": "gemini-2.5-pro-preview-05-06", "quick": "gemini-2.0-flash"},
    "openrouter": {"deep": "openai/gpt-4o",            "quick": "openai/gpt-4o-mini"},
    "ollama":     {"deep": "llama3.1:70b",             "quick": "llama3.1:8b"},
    "deepseek":   {"deep": "deepseek-reasoner",        "quick": "deepseek-chat"},
}


def _extract_content(field: str, value) -> str:
    """Extract readable text from a state field value."""
    if field in ("investment_debate_state", "risk_debate_state"):
        if isinstance(value, dict):
            # v0.2.2: prefer judge_decision, fall back to full history
            return value.get("judge_decision") or value.get("history") or ""
    if isinstance(value, list):
        # Normalise list responses (v0.2.2 Anthropic/Google fix)
        return "\n".join(str(v) for v in value if v)
    return str(value) if value else ""


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_trading_analysis(
    ticker: str,
    trade_date: str,
    openai_api_key: str = "",
    anthropic_api_key: str = "",
    google_api_key: str = "",
    deepseek_api_key: str = "",
    backend_url: str = "",
    analysts: Optional[List[str]] = None,
    deep_model: str = "",
    quick_model: str = "",
    llm_provider: str = "openai",
    max_debate_rounds: int = 1,
    max_risk_discuss_rounds: int = 1,
    openai_reasoning_effort: Optional[str] = None,
    anthropic_effort: Optional[str] = None,
    google_thinking_level: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Run TradingAgents v0.2.2 multi-agent analysis and stream each agent result as SSE.

    SSE event types:
      {"type": "init",         "message": "..."}
      {"type": "agent_update", "agent": "...", "label": "...", "field": "...", "content": "..."}
      {"type": "done",         "message": "Analysis complete"}
      {"type": "error",        "message": "..."}
    """
    provider = llm_provider.lower()
    if analysts is None:
        analysts = ["market", "social", "news", "fundamentals"]

    # Resolve models — use provider defaults if not explicitly set
    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["openai"])
    resolved_deep  = deep_model.strip()  or defaults["deep"]
    resolved_quick = quick_model.strip() or defaults["quick"]

    # Build v0.2.2 config
    config = {
        **DEFAULT_CONFIG,
        "llm_provider":              provider,
        "deep_think_llm":            resolved_deep,
        "quick_think_llm":           resolved_quick,
        "max_debate_rounds":         max_debate_rounds,
        "max_risk_discuss_rounds":   max_risk_discuss_rounds,
        "openai_reasoning_effort":   openai_reasoning_effort,
        "anthropic_effort":          anthropic_effort,
        "google_thinking_level":     google_thinking_level,
    }
    if backend_url:
        config["backend_url"] = backend_url

    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def run_sync():
        try:
            # Set API keys in environment
            if openai_api_key:
                os.environ["OPENAI_API_KEY"] = openai_api_key
            if anthropic_api_key:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
            if google_api_key:
                os.environ["GOOGLE_API_KEY"] = google_api_key
                os.environ["GEMINI_API_KEY"] = google_api_key
            if provider == "deepseek" and deepseek_api_key:
                os.environ["OPENAI_API_KEY"] = deepseek_api_key
                config["backend_url"] = "https://api.deepseek.com/v1"

            loop.call_soon_threadsafe(
                queue.put_nowait,
                _sse({"type": "init", "message": f"Initialising {ticker} analysis with {provider.capitalize()} ({resolved_deep})…"}),
            )

            ta = TradingAgentsGraph(selected_analysts=analysts, config=config)
            propagator = Propagator()
            init_state = propagator.create_initial_state(ticker, trade_date)
            args = propagator.get_graph_args()

            prev_fields: dict = {}

            for chunk in ta.graph.stream(init_state, **args):
                for field, agent, label in WATCH_FIELDS:
                    # chunk keys are node names; find the state value inside
                    val = None
                    if field in chunk:
                        val = chunk[field]
                    else:
                        # v0.2.2 wraps state in node-keyed dicts
                        for node_val in chunk.values():
                            if isinstance(node_val, dict) and field in node_val:
                                val = node_val[field]
                                break
                    if not val:
                        continue
                    content = _extract_content(field, val)
                    if not content or content == prev_fields.get(field, ""):
                        continue
                    prev_fields[field] = content
                    loop.call_soon_threadsafe(
                        queue.put_nowait,
                        _sse({
                            "type":    "agent_update",
                            "agent":   agent,
                            "label":   label,
                            "field":   field,
                            "content": content,
                        }),
                    )

            loop.call_soon_threadsafe(
                queue.put_nowait,
                _sse({"type": "done", "message": "Analysis complete"}),
            )

        except Exception as e:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                _sse({"type": "error", "message": str(e)}),
            )

    t = threading.Thread(target=run_sync, daemon=True)
    t.start()

    while True:
        data = await queue.get()
        yield data
        try:
            parsed = json.loads(data[6:])
            if parsed.get("type") in ("done", "error"):
                break
        except Exception:
            break

    t.join(timeout=10)
