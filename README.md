# Orangetheory

Pulls the daily workout thread from [r/orangetheory](https://www.reddit.com/r/orangetheory/)
and renders its exercises as a Markdown table.

## How it works

- `otf_workout/reddit_client.py` — fetches posts from the subreddit's public
  `.json` listing/search endpoints (no Reddit API credentials needed) and
  picks the post that best matches "today's workout" by title/flair and
  post date.
- `otf_workout/parser.py` — turns the post body into exercise rows: section
  headers (e.g. **Treadmill**, **Rower**, **Floor**) become the `Block`
  column, and bulleted/numbered lines become `Exercise` / `Detail` pairs.
- `otf_workout/table.py` — renders the rows as a GitHub-flavored Markdown
  table.
- `otf_workout/cli.py` — command-line entry point that ties it together.

## Usage

```bash
pip install -r requirements.txt

# Fetch today's workout from r/orangetheory and print the table
python -m otf_workout.cli

# Save it to a file instead
python -m otf_workout.cli --output workout_table.md

# Target a specific date (UTC) or subreddit
python -m otf_workout.cli --date 2026-09-22 --subreddit orangetheory

# Parse a post you already have saved locally (e.g. pasted from Reddit) —
# useful anywhere live Reddit access isn't available
python -m otf_workout.cli --input-file post.txt --title "Today's Workout"
```

## Development note

This was built and unit-tested in a sandboxed environment whose network
policy blocks outbound requests to Reddit (and most other external sites),
so the Reddit-fetching path could not be exercised live here. The parser
and table renderer are covered by `tests/test_parser.py` against a
realistic sample workout post (`tests/fixtures/sample_workout.txt`). Run it
against the real subreddit from an environment with normal internet access:

```bash
pip install -r requirements.txt
python -m otf_workout.cli
```

If the post format on r/orangetheory doesn't match cleanly (formatting
varies by author), tweak the header/bullet regexes in
`otf_workout/parser.py` or fall back to `--input-file` with the pasted
post text.

## Tests

```bash
pip install -r requirements.txt pytest
python -m pytest
```
