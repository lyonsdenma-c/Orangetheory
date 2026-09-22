from pathlib import Path

from otf_workout.parser import parse_workout_text
from otf_workout.table import to_markdown_table

FIXTURE = Path(__file__).parent / "fixtures" / "sample_workout.txt"


def test_parses_blocks_and_exercises():
    rows = parse_workout_text(FIXTURE.read_text())

    blocks = {row.block for row in rows}
    assert blocks == {"Treadmill Block 1 (10 min)", "Rower Block 1", "Floor Block 1"}
    assert len(rows) == 11


def test_splits_exercise_and_detail():
    rows = parse_workout_text(FIXTURE.read_text())
    pairs = [(row.exercise, row.detail) for row in rows]

    assert ("Base pace", "2 min") in pairs
    assert ("Row", "300m") in pairs
    assert ("Row", "250m") in pairs
    assert ("Bicep curl to shoulder press", "x12") in pairs
    assert ("Plank row", "x10 each arm") in pairs


def test_renders_markdown_table():
    rows = parse_workout_text(FIXTURE.read_text())
    table = to_markdown_table(rows)

    lines = table.splitlines()
    assert lines[0] == "| Block | Exercise | Detail |"
    assert lines[1] == "| --- | --- | --- |"
    assert len(lines) == len(rows) + 2
    assert "| Treadmill Block 1 (10 min) | Base pace | 2 min |" in table


def test_empty_text_yields_no_rows():
    assert parse_workout_text("") == []
