# SQL Generator CLI Tool using Anthropic Claude

A Python CLI tool that converts natural language questions into SQL queries using the Anthropic Claude API, supporting MySQL, PostgreSQL, and SQLite dialects.

## Proposed Changes

### Project Structure

```
C:\Users\muthu\.gemini\antigravity\scratch\sql-generator\
├── sql_generator/
│   ├── __init__.py
│   ├── cli.py          # CLI entry point using argparse
│   ├── generator.py    # Core LLM interaction logic
│   └── prompts.py      # System prompts for SQL generation
├── requirements.txt     # anthropic, rich (for pretty output)
├── setup.py             # Package setup for `pip install -e .`
└── README.md            # Usage instructions
```

---

### Core Components

#### [NEW] [cli.py](file:///C:/Users/muthu/.gemini/antigravity/scratch/sql-generator/sql_generator/cli.py)
- CLI entry point using `argparse`
- Supports flags: `--dialect` (mysql/postgresql/sqlite, default: postgresql), `--explain` (add explanation of the query)
- Interactive mode: keeps prompting for queries until user types `exit`
- Single-shot mode: pass a query directly as an argument
- Uses `rich` library for beautifully formatted, syntax-highlighted SQL output in the terminal

#### [NEW] [generator.py](file:///C:/Users/muthu/.gemini/antigravity/scratch/sql-generator/sql_generator/generator.py)
- `SQLGenerator` class that wraps the Anthropic Python SDK
- Sends natural language to Claude with a carefully crafted system prompt
- Parses the response to extract clean SQL
- Handles API errors gracefully (invalid key, rate limits, etc.)
- Reads `ANTHROPIC_API_KEY` from environment variable

#### [NEW] [prompts.py](file:///C:/Users/muthu/.gemini/antigravity/scratch/sql-generator/sql_generator/prompts.py)
- System prompt template that instructs Claude to:
  - Generate valid SQL for the selected dialect
  - Return only the SQL query (no markdown fences)
  - Use best practices (proper JOINs, avoid SELECT *, etc.)
- Separate prompt variant for when `--explain` flag is used

#### [NEW] [requirements.txt](file:///C:/Users/muthu/.gemini/antigravity/scratch/sql-generator/requirements.txt)
- `anthropic` — Anthropic Python SDK
- `rich` — Terminal formatting and SQL syntax highlighting

#### [NEW] [setup.py](file:///C:/Users/muthu/.gemini/antigravity/scratch/sql-generator/setup.py)
- Allows `pip install -e .` for development
- Registers `sqlgen` as a console script entry point

---

## User Review Required

> [!IMPORTANT]
> **Anthropic API Key**: You will need a valid Anthropic API key. The tool will read it from the `ANTHROPIC_API_KEY` environment variable. You can set it with:
> ```bash
> set ANTHROPIC_API_KEY=sk-ant-...
> ```

## Usage Examples

```bash
# Single-shot mode
sqlgen "show all users who signed up in the last 30 days"

# Specify dialect
sqlgen --dialect mysql "get top 10 products by sales"

# With explanation
sqlgen --explain "find duplicate email addresses"

# Interactive mode
sqlgen -i
```

## Verification Plan

### Manual Verification
- Run the CLI with a sample natural language query and verify SQL output
- Test each dialect flag (mysql, postgresql, sqlite)
- Test interactive mode
- Test error handling (missing API key, invalid input)
