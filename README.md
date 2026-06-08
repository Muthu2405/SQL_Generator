# sqlgen

Convert plain-English questions into SQL queries using AI.

Powered by **Anthropic Claude** (cloud) or **Ollama** (local/offline). Supports three interfaces — a CLI, a REST API server, and a React web UI — all backed by the same core `sql_generator` package.

**LIVE DEMO:** [https://sql-generator-bvxv.onrender.com](https://sql-generator-bvxv.onrender.com)

---

## Quick Start

### Local Development

```bash
# Terminal 1 — start the API server
sqlgen-server

# Terminal 2 — start the React dev server
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### Production (Deployed on Render)

Use the live demo at [https://sqlgen-frontend.onrender.com](https://sqlgen-frontend.onrender.com) — no setup required. The frontend is pre-configured to call the production backend at `https://sql-generator-bvxv.onrender.com`.

---

## Features

- **Natural language → SQL** using Claude or a local Ollama model
- **Three interfaces**: terminal CLI, FastAPI server, Vite + React web UI
- **Three SQL dialects**: PostgreSQL, MySQL, SQLite
- **Optional explanations**: ask for a plain-English breakdown of the generated query
- **Glassmorphic web UI** with query history, provider/model settings, and live server status
- **Zero lock-in**: swap providers per request via CLI flag, API field, or settings panel
- **Cloud-ready**: deployed on Render with environment-based backend routing

---

## AI Providers

| Provider | Default model | Requirement |
|---|---|---|
| Anthropic Claude | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` env var |
| Local Ollama | `qwen2.5-coder` | Ollama running on `localhost:11434` |

---

## Project Layout

```
sql_generator/          # Core Python package
├── __init__.py
├── cli.py              # CLI entry point  →  sqlgen
├── generator.py        # Anthropic + Ollama client, response parsing
├── prompts.py          # System prompt templates per SQL dialect
└── server.py           # FastAPI app      →  sqlgen-server

frontend/               # Vite + React 19 web UI
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── App.jsx
    ├── App.css
    ├── index.css
    └── main.jsx

requirements.txt
setup.py
```

---

## Install

### Prerequisites

- Python 3.9+
- Node.js (for the web UI only)

### 1. Clone and install the Python package

```bash
git clone <repo-url>
cd sqlgen

pip install -r requirements.txt
pip install -e .
```

This registers the `sqlgen` and `sqlgen-server` console scripts.

A local venv is provisioned at `SQL_env/` if you prefer to isolate dependencies:

```bash
SQL_env\Scripts\activate   # Windows
source SQL_env/bin/activate # macOS / Linux
pip install -r requirements.txt
pip install -e .
```

### 2. Install frontend dependencies (web UI only)

```bash
cd frontend
npm install
```

---

## Configuration

### Anthropic

Set your API key before running:

```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-...

# macOS / Linux
export ANTHROPIC_API_KEY=sk-ant-...
```

### Ollama

Install [Ollama](https://ollama.com), pull a model, and keep the server running:

```bash
ollama pull qwen2.5-coder
ollama serve
```

Override the host with `--ollama-host` (CLI) or the settings panel (web UI) if Ollama isn't on the default `localhost:11434`.

---

## CLI

### Single query

```bash
sqlgen "show all users who signed up in the last 30 days"
```

### Options

```bash
# Choose a SQL dialect
sqlgen --dialect mysql "get top 10 products by sales"

# Include a plain-English explanation
sqlgen --explain "find duplicate email addresses"

# Use local Ollama instead of Claude
sqlgen --provider ollama "show all orders placed today"

# Interactive REPL mode
sqlgen -i
sqlgen --provider ollama -i
```

Type `exit` or press Ctrl-D to quit the REPL.

### All flags

| Flag | Default | Description |
|---|---|---|
| `query` | — | Natural-language question (positional). Omit for interactive mode. |
| `-i`, `--interactive` | — | Start interactive REPL. |
| `-d`, `--dialect` | `postgresql` | `postgresql`, `mysql`, or `sqlite`. |
| `-e`, `--explain` | off | Append a plain-English explanation. |
| `--model` | provider default | Override model ID. |
| `--provider` | `anthropic` | `anthropic` or `ollama`. |
| `--ollama-host` | `http://localhost:11434` | Ollama server URL. |
| `--max-tokens` | `1024` | Max tokens to generate. |
| `--version` | — | Print version and exit. |

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Generation or API error |
| `2` | Missing `ANTHROPIC_API_KEY` |

---

## API Server

### Start locally

```bash
sqlgen-server
```

Defaults to `http://127.0.0.1:8000`.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SQLGEN_HOST` | `127.0.0.1` | Bind address |
| `SQLGEN_PORT` | `8000` | Bind port |
| `SQLGEN_DEV` | `true` | Set to `false` to disable auto-reload |
| `ANTHROPIC_API_KEY` | — | Required for the Anthropic provider |

### `GET /api/health`

```bash
curl http://localhost:8000/api/health
# {"status":"healthy","api_key_configured":true}
```

### `POST /api/generate`

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "show all users who signed up in the last 30 days",
    "dialect": "postgresql",
    "explain": false,
    "provider": "anthropic",
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "api_key": "sk-ant-..."
  }'
```

**Request body:**

| Field | Type | Default | Notes |
|---|---|---|---|
| `query` | `str` | required | Natural-language question |
| `dialect` | `str` | `postgresql` | `postgresql`, `mysql`, or `sqlite` |
| `explain` | `bool` | `false` | Include a plain-English explanation |
| `provider` | `str` | `anthropic` | `anthropic` or `ollama` |
| `model` | `str` | provider default | Override model ID |
| `max_tokens` | `int` | `1024` | Max tokens to generate |
| `api_key` | `str` | env `ANTHROPIC_API_KEY` | Per-request Anthropic key |
| `ollama_host` | `str` | `http://localhost:11434` | Per-request Ollama host |

**Response:** `{"sql": "...", "explanation": null | "..."}`

Errors return `{"detail": "..."}` with HTTP 400 (bad input) or 500 (server error).

---

## Web UI

### Local development

```bash
# Terminal 1 — start the API server
sqlgen-server

# Terminal 2 — start the React dev server
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### Local with production backend

To test the frontend against the production Render backend:

```bash
cd frontend
VITE_BACKEND_URL=https://sql-generator-bvxv.onrender.com npm run dev
```

### Production build

```bash
cd frontend
npm run build     # outputs to frontend/dist/
npm run preview   # serve the built bundle locally
```

### UI features

- Query history sidebar (last 50 queries, persisted in `localStorage`)
- Dialect picker, explain toggle, and generate button
- Settings panel (⚙️) — provider, model, max-tokens, backend URL, API key / Ollama host
- Live server status badge (polls `/api/health` every 8 seconds)
- One-click SQL copy

---

## Deployment

### Backend (API Server on Render)

1. Create a new Web Service on Render
2. Connect your GitHub repo
3. Set the **start command**:
   ```
   uvicorn sql_generator.server:app --host 0.0.0.0 --port $PORT
   ```
4. Add environment variable:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
5. Deploy

Your backend will be available at `https://<service-name>.onrender.com`.

### Frontend (Web UI on Render)

1. Create a new Static Site on Render
2. Connect your GitHub repo and set the **build command**:
   ```
   cd frontend && npm install && npm run build
   ```
3. Set the **publish directory** to `frontend/dist`
4. Add environment variable for backend URL:
   ```
   VITE_BACKEND_URL=https://sql-generator-bvxv.onrender.com
   ```
5. Deploy

Your frontend will be available at `https://<service-name>.onrender.com` and will route all API calls to the backend URL.

### Environment variable: `VITE_BACKEND_URL`

The frontend uses `import.meta.env.VITE_BACKEND_URL` to determine the API backend. At build time, this is replaced with the environment variable value.

- **Production (Render)**: `VITE_BACKEND_URL=https://sql-generator-bvxv.onrender.com`
- **Local dev**: Create `frontend/.env.local` with `VITE_BACKEND_URL=http://localhost:8000`
- **Default fallback**: If unset, the frontend defaults to `http://localhost:8000`

---

## Known Limitations

- No test suite yet — `pytest` coverage for `prompts`, generator parsing, and CLI smoke tests is a planned next step.
- No schema awareness — the model assumes a generic schema. Pointing at a DDL file or live DB connection is a future enhancement.
- No streaming — generation is request/response only; no token-by-token output.
- No server-side query history — the frontend history is `localStorage` only and not shared across devices or browsers.

---

## Links

- **Live Demo**: [https://sqlgen-frontend.onrender.com](https://sqlgen-frontend.onrender.com)
- **Backend API**: [https://sql-generator-bvxv.onrender.com](https://sql-generator-bvxv.onrender.com)
- **GitHub**: [your-repo-url]