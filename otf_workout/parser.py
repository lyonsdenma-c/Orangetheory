"""Parse a daily Orangetheory workout Reddit post into structured exercise rows."""
from __future__ import annotations

import re
from dataclasses import dataclass

# A block/section header: a markdown heading, a bold line, or a short line
# ending in a colon (e.g. "**Treadmill Block 1**", "## Floor", "Rower:").
_HEADER_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?\*{0,2}(?P<text>[^*:#\n]{2,60}?)\*{0,2}\s*:?\s*$"
)
_BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(?P<text>.+?)\s*$")

# Splits "Exercise - detail" / "Exercise: detail" / "Exercise x12".
_EXERCISE_DETAIL_RE = re.compile(
    r"^(?P<exercise>.+?)\s*(?:[-–—:]\s*|(?=\bx\s*\d)\s*)(?P<detail>(?:x\s*)?\d.*)$",
    re.IGNORECASE,
)

DEFAULT_BLOCK = "General"


@dataclass
class ExerciseRow:
    block: str
    exercise: str
    detail: str = ""


def _looks_like_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return False
    if _BULLET_RE.match(stripped):
        return False
    if stripped.startswith("#"):
        return True
    if stripped.startswith("**") and stripped.endswith("**"):
        return True
    if stripped.endswith(":") and len(stripped.split()) <= 8:
        return True
    return False


def _split_exercise_detail(text: str) -> tuple[str, str]:
    match = _EXERCISE_DETAIL_RE.match(text)
    if match:
        exercise = match.group("exercise").strip(" -–—:")
        detail = match.group("detail").strip()
        if exercise:
            return exercise, detail
    return text.strip(), ""


def parse_workout_text(text: str) -> list[ExerciseRow]:
    """Turn the free-form body of a workout post into a list of exercise rows.

    Lines that look like section headers (markdown headings, bold text, or a
    short line ending in ``:``) set the current "block" (e.g. Treadmill,
    Rower, Floor). Bulleted or numbered lines under a block become exercise
    rows, split into an exercise name and its detail (reps/time/distance)
    where a separator is present.
    """
    rows: list[ExerciseRow] = []
    current_block = DEFAULT_BLOCK

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            exercise, detail = _split_exercise_detail(bullet_match.group("text"))
            if exercise:
                rows.append(ExerciseRow(block=current_block, exercise=exercise, detail=detail))
            continue

        if _looks_like_header(line):
            header_match = _HEADER_RE.match(line)
            current_block = (header_match.group("text").strip() if header_match else line).strip("* ")
            continue

    return rows
