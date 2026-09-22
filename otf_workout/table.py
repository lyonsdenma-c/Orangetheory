"""Render parsed exercise rows as a Markdown table."""
from __future__ import annotations

from .parser import ExerciseRow


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def to_markdown_table(rows: list[ExerciseRow]) -> str:
    """Render exercise rows as a GitHub-flavored Markdown table."""
    header = "| Block | Exercise | Detail |"
    separator = "| --- | --- | --- |"
    lines = [header, separator]
    for row in rows:
        lines.append(
            f"| {_escape_cell(row.block)} | {_escape_cell(row.exercise)} | {_escape_cell(row.detail)} |"
        )
    return "\n".join(lines)
