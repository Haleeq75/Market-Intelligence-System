# Market Intelligence System

A production-grade, multi-agent AI system for market movement prediction. The system deploys an **Adversarial Swarm** architecture: a Bull Agent and Bear Agent debate every thesis, and an Arbiter Agent issues the final BUY / HOLD / SELL verdict — all in real-time with a premium dark-mode dashboard.

---

## Architecture Overview

```
External Data Sources (News, Alt Data, Market Feeds, pgvector history)
        ↓  [MCP Protocol]
  ┌─────────────────────────────────────────────────────────┐
  │                  FastAPI Backend                        │
  │                                                         │
  │   ┌──────────┐   ┌──────────┐   ┌──────────┐          │
  │   │  The Ear │ → │ Bull     │ → │ Bear     │          │
  │   │ (Ingest) │   │ Agent    │   │ Agent    │          │
  │   └──────────┘   └──────────┘   └──────────┘          │
  │                         ↓  [A2A State]                  │
  │                   ┌───────────┐                         │
  │                   │ Arbiter   │  → BUY / HOLD / SELL   │
  │                   └───────────┘                         │
  │                         ↓                               │
  │         PostgreSQL + pgvector (Decision Journal)        │
  │                         ↓                               │
  │            WebSocket (real-time events)                 │
  └─────────────────────────────────────────────────────────┘
        ↓
  Next.js Control Tower Dashboard (dark mode, real-time)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend API** | Python 3.11, FastAPI (async), Pydantic v2 |
| **AI Orchestration** | LangGraph (StateGraph), LangChain, OpenAI GPT-4o |
| **Data Ingestion** | MCP Protocol pattern, NewsAPI, Finnhub, Reddit |
| **Database** | PostgreSQL 16 + pgvector (IVFFlat cosine similarity) |
| **ORM / Migrations** | SQLAlchemy 2.0 async, Alembic |
| **Auth** | JWT (python-jose), bcrypt (passlib) |
| **Realtime** | WebSockets (FastAPI native) |
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript |
| **UI** | TailwindCSS, Radix UI primitives, Lucide icons |
| **State** | Zustand (agent status, auth, signals) |
| **Infra** | Docker Compose, pgvector/pgvector:pg16 image |

---

## Project Structure

```
adversarial-swarm/
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── .env.example               ← copy to .env and fill in keys
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/001_initial.py
│   └── app/
│       ├── main.py                ← FastAPI app factory
│       ├── core/                  ← config, logging, security, deps
│       ├── database/              ← ORM models, CRUD, pgvector search
│       ├── agents/                ← LangGraph swarm (ear, bull, bear, arbiter)
│       ├── api/v1/                ← all FastAPI routers + WebSocket
│       └── services/              ← analysis orchestration, embeddings, WS
└── frontend/
    └── src/
        ├── app/                   ← Next.js App Router pages
        ├── components/            ← dashboard, journal, shared UI
        ├── lib/                   ← API client, WS hook, utilities
        ├── store/                 ← Zustand stores
        └── types/                 ← TypeScript interfaces
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### 1. Clone and configure

```bash
git clone <your-repo>
cd adversarial-swarm

cp backend/.env.example backend/.env
# Edit backend/.env — at minimum set OPENAI_API_KEY and APP_SECRET_KEY
```

### 2. Start the full stack

```bash
docker compose up --build
```

This starts:
- PostgreSQL 16 + pgvector on `:5432`
- FastAPI backend on `:8000` (auto-runs Alembic migrations)
- Next.js frontend on `:3000`

### 3. Create your account

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword"}'
```

### 4. Open the dashboard

Navigate to `http://localhost:3000` and sign in.

---

## Running Without Docker

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in your keys

# Start Postgres separately, then:
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 \
NEXT_PUBLIC_WS_URL=ws://localhost:8000 \
npm run dev
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/token` | Get JWT tokens |
| `GET`  | `/api/v1/auth/me` | Current user |
| `POST` | `/api/v1/analysis/run` | Trigger swarm for a ticker |
| `GET`  | `/api/v1/analysis/status/{id}` | Poll analysis status |
| `GET`  | `/api/v1/journal` | List Decision Journal |
| `GET`  | `/api/v1/journal/{id}` | Full decision detail |
| `GET`  | `/api/v1/signals` | Signal history |
| `GET`  | `/api/v1/assets` | Watchlist |
| `POST` | `/api/v1/assets` | Add to watchlist |
| `WS`   | `/ws/live?token=<jwt>` | Real-time agent event stream |

Interactive docs: `http://localhost:8000/docs`

---

## Agent Pipeline

Each analysis follows this sequential LangGraph flow:

```
START
  │
  ▼
[The Ear]           — Fetches news, market data, alt data via MCP
                      Embeds context, runs pgvector similarity search
  │
  ▼
[Bull Agent]        — Builds bullish thesis + confidence score (0–1)
                      Uses GPT-4o with structured JSON output
  │
  ▼ (reads Bull's thesis from shared state — A2A pattern)
[Bear Agent]        — Builds bearish counter-thesis + confidence score
  │
  ▼
[Arbiter Agent]     — Weighs both theses
                      Applies rule-based confidence thresholds
                      Emits BUY / HOLD / SELL
                      Persists full Decision to PostgreSQL
  │
  ▼
END   →  WebSocket event  →  Dashboard real-time update
```

---

## WebSocket Events

Connect to `ws://localhost:8000/ws/live?token=<access_token>`

```json
{ "type": "connected",       "message": "Connected to live feed" }
{ "type": "agent_status",    "ticker": "TSLA", "message": "Bull agent: thesis complete — confidence 0.72" }
{ "type": "final_signal",    "ticker": "TSLA", "data": { "signal": "BUY", "net_confidence": 0.31 } }
{ "type": "pipeline_error",  "ticker": "TSLA", "message": "Analysis failed: ..." }
```

---

## Configuration

Key settings in `backend/.env`:

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | Required — GPT-4o + embeddings | — |
| `OPENAI_MODEL` | LLM for agents | `gpt-4o` |
| `ARBITER_CONFIDENCE_THRESHOLD` | Min net confidence for non-HOLD | `0.35` |
| `ARBITER_DOMINANT_ADVANTAGE` | Min bull-bear gap for BUY/SELL | `0.20` |
| `MAX_NEWS_ARTICLES` | Articles per analysis | `15` |
| `NEWS_API_KEY` | NewsAPI.org key (optional — uses mock if absent) | — |
| `FINNHUB_API_KEY` | Finnhub market data (optional) | — |

---

## Extending the System

**Add a new data source (MCP):** Add a method to `app/agents/ear/mcp_client.py` and call it in `fetch_alternative_data()`.

**Change the LLM:** Update `OPENAI_MODEL` in `.env`. Any LangChain-compatible model works — swap `ChatOpenAI` for `ChatAnthropic`, `ChatGroq`, etc.

**Add a new agent:** Create a new node in `app/agents/`, register it in `app/agents/graph.py`, and add its output field to `SwarmState`.

**Adjust arbitration logic:** Edit `app/agents/arbiter/confidence.py` — all threshold rules live there.
