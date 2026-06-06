"""System prompt templates for the SQL generator.

The public entry point is :func:`build_system_prompt`, which composes a base
set of rules, a dialect-specific paragraph, and (optionally) an "explain
mode" suffix that asks the model to append a plain-English explanation after
a deterministic ``---EXPLAIN---`` separator.
"""

from __future__ import annotations

from typing import Dict


BASE_RULES = """\
You are an expert SQL generator.
Given a natural-language question, produce a single, executable SQL query that answers it.

Rules:
- Return ONLY the SQL query. No prose, no explanation, no markdown fences.
- Use proper, explicit JOIN syntax (never implicit joins in the WHERE clause).
- Prefer explicit column lists over SELECT *.
- Use parameterizable values where the question is ambiguous.
- Assume a reasonable schema; if the question is ambiguous, choose the most natural interpretation and stick with it.
- Do not include comments, database-creation statements, or DDL unless the question explicitly asks for them.
- If the question cannot be answered with SQL alone, still return the closest valid query.
"""


DIALECT_NOTES: Dict[str, str] = {
    "postgresql": (
        "Target dialect: PostgreSQL.\n"
        "- Use double quotes for identifiers when needed.\n"
        "- Use date/time functions like NOW(), INTERVAL, DATE_TRUNC.\n"
        "- Use window functions (ROW_NUMBER, RANK) and CTEs (WITH ...) freely.\n"
        "- Prefer SERIAL or GENERATED AS IDENTITY for surrogate keys if needed."
    ),
    "mysql": (
        "Target dialect: MySQL 8.x.\n"
        "- Use backticks for identifiers when needed.\n"
        "- Use date/time functions like CURDATE(), DATE_ADD, DATE_FORMAT.\n"
        "- Use window functions and CTEs (WITH ...) freely in 8.x.\n"
        "- Prefer AUTO_INCREMENT for surrogate keys if needed."
    ),
    "sqlite": (
        "Target dialect: SQLite 3.\n"
        "- Use double quotes for identifiers when needed.\n"
        "- Use date/time functions like DATE('now'), julianday, strftime.\n"
        "- Use CTEs (WITH ...) freely.\n"
        "- SQLite has limited ALTER TABLE support; emit portable statements.\n"
        "- INTEGER PRIMARY KEY auto-increments in SQLite if needed."
    ),
}


EXPLAIN_SUFFIX = (
    "\n--explain mode--\n"
    "After the SQL query, on a new line, add a brief plain-English explanation "
    "(2-4 sentences) of how the query works. Separate the SQL and the explanation "
    "with a single line containing exactly: ---EXPLAIN---"
)


SUPPORTED_DIALECTS = tuple(DIALECT_NOTES.keys())


def build_system_prompt(dialect: str, explain: bool = False) -> str:
    """Compose the system prompt for the given dialect.

    Args:
        dialect: One of ``SUPPORTED_DIALECTS``.
        explain: If True, append the explain-mode suffix.

    Raises:
        ValueError: If ``dialect`` is not supported.
    """
    key = dialect.lower()
    note = DIALECT_NOTES.get(key)
    if note is None:
        raise ValueError(
            f"Unsupported dialect: {dialect!r}. Choose from {SUPPORTED_DIALECTS}."
        )
    parts = [BASE_RULES, note]
    if explain:
        parts.append(EXPLAIN_SUFFIX)
    return "\n\n".join(parts)
