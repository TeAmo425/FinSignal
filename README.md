# FinSignal — AI-Powered Financial Analysis Platform

> Real-time market data combined with a multi-agent AI system for investment research

**Live Demo:** [finsignal.app](https://finsignal.app)

---

## Overview

FinSignal is a full-stack financial analysis platform that combines real-time stock market data with an AI-driven multi-agent pipeline. Users can monitor watchlists, explore fundamentals, run LSTM-based price forecasts, detect anomalies, and trigger a team of specialized AI agents that collaborate to produce a structured BUY / SELL / HOLD recommendation.

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | Vue 3 · TypeScript · Vite · Pinia · ECharts |
| Backend | FastAPI · SQLAlchemy · SQLite · Motor (async MongoDB) |
| Cache | Redis (stock prices TTL 2h, fundamentals TTL 24h) |
| AI / Agents | LangGraph · LangChain · TradingAgents framework |
| LLM Providers | OpenAI · Anthropic · Google Gemini · DeepSeek |
| Deployment | Docker Compose · Nginx · Let's Encrypt (HTTPS) |

---

## Features

### Markets
- **Dashboard** — Real-time prices for a configurable watchlist, fundamentals snapshot, and cached AI decision badges per ticker
- **Market Hub** — Search US equities by symbol or company name; click through to full stock detail pages
- **Stock Detail** — Interactive price charts with MA / RSI / MACD overlays, 52-week range, financial metrics, and sector peer comparison table
- **Price Forecast** — LSTM neural network trained on 2 years of price and volume data, augmented with fundamental signals (P/E, revenue growth, ROE, beta). Outputs a directional trend, confidence score, and confidence interval band. Falls back to an EMA statistical model if training exceeds the time limit
- **Anomaly Detection** — Statistical outlier detection on price and volume to surface unusual market activity

### AI Trading Agents
The core feature. Powered by **LangGraph** for agent orchestration and **LangChain** for unified LLM access:

1. **Market Agent** — Analyzes price history and technical indicators
2. **Sentiment Agent** — Evaluates news headlines and social signals
3. **Fundamentals Agent** — Reviews financial ratios and earnings data
4. **Portfolio Manager Agent** — Synthesizes all three reports and issues a final **BUY / SELL / HOLD** decision with reasoning

Results stream to the browser in real time via **Server-Sent Events (SSE)** — no polling, no page refresh. Supports OpenAI, Anthropic, Google Gemini, and DeepSeek as interchangeable LLM backends.

### Intelligence & Data
- **Reports** — All analyses are persisted to MongoDB per user account and accessible across devices. Filter by decision, view full agent breakdowns in a detail modal
- **Paper Trading** — Simulated portfolio for testing strategies without real capital
- **Datasets** — Upload and manage custom CSV / Excel datasets for analysis
- **Stock Screener** — Filter equities by financial metrics

### Account & Security
- JWT authentication with bcrypt password hashing
- Per-user API key storage (saved server-side, synced on login)
- Rate limiting via slowapi
- Redis-cached responses to minimize external API calls
- All secrets excluded from version control via `.gitignore`

---

## Architecture

```
Browser
  │
  ├── HTTPS (Let's Encrypt)
  │
Host Nginx (reverse proxy)
  ├── /          → Docker: Frontend (Vue 3 + Nginx, port 8080)
  └── /api/      → Docker: Backend (FastAPI, port 8001)
                      ├── SQLite  (users, sessions)
                      ├── MongoDB (analysis history, paper trades)
                      └── Redis   (stock price & fundamentals cache)
```

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- An API key from at least one LLM provider (OpenAI, Anthropic, Google, or DeepSeek)

### Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/TeAmo425/FinSignal.git
cd FinSignal

# 2. Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env — set SECRET_KEY, and optionally pre-configure LLM API keys

# Create root .env for Redis password
echo "REDIS_PASSWORD=your_strong_password" > .env

# 3. Start all services
docker compose up --build
```

Visit **http://localhost** in your browser.

### Environment Variables

`backend/.env`:
```env
SECRET_KEY=your_secret_key_here
ENVIRONMENT=development
# Optional: pre-configure LLM keys (users can also add them via Settings)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Root `.env`:
```env
REDIS_PASSWORD=your_strong_redis_password
```

---

## Deployment

The project is designed for single-command deployment on any Linux server with Docker installed.

```bash
bash deploy.sh
```

For production with a custom domain and HTTPS, configure a host-level Nginx reverse proxy pointing to the Docker containers, then obtain an SSL certificate with Certbot:

```bash
certbot --nginx -d yourdomain.com
```

---

## Project Structure

```
FinSignal/
├── backend/
│   ├── routers/          # FastAPI route handlers
│   ├── services/         # Business logic (stock data, forecasting, AI agents)
│   ├── models/           # SQLAlchemy ORM models
│   ├── core/             # Redis client, MongoDB connection, auth dependencies
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/        # Page components
│   │   ├── stores/       # Pinia state management
│   │   ├── composables/  # useTradingAgent (SSE streaming logic)
│   │   └── api/          # Axios instance with JWT interceptor
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```
