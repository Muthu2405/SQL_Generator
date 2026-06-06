# sqlgen — Project Context for Antigravity

This file provides the project context, architectural notes, run instructions, and coding standards for the **`sqlgen`** tool.

## What this project is

A Python CLI tool and web application called **`sqlgen`** that converts natural-language questions into SQL queries. It supports two AI providers:
1.  **Anthropic Claude API** (defaults to `claude-sonnet-4-6`, requires API key).
2.  **Local Ollama Server** (defaults to `qwen2.5-coder`, runs locally and is completely free).

It supports three SQL dialects: **PostgreSQL** (default), **MySQL**, and **SQLite**.

It is a small, utility-focused codebase consisting of:
- [prompts.py](file:///D:/SQL%20Generator/sql_generator/prompts.py): System prompts and dialect instructions.
- [generator.py](file:///D:/SQL%20Generator/sql_generator/generator.py): Wrapper around the Anthropic SDK and HTTP clients for Ollama. Features detailed JSON error reporting for Ollama.
- [cli.py](file:///D:/SQL%20Generator/sql_generator/cli.py): CLI interface supporting `--provider` and `--ollama-host` flags.
- [server.py](file:///D:/SQL%20Generator/sql_generator/server.py): FastAPI API backend server.
- [frontend/](file:///D:/SQL%20Generator/frontend): React frontend application scaffolded using Vite.

---

## Codebase Architecture & Key Decisions

- **Prompt Design** ([prompts.py](file:///D:/SQL%20Generator/sql_generator/prompts.py)):
  - `BASE_RULES` enforces "SQL only, no prose, no fences, explicit JOINs, no `SELECT *`".
  - `DIALECT_NOTES` is a per-dialect paragraph appended to the base rules.
  - In `--explain` mode, an `EXPLAIN_SUFFIX` asks the model to append a plain-English explanation after a literal `---EXPLAIN---` separator.
- **Generator** ([generator.py](file:///D:/SQL%20Generator/sql_generator/generator.py)):
  - Dynamically supports `anthropic` and `ollama` providers.
  - Returns a `GenerationResult(sql, explanation=None)` dataclass.
  - Connects to local Ollama server at `http://localhost:11434` (configurable) when running local mode.
  - Intercepts Ollama non-200 HTTP codes (like a 404 model not found error) and extracts the exact JSON error text to give clear advice (e.g. telling the user to pull the model first).
- **CLI** ([cli.py](file:///D:/SQL%20Generator/sql_generator/cli.py)):
  - Supports `--provider [anthropic|ollama]` and `--ollama-host` parameters.
  - Falls into interactive mode automatically when no positional `query` is given.
  - Renders SQL in a `rich` `Panel` with monokai syntax highlighting.
- **Backend API Server** ([server.py](file:///D:/SQL%20Generator/sql_generator/server.py)):
  - Exposes POST `/api/generate` to translate natural-language to SQL.
  - Exposes GET `/api/health` to verify server state.
  - Runs on port `8000` by default.
- **React Frontend** ([frontend/](file:///D:/SQL%20Generator/frontend)):
  - Built using Vite, React, Vanilla CSS, and `lucide-react` icons.
  - Features a dropdown in Settings to toggle the provider between Anthropic Claude and Local Ollama.
  - Saves your choice of provider, API key, and Ollama host URL to `localStorage`.
  - Shows custom troubleshooting messages conditional on the active AI provider.

---

## Build, Run & Environment Setup

### Environment Variables (for Anthropic)
- `ANTHROPIC_API_KEY`: Required to make calls to Claude (can also be entered in the Web Settings).

### Python Package & Server Installation
```bash
cd "D:/SQL Generator"
pip install -r requirements.txt
pip install -e .
```

### React Frontend Installation
```bash
cd "D:/SQL Generator/frontend"
npm install
```

### Running the Project

1. **Start the API Backend Server**:
   ```bash
   sqlgen-server
   ```
   *(Runs on http://localhost:8000)*

2. **Start the React Frontend Dev Server**:
   ```bash
   cd frontend
   npm run dev
   ```
   *(Runs on http://localhost:5173)*

3. **Running the CLI Tool**:
   *   Using Anthropic Claude:
       ```bash
       sqlgen "show all users who signed up in the last 30 days"
       ```
   *   Using Local Ollama (completely free, requires Ollama running):
       ```bash
       sqlgen --provider ollama "show all users who signed up in the last 30 days"
       ```
   *   Interactive mode:
       ```bash
       sqlgen -i
       sqlgen --provider ollama -i
       ```

---

## Coding Standards & Preferences

- **Code Formatting**: Use standard Python type hinting, clean comments, and structured docstrings. For frontend code, use clean JSX structure and modular CSS.
- **CSS Styles**: Use Vanilla CSS for custom web app layout design. Maintain glassmorphism, responsive styles, clean scrollbars, and glows as part of visual branding.
- **Console Output**: Use the `rich` library console for CLI, and `rich.syntax.Syntax` panels for SQL displays.

---

## Open Tasks & Roadmaps

- [ ] **Test Suite**: Add `pytest` test cases for `prompts.build_system_prompt`, response parsing in `generator.py`, and CLI command integration.
- [ ] **Schema Awareness**: Allow passing a DDL or connecting to a database to provide schema context to Claude/Ollama.
- [ ] **Token Streaming**: Stream SQL/explanations directly from Claude's/Ollama's response.
- [ ] **Query History Backend**: Persist query/REPL history to a database or local file instead of just `localStorage`.
