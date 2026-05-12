# FinSignal — AI-Powered Financial Analysis Platform

> Real-time market data and multi-agent AI investment analysis

**Live Demo:** [finsignal.app](https://finsignal.app)

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | Vue 3 · TypeScript · Vite · Pinia |
| Backend | FastAPI · SQLAlchemy · SQLite · MongoDB |
| Cache | Redis |
| AI | LangGraph · LangChain · TradingAgents · OpenAI / Anthropic / Google / DeepSeek |
| Deployment | Docker Compose · Nginx · Let's Encrypt |

## Features

- **Dashboard** — Real-time watchlist prices, fundamentals snapshot, cached AI decision badges
- **Multi-Agent AI Analysis** — Market, sentiment, and fundamentals agents run in parallel via LangGraph; results stream in real time over SSE; portfolio manager agent issues a final BUY / SELL / HOLD decision
- **Stock Detail** — Price history charts, financial metrics, and peer comparison
- **Price Forecast** — LSTM neural network + fundamental signals with confidence intervals
- **Anomaly Detection** — Statistical detection of unusual price and volume movements
- **Paper Trading** — Simulated portfolio management
- **JWT Authentication** — Register / login with per-user API key storage and analysis history

## Getting Started

```bash
# 1. Copy environment template
cp backend/.env.example backend/.env
# Edit backend/.env and fill in SECRET_KEY and other config

# 2. Start all services
docker compose up --build
```

Visit http://localhost

## Deployment

```bash
bash deploy.sh
```

Requires a root-level `.env` (with `REDIS_PASSWORD`) and `backend/.env` to be configured before running.
