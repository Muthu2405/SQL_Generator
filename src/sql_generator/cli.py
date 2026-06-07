"""CLI entry point for the SQL generator.

Run as ``sqlgen`` (registered via ``setup.py``) or ``python -m sql_generator.cli``.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt

from . import __version__
from .generator import (
    APIError,
    GenerationResult,
    MissingAPIKeyError,
    SQLGenerator,
    SQLGeneratorError,
)
from .prompts import SUPPORTED_DIALECTS


console = Console(stderr=False)
err_console = Console(stderr=True)


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        prog="sqlgen",
        description="Convert natural-language questions into SQL using Claude.",
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Natural-language question to translate. Omit for interactive mode.",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive REPL mode (prompts repeatedly until 'exit').",
    )
    parser.add_argument(
        "-d", "--dialect",
        choices=SUPPORTED_DIALECTS,
        default="postgresql",
        help="Target SQL dialect (default: postgresql).",
    )
    parser.add_argument(
        "-e", "--explain",
        action="store_true",
        help="Ask the model to also explain the generated query.",
    )
    parser.add_argument(
        "--model",
        default=SQLGenerator.DEFAULT_MODEL,
        help=f"Model identifier to use (default: {SQLGenerator.DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "ollama"],
        default="anthropic",
        help="LLM provider to use (default: anthropic).",
    )
    parser.add_argument(
        "--ollama-host",
        default="http://localhost:11434",
        help="Ollama host URL (default: http://localhost:11434).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens to generate (default: 1024).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"sqlgen {__version__}",
    )
    return parser


def render_result(result: GenerationResult, dialect: str) -> None:
    """Pretty-print a :class:`GenerationResult` using rich."""
    syntax = Syntax(result.sql, "sql", theme="monokai", word_wrap=True)
    title = f"Generated SQL ({dialect})"
    console.print(Panel(syntax, title=title, border_style="cyan", expand=False))
    if result.explanation:
        console.print()
        console.print(Panel(result.explanation, title="Explanation", border_style="green"))


def run_single(generator: SQLGenerator, question: str, dialect: str, explain: bool) -> int:
    """Run a single question and print the result. Returns process exit code."""
    try:
        result = generator.generate(question, dialect=dialect, explain=explain)
    except MissingAPIKeyError as exc:
        err_console.print(f"[bold red]Missing API key:[/bold red] {exc}")
        return 2
    except APIError as exc:
        err_console.print(f"[bold red]API error:[/bold red] {exc}")
        return 1
    except SQLGeneratorError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        return 1

    render_result(result, dialect)
    return 0


def run_interactive(generator: SQLGenerator, dialect: str, explain: bool) -> int:
    """Run an interactive REPL. Returns process exit code."""
    console.print(
        f"[bold cyan]sqlgen[/bold cyan] interactive mode "
        f"(provider=[green]{generator.provider}[/green], model=[green]{generator.model}[/green], dialect=[green]{dialect}[/green], explain=[green]{explain}[/green]). "
        "Type 'exit' or Ctrl-D to quit."
    )
    while True:
        try:
            question = Prompt.ask("[bold blue]\\[sqlgen][/bold blue]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            return 0
        question = question.strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            console.print("[dim]Goodbye.[/dim]")
            return 0
        exit_code = run_single(generator, question, dialect=dialect, explain=explain)
        if exit_code != 0:
            # Keep going on transient errors so the REPL stays useful.
            err_console.print("[dim](continuing — type 'exit' to quit)[/dim]")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    interactive = args.interactive or args.query is None
    if not interactive and not args.query.strip():
        parser.error("query must not be empty")

    # Override default model if provider is Ollama
    model = args.model
    if args.provider == "ollama" and model == SQLGenerator.DEFAULT_MODEL:
        model = "qwen2.5-coder"

    try:
        generator = SQLGenerator(
            provider=args.provider,
            model=model,
            max_tokens=args.max_tokens,
            ollama_host=args.ollama_host,
        )
    except MissingAPIKeyError as exc:
        err_console.print(f"[bold red]Missing API key:[/bold red] {exc}")
        return 2

    if interactive:
        return run_interactive(generator, dialect=args.dialect, explain=args.explain)
    return run_single(generator, args.query, dialect=args.dialect, explain=args.explain)


if __name__ == "__main__":
    sys.exit(main())
