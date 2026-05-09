# FinSignal — AI-Powered Financial Analysis Platform

> 实时股票行情 + AI 多智能体投资分析平台

**Live Demo:** [finsignal.app](https://finsignal.app)

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 · TypeScript · Vite · Pinia |
| 后端 | FastAPI · SQLAlchemy · SQLite · MongoDB |
| 缓存 | Redis |
| AI | LangGraph · LangChain · TradingAgents · OpenAI / Anthropic / Google / DeepSeek |
| 部署 | Docker Compose · Nginx · Let's Encrypt |

## 功能

- **Dashboard** — 实时股票行情（watchlist 5 支）、基本面快照、AI 分析缓存徽章
- **AI 多智能体分析** — 市场、情绪、基本面多路 Agent 并行分析，SSE 实时流式输出，最终生成 BUY / SELL / HOLD 决策
- **股票详情** — 历史 K 线、财务指标、同行业对比
- **A 股支持** — 接入 A 股行情数据
- **模拟交易** — Paper Trading 仓位管理
- **JWT 认证** — 注册/登录，接口全局鉴权

## 本地运行

```bash
# 1. 复制环境变量模板
cp backend/.env.example backend/.env
# 编辑 backend/.env 填写 SECRET_KEY 等配置

# 2. 启动所有服务
docker compose up --build
```

访问 http://localhost

## 部署

```bash
bash deploy.sh
```

需要提前配置根目录 `.env`（含 `REDIS_PASSWORD`）和 `backend/.env`。
