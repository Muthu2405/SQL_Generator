"""Core LLM interaction logic for the SQL generator.

This module wraps the Anthropic Python SDK in a thin :class:`SQLGenerator`
class. It builds the request, sends it to Claude, and parses the response
into a clean SQL string (and optional explanation when ``--explain`` is on).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

import anthropic

from .prompts import build_system_prompt


# Custom exception hierarchy so callers can catch generator errors specifically.
class SQLGeneratorError(RuntimeError):
    """Base error for the SQL generator."""


class MissingAPIKeyError(SQLGeneratorError):
    """Raised when ANTHROPIC_API_KEY is not set in the environment."""


class APIError(SQLGeneratorError):
    """Raised when the Anthropic API call fails."""


EXPLAIN_SEPARATOR = "---EXPLAIN---"


@dataclass
class GenerationResult:
    """The result of a single generation call."""

    sql: str
    explanation: Optional[str] = None


class SQLGenerator:
    """Generates SQL from natural language via the Anthropic Claude API.

    Parameters:
        model: Claude model identifier to use for generation.
        max_tokens: Maximum tokens to generate in the response.
        api_key: Optional explicit API key. Falls back to ``ANTHROPIC_API_KEY``.
    """

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        max_tokens: int = 1024,
        api_key: Optional[str] = None,
        ollama_host: Optional[str] = None,
    ) -> None:
        self.provider = provider.lower()
        self.max_tokens = max_tokens
        self.ollama_host = ollama_host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")

        if self.provider == "anthropic":
            self.model = model or self.DEFAULT_MODEL
            self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise MissingAPIKeyError(
                    "ANTHROPIC_API_KEY is not set. Export it as an environment variable "
                    "before running sqlgen."
                )
            self._client = anthropic.Anthropic(api_key=self.api_key)
        elif self.provider == "ollama":
            self.model = model or "qwen2.5-coder"
        else:
            raise ValueError(f"Unsupported provider: {provider!r}. Choose 'anthropic' or 'ollama'.")

    def generate(self, question: str, dialect: str, explain: bool = False) -> GenerationResult:
        """Generate a SQL query (and optional explanation) for ``question``.

        Args:
            question: Natural-language question to translate.
            dialect: One of ``postgresql``, ``mysql``, ``sqlite``.
            explain: If True, ask the model to append an explanation.

        Returns:
            A :class:`GenerationResult` with cleaned SQL and (if requested) an explanation.
        """
        system_prompt = build_system_prompt(dialect=dialect, explain=explain)

        if self.provider == "ollama":
            return self._generate_ollama(question, system_prompt, explain)

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": question}],
            )
        except anthropic.APIConnectionError as exc:
            raise APIError(f"Could not reach the Anthropic API: {exc}") from exc
        except anthropic.AuthenticationError as exc:
            raise APIError(
                "Authentication failed. Check that ANTHROPIC_API_KEY is valid."
            ) from exc
        except anthropic.RateLimitError as exc:
            raise APIError("Rate limited by the Anthropic API. Try again shortly.") from exc
        except anthropic.APIStatusError as exc:
            raise APIError(f"Anthropic API error: {exc}") from exc

        raw_text = _extract_text(response)
        if not raw_text.strip():
            raise APIError("Model returned an empty response.")

        if explain:
            sql, explanation = _split_sql_and_explanation(raw_text)
        else:
            sql = _strip_code_fences(raw_text)
            explanation = None

        return GenerationResult(sql=sql.strip(), explanation=explanation)

    def _generate_ollama(self, question: str, system_prompt: str, explain: bool) -> GenerationResult:
        """Connect to local Ollama server and run generation."""
        import httpx
        url = f"{self.ollama_host.rstrip('/')}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            "stream": False,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": 0.0,
            }
        }

        try:
            response = httpx.post(url, json=payload, timeout=60.0)
            
            if response.status_code != 200:
                try:
                    err_msg = response.json().get("error", response.text)
                except Exception:
                    err_msg = response.text
                raise APIError(f"Ollama error: {err_msg}")
                
            data = response.json()
            raw_text = data["message"]["content"].strip()
        except httpx.ConnectError as exc:
            raise APIError(
                f"Could not connect to Ollama server at {self.ollama_host}. "
                "Make sure Ollama is running (`ollama serve`)."
            ) from exc
        except APIError:
            # Re-raise custom APIError directly
            raise
        except Exception as exc:
            raise APIError(f"Ollama generation failed: {exc}") from exc

        if not raw_text:
            raise APIError("Ollama model returned an empty response.")

        if explain:
            sql, explanation = _split_sql_and_explanation(raw_text)
        else:
            sql = _strip_code_fences(raw_text)
            explanation = None

        return GenerationResult(sql=sql.strip(), explanation=explanation)


# --- response parsing helpers ------------------------------------------------


def _extract_text(response) -> str:
    """Concatenate the text fields from a Messages API response."""
    parts = []
    for block in response.content:
        # Only TextBlock carries a .text attribute; skip tool-use blocks etc.
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


_FENCE_RE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.MULTILINE)


def _strip_code_fences(text: str) -> str:
    """Remove a single leading/trailing markdown code fence if present."""
    stripped = text.strip()
    stripped = _FENCE_RE.sub("", stripped)
    return stripped.strip()


def _split_sql_and_explanation(text: str) -> tuple[str, Optional[str]]:
    """Split the model's response on the ---EXPLAIN--- separator."""
    cleaned = _strip_code_fences(text)
    if EXPLAIN_SEPARATOR in cleaned:
        sql, _, explanation = cleaned.partition(EXPLAIN_SEPARATOR)
        return sql.strip(), explanation.strip() or None
    # Fallback: model forgot the separator — treat the whole thing as SQL.
    return cleaned.strip(), None
