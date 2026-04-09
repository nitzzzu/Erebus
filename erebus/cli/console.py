"""Rich-powered console utilities for Erebus.

Provides a shared ``Console`` instance and helpers for rendering
panels, tables, spinners, markdown, and syntax-highlighted output.
"""

from __future__ import annotations

from typing import Any, Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

# Shared global console instance
console = Console()


def print_panel(
    content: str,
    *,
    title: str = "Erebus",
    subtitle: Optional[str] = None,
    border_style: str = "bright_cyan",
    expand: bool = True,
) -> None:
    """Render a Rich panel around *content*."""
    console.print(
        Panel(
            Markdown(content),
            title=f"[bold]{title}[/bold]",
            subtitle=subtitle,
            border_style=border_style,
            expand=expand,
            padding=(1, 2),
        )
    )


def print_markdown(text: str) -> None:
    """Render markdown text to the terminal."""
    console.print(Markdown(text))


def print_syntax(code: str, language: str = "python", *, theme: str = "monokai") -> None:
    """Render syntax-highlighted code."""
    console.print(
        Syntax(code, language, theme=theme, line_numbers=True, padding=1)
    )


def print_table(
    title: str,
    columns: list[str],
    rows: list[list[Any]],
    *,
    border_style: str = "bright_cyan",
) -> None:
    """Render a Rich table."""
    table = Table(title=title, border_style=border_style, show_lines=True)
    for col in columns:
        table.add_column(col, style="bold")
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    console.print(table)


def status_spinner(message: str = "Thinking…"):
    """Return a Rich ``Status`` spinner context manager."""
    return console.status(f"[bold cyan]{message}[/bold cyan]", spinner="dots")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_info(message: str) -> None:
    """Print an informational message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_welcome() -> None:
    """Print the Erebus welcome banner."""
    banner = Text()
    banner.append("  ╔═══════════════════════════════════════╗\n", style="bright_cyan")
    banner.append("  ║           ", style="bright_cyan")
    banner.append("⚡ EREBUS ⚡", style="bold bright_white")
    banner.append("              ║\n", style="bright_cyan")
    banner.append("  ║   ", style="bright_cyan")
    banner.append("Feature-Packed AI Agent", style="dim")
    banner.append("          ║\n", style="bright_cyan")
    banner.append("  ╚═══════════════════════════════════════╝", style="bright_cyan")
    console.print(banner)
    console.print()
