# sqlgen — Project Context for Claude

## What this project is

A **multi-surface Python tool called `sqlgen`** that converts natural-language
questions into SQL queries. It exposes three interfaces sharing one core:

1. A **CLI** (`sqlgen` command) for terminal use.
2. A **FastAPI server** (`sqlgen-server`) that powers a web UI.
3. A **React + Vite frontend** in `frontend/` that talks to the server.

It supports **two AI providers**:
- **Anthropic Claude** (default, `claude-sonnet-4-6`, requires `ANTHROPIC_API_KEY`).
- **Local Ollama** (default model `qwen2.5-coder`, hits `http://localhost:11434`, free/local).

It supports **three SQL dialects**: **PostgreSQL** (default), **MySQL**, and **SQLite**.

The core package is small and deliberately focused:
- `prompts.py` — system prompt templates
- `generator.py` — Anthropic SDK + Ollama HTTP wrapper, response parsing
- `cli.py` — argparse CLI with `rich` rendering
- `server.py` — FastAPI app exposing `/api/generate` and `/api/health`

## Why it exists

Built as a personal/internal tool so the author (Muthu) can quickly draft SQL
queries from natural language — in the terminal (CLI) or with a richer UX
(React UI) — without opening a chat interface.

## Status

- ✅ `prompts.py` — system prompt templates, dialect notes, explain-mode suffix
- ✅ `__init__.py` — exposes `__version__ = "0.1.0"`
- ✅ `generator.py` — `SQLGenerator` class with `anthropic` and `ollama` providers,
      response parsing, error hierarchy
- ✅ `cli.py` — argparse CLI, single-shot + interactive REPL, `rich` rendering
- ✅ `server.py` — FastAPI app, CORS, `/api/generate` + `/api/health`
- ✅ `frontend/` — Vite + React 19 + `lucide-react` + vanilla CSS (glassmorphism)
- ✅ `requirements.txt` — `anthropic`, `rich`, `fastapi`, `uvicorn`, `pydantic`
- ✅ `setup.py` — registers `sqlgen` and `sqlgen-server` console scripts
- ✅ `README.md` — install + usage docs (CLI only — see note below)
- ✅ `SQL_env/` — local Windows venv, already provisioned
- ⚠️  `AGY.md` and `AVG.md` — **near-duplicate context files** (Antigravity
      format). `AGY.md` adds one line about Ollama JSON-error parsing; the rest
      is duplicated from `CLAUDE.md`. Consider consolidating to one source of truth.

## Architecture / key decisions

### Core package — `sql_generator/`

- **Prompt design** lives in [`prompts.py`](sql_generator/prompts.py):
  - `BASE_RULES` enforces "SQL only, no prose, no fences, explicit JOINs,
    no `SELECT *`".
  - `DIALECT_NOTES` is a per-dialect paragraph appended to the base rules.
  - In `--explain` mode, an `EXPLAIN_SUFFIX` asks the model to append
    plain-English explanation after a literal `---EXPLAIN---` separator
    (used by the parser to split SQL from explanation deterministically).
  - `build_system_prompt(dialect, explain)` is the single public entry point;
    raises `ValueError` for unsupported dialects.

- **Generator** ([`generator.py`](sql_generator/generator.py)):
  - Constructor: `SQLGenerator(provider, model, max_tokens, api_key, ollama_host)`.
    `provider` is `"anthropic"` (default) or `"ollama"`.
  - **Anthropic path**: reads `ANTHROPIC_API_KEY` from env (or accepts explicit
    `api_key`); raises `MissingAPIKeyError` (exit code 2) and `APIError` (exit
    code 1) for SDK failures (`APIConnectionError`, `AuthenticationError`,
    `RateLimitError`, `APIStatusError`).
  - **Ollama path**: `httpx` `POST {host}/api/chat` with the system + user
    messages. Non-200 responses are parsed for the JSON `error` field and
    surfaced via `APIError` (so e.g. "model not found" gives clear advice).
  - `generate(question, dialect, explain)` returns
    `GenerationResult(sql, explanation=None)`.
  - Strips markdown code fences defensively; falls back gracefully if the
    model forgets the `---EXPLAIN---` separator.

- **CLI** ([`cli.py`](sql_generator/cli.py)):
  - `sqlgen` console script. Falls into interactive mode automatically when
    no positional `query` is given.
  - Flags: `-i`/`--interactive`, `-d`/`--dialect`, `-e`/`--explain`, `--model`,
    `--provider [anthropic|ollama]`, `--ollama-host`, `--max-tokens`, `--version`.
  - Renders SQL in a `rich` `Panel` with monokai syntax highlighting.
  - Interactive mode keeps the REPL alive on transient errors so one bad
    generation doesn't kill the session.
  - Exit codes: 0 success, 1 API/generator error, 2 missing API key.
  - Default Claude model: `claude-sonnet-4-6`, `max_tokens=1024`.
  - Default Ollama model: `qwen2.5-coder`.

- **API server** ([`server.py`](sql_generator/server.py)):
  - `sqlgen-server` console script. FastAPI app, runs on `127.0.0.1:8000`
    by default (override via `SQLGEN_HOST`, `SQLGEN_PORT`; `SQLGEN_DEV=true`
    enables uvicorn reload).
  - `POST /api/generate` — body: `GenerateRequest(query, dialect, explain,
    model, max_tokens, api_key, provider, ollama_host)`. Returns
    `{sql, explanation}`.
  - `GET /api/health` — returns `{status: "healthy", api_key_configured: bool}`
    by checking `ANTHROPIC_API_KEY` env.
  - CORS: `allow_origins=["*"]` (fine for local dev, tighten for prod).

### Frontend — `frontend/`

- **Stack**: Vite 8, React 19, `lucide-react` for icons, **vanilla CSS**
  (glassmorphism, glows, custom scrollbars — no Tailwind/CSS-in-JS).
- **Single component** in `src/App.jsx` with:
  - **Sidebar** of recent queries (capped at 50, persisted in `localStorage`).
  - **Glass-card input** with auto-resizing textarea, dialect tabs
    (PostgreSQL/MySQL/SQLite), explain toggle, settings gear, generate button.
  - **Settings panel** (collapsible): AI provider, model, max-tokens slider,
    backend URL, Anthropic API key / Ollama host URL.
  - **Live status badge** polling `/api/health` every 8s; auto-refresh button.
  - **SQL syntax highlighter** implemented client-side in JSX (regex-based,
    strings/numbers/keywords/comments — escapes HTML to avoid XSS).
  - **Output cards**: generated SQL + optional explanation, copy-to-clipboard
    with toast confirmation.
  - **Troubleshooting hint** when backend is reachable but
    `ANTHROPIC_API_KEY` is missing.
- **Persistence** (localStorage): `sqlgen_api_key`, `sqlgen_provider`,
  `sqlgen_ollama_host`, `sqlgen_history` (capped 50).
- **Default backend URL**: `http://localhost:8000`.
- **Frontend dev port**: `http://localhost:5173` (Vite default).

## User preferences (Muthu)

- Prefers working in **`D:\SQL Generator`** on Windows.
- Bash shell semantics inside this environment (use `/dev/null`, forward slashes).
- Likes `rich`-style pretty terminal output and clean, well-commented code.
- Likes the glassmorphism + glow visual branding on the React side.

## Build / run

### Python (CLI + server)

```bash
cd "D:/SQL Generator"
pip install -r requirements.txt
pip install -e .
set ANTHROPIC_API_KEY=sk-ant-...   # Windows cmd; adjust for your shell
```

A local venv is already provisioned at `SQL_env/` — activate it instead of
installing globally if you prefer.

### CLI

```bash
# Single-shot
sqlgen "show all users who signed up in the last 30 days"

# Different dialect
sqlgen --dialect mysql "get top 10 products by sales"

# With explanation
sqlgen --explain "find duplicate email addresses"

# Use local Ollama (free, requires Ollama running locally)
sqlgen --provider ollama "show all users who signed up in the last 30 days"

# Interactive REPL
sqlgen -i
sqlgen --provider ollama -i
```

### API server + frontend (web UI)

```bash
# 1. Start the backend (port 8000)
sqlgen-server

# 2. In a second terminal, start the React dev server (port 5173)
cd "D:/SQL Generator/frontend"
npm run dev
```

Then open <http://localhost:5173>. The React UI hits the backend at
`http://localhost:8000` (configurable in the settings panel).

## Repo layout

```
D:\SQL Generator\
├── sql_generator/             # core Python package
│   ├── __init__.py
│   ├── cli.py                 # sqlgen console script
│   ├── generator.py           # Anthropic + Ollama wrapper
│   ├── prompts.py             # system prompts per dialect
│   └── server.py              # FastAPI app → sqlgen-server
├── frontend/                  # Vite + React 19 UI
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx            # single component, all logic
│       ├── App.css
│       ├── index.css
│       └── main.jsx
├── requirements.txt
├── setup.py
├── README.md                  # CLI-only usage docs (web UI not yet documented here)
├── implementation_plan.md     # original Gemini-style planning doc
├── CLAUDE.md                  # this file
├── AGY.md                     # Antigravity context (duplicates much of CLAUDE.md)
├── AVG.md                     # near-duplicate of AGY.md
├── SQL_env/                   # local Windows venv (already provisioned)
└── sqlgen.egg-info/           # editable-install metadata
```

## Known issues / things to be aware of

- **`AGY.md` and `AVG.md` duplicate context** that already lives in `CLAUDE.md`.
  The two Antigravity files are themselves near-duplicates of each other.
  Pick one source of truth when starting new work.
- **`httpx` is imported by `generator._generate_ollama` but is not listed in
  `requirements.txt`**. It's pulled in transitively via the `anthropic` SDK
  (visible in `SQL_env\Lib\site-packages\httpx`), so the import works — but
  this is a latent fragility if `anthropic`'s deps ever change.
- **`README.md` only documents the CLI.** The web UI (`sqlgen-server` +
  frontend) is documented in `AGY.md`/`AVG.md` and in this file, but not in
  the public README.
- **Frontend model dropdown** in `App.jsx` lists `claude-opus-2-6` and
  `claude-haiku-3` as options. These are **not valid Anthropic model ids**
  (the real Claude 4 family is Opus 4.7/4.8, Sonnet 4.6, Haiku 4.5). The
  default `claude-sonnet-4-6` is correct. Selecting the fake options will
  cause API errors.
- **CORS is wide-open** (`allow_origins=["*"]`) in `server.py` — fine for
  local dev, worth tightening before any deployment.
- **`implementation_plan.md` is the original planning doc** (Gemini style,
  references `~/.gemini/antigravity/scratch/...`). It's now historical but
  has not been deleted.

## Open follow-ups (not yet done)

- [ ] No tests yet — `pytest` suite for `prompts.build_system_prompt`,
      generator response parsing, and CLI smoke tests would be the next step.
- [ ] No schema-awareness yet — the model assumes a "reasonable schema". A
      future enhancement could let the user point at a DDL or DB connection.
- [ ] No streaming output — generation is request/response only.
- [ ] No persistence of past queries on the server — frontend history lives
      in `localStorage` only; nothing is shared across devices/browsers.
- [ ] Consolidate `CLAUDE.md` / `AGY.md` / `AVG.md` into one source of truth.
- [ ] Add `httpx` to `requirements.txt` (currently transitive-only).
- [ ] Replace the invalid model ids in the frontend dropdown
      (`claude-opus-2-6`, `claude-haiku-3`).
- [ ] Document the web UI flow in `README.md`.
