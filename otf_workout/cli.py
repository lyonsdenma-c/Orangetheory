"""CLI: fetch (or read) the daily OTF workout post and write it out as a table."""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Optional

import requests

from .parser import parse_workout_text
from .reddit_client import get_daily_workout_post
from .table import to_markdown_table


def _parse_date(value: Optional[str]) -> Optional[dt.date]:
    if not value:
        return None
    return dt.date.fromisoformat(value)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--subreddit", default="orangetheory", help="Subreddit to pull the workout post from."
    )
    parser.add_argument(
        "--date", default=None, help="Target date (YYYY-MM-DD) to match the workout post against; defaults to today (UTC)."
    )
    parser.add_argument(
        "--input-file",
        default=None,
        help="Parse a local text file (e.g. a pasted Reddit post) instead of fetching from Reddit. "
        "Useful when live network access to Reddit isn't available.",
    )
    parser.add_argument("--title", default=None, help="Override the title used in the output.")
    parser.add_argument(
        "--output", default=None, help="Write the Markdown table to this file instead of stdout."
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    if args.input_file:
        text = Path(args.input_file).read_text(encoding="utf-8")
        title = args.title or Path(args.input_file).stem
    else:
        try:
            post = get_daily_workout_post(args.subreddit, target_date=_parse_date(args.date))
        except requests.exceptions.RequestException as exc:
            print(f"Could not reach Reddit: {exc}", file=sys.stderr)
            return 1
        if post is None:
            print(f"No workout post found in r/{args.subreddit}.", file=sys.stderr)
            return 1
        text = post.get("selftext", "")
        title = args.title or post.get("title", "Daily Orangetheory Workout")

    rows = parse_workout_text(text)
    if not rows:
        print("No exercises could be parsed from the post body.", file=sys.stderr)
        return 1

    output = f"# {title}\n\n{to_markdown_table(rows)}\n"

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote {len(rows)} exercises to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
