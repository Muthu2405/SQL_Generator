# sqlgen — Natural Language to SQL (powered by Claude)

`sqlgen` turns plain-English questions into SQL queries using AI. It comes in
three flavors, all backed by the same core `sql_generator` package:

- **CLI** (`sqlgen`) — quick single-shot or interactive REPL in your terminal.
- **API server** (`sqlgen-server`) — FastAPI app exposing
  `POST /api/generate` and `GET /api/health` so other tools can use it.
- **Web UI** — a Vite + React frontend in `frontend/` that talks to the server,
  with a glassmorphic UI, history sidebar, and a settings panel for
  provider/model/API-key.

## AI providers

| Provider | Default model | Notes |
| --- | --- | --- |
| **Anthropic Claude** | `claude-sonnet-4-6` | Requires `ANTHROPIC_API_KEY`. |
| **Local Ollama** | `qwen2.5-coder` | Free + offline. Requires Ollama running locally. |

## SQL dialects

PostgreSQL (default), MySQL, and SQLite.

---

## Install

### 1. Python package (CLI + server)

```bash
cd "D:/SQL Generator"
pip install -r requirements.txt
pip install -e .
```

A local venv is already provisioned at `SQL_env/` — activate it instead of
installing globally if you prefer.

### 2. Frontend (web UI only)

```bash
cd "D:/SQL Generator/frontend"
npm install
```

---

## Set your API key (Anthropic only)

Windows `cmd` shown — adjust for your shell:

```bash
set ANTHROPIC_API_KEY=sk-ant-...
```

For Ollama, install [Ollama](https://ollama.com), pull a model
(`ollama pull qwen2.5-coder`), and leave the server running. Override the host
with `--ollama-host` or the settings panel if it's not on `localhost:11434`.

---

## Usage — CLI

### Single-shot

```bash
sqlgen "show all users who signed up in the last 30 days"
```

### Pick a dialect

```bash
sqlgen --dialect mysql "get top 10 products by sales"
```

### Include a plain-English explanation

```bash
sqlgen --explain "find duplicate email addresses"
```

### Use local Ollama (free, no API key)

```bash
sqlgen --provider ollama "show all users who signed up in the last 30 days"
```

### Interactive REPL

```bash
sqlgen -i
sqlgen --provider ollama -i
```

Type `exit` (or hit Ctrl-D) to quit.

### CLI flags

| Flag | Description |
| --- | --- |
| `query` | Natural-language question (positional). Omit for interactive mode. |
| `-i`, `--interactive` | Run as a REPL. Used automatically if no query is given. |
| `-d`, `--dialect` | `postgresql` (default), `mysql`, or `sqlite`. |
| `-e`, `--explain` | Append a short explanation of the generated query. |
| `--model` | Claude model id (default `claude-sonnet-4-6`). |
| `--provider` | `anthropic` (default) or `ollama`. |
| `--ollama-host` | Ollama server URL (default `http://localhost:11434`). |
| `--max-tokens` | Max tokens to generate (default `1024`). |
| `--version` | Print version and exit. |

### CLI exit codes

- `0` — success
- `1` — generation/API error
- `2` — missing `ANTHROPIC_API_KEY`

---

## Usage — API server (`sqlgen-server`)

```bash
# Start the server (port 8000 by default)
sqlgen-server
```

Env vars:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SQLGEN_HOST` | `127.0.0.1` | Bind address. |
| `SQLGEN_PORT` | `8000` | Bind port. |
| `SQLGEN_DEV` | `true` | Set to `false` to disable uvicorn auto-reload. |
| `ANTHROPIC_API_KEY` | _(unset)_ | Required when using the Anthropic provider. |

### `GET /api/health`

Returns whether the server is up and whether `ANTHROPIC_API_KEY` is
configured.

```bash
curl http://localhost:8000/api/health
# {"status":"healthy","api_key_configured":true}
```

### `POST /api/generate`

Translates a natural-language question into SQL.

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

**Request body** (`GenerateRequest`):

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `query` | `str` | _(required)_ | Natural-language question. |
| `dialect` | `str` | `postgresql` | `postgresql`, `mysql`, or `sqlite`. |
| `explain` | `bool` | `false` | Append a plain-English explanation. |
| `provider` | `str` | `anthropic` | `anthropic` or `ollama`. |
| `model` | `str?` | provider default | Override the model id. |
| `max_tokens` | `int?` | `1024` | Max tokens to generate. |
| `api_key` | `str?` | env `ANTHROPIC_API_KEY` | Per-request Anthropic key. |
| `ollama_host` | `str?` | env `OLLAMA_HOST` or `http://localhost:11434` | Per-request Ollama host. |

**Response**: `{"sql": "...", "explanation": null | "..."}`

Errors come back as `{"detail": "..."}` with appropriate HTTP status codes
(400 for bad input, 500 for internal failures).

---

## Usage — Web UI

1. **Start the API server** (in one terminal):

   ```bash
   sqlgen-server
   ```

2. **Start the React dev server** (in another terminal):

   ```bash
   cd "D:/SQL Generator/frontend"
   npm run dev
   ```

3. Open <http://localhost:5173>.

The UI features:

- Sidebar with the last 50 queries (persisted in `localStorage`).
- Glassmorphic cards with a dialect picker, explain toggle, and generate button.
- A **settings** panel (⚙️) for AI provider, model, max-tokens slider, backend
  URL, and the Anthropic API key / Ollama host URL.
- A live status badge polling `/api/health` every 8 seconds.
- One-click copy of the generated SQL.

To build the frontend for production:

```bash
cd "D:/SQL Generator/frontend"
npm run build      # outputs to frontend/dist/
npm run preview    # serves the built bundle locally
```

---

## Project layout

```
sql_generator/        # core Python package (shared by CLI and server)
├── __init__.py
├── cli.py            # argparse + rich-rendered CLI  →  sqlgen
├── generator.py      # Anthropic + Ollama wrapper, response parsing
├── prompts.py        # System prompt templates per dialect
└── server.py         # FastAPI app                   →  sqlgen-server

frontend/             # Vite + React 19 web UI
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── App.jsx       # single component, all logic
    ├── App.css
    ├── index.css
    └── main.jsx

requirements.txt
setup.py              # registers sqlgen + sqlgen-server console scripts
```

## Open follow-ups

- [ ] No tests yet — `pytest` suite for `prompts.build_system_prompt`,
      generator response parsing, and CLI smoke tests would be the next step.
- [ ] No schema-awareness yet — the model assumes a "reasonable schema". A
      future enhancement could let the user point at a DDL or DB connection.
- [ ] No streaming output — generation is request/response only.
- [ ] No persistence of past queries on the server — frontend history lives
      in `localStorage` only; nothing is shared across devices/browsers.
