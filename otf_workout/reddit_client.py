"""Read-only client for pulling posts from a subreddit's public JSON API.

No Reddit API credentials are required: this uses the public
``https://www.reddit.com/r/<sub>/<sort>.json`` endpoints that back the
website itself. Reddit rate-limits requests without a descriptive
User-Agent, so one is always sent.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Iterable, Optional, Sequence

import requests

DEFAULT_USER_AGENT = "python:otf-workout-table:1.0 (by /u/otf-workout-bot)"
DEFAULT_TITLE_KEYWORDS = ("workout",)
DEFAULT_FLAIR_KEYWORDS = ("workout",)


def fetch_posts(
    subreddit: str,
    *,
    sort: str = "new",
    limit: int = 50,
    query: Optional[str] = None,
    session: Optional[requests.Session] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: float = 15.0,
) -> list[dict[str, Any]]:
    """Return raw post data dicts from a subreddit listing or search."""
    session = session or requests.Session()
    base = f"https://www.reddit.com/r/{subreddit}"
    if query:
        url = f"{base}/search.json"
        params = {"q": query, "restrict_sr": "on", "sort": sort, "limit": limit}
    else:
        url = f"{base}/{sort}.json"
        params = {"limit": limit}

    resp = session.get(url, params=params, headers={"User-Agent": user_agent}, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return [child["data"] for child in data["data"]["children"]]


def _post_date(post: dict[str, Any]) -> dt.date:
    return dt.datetime.fromtimestamp(post["created_utc"], tz=dt.timezone.utc).date()


def find_daily_workout_post(
    posts: Iterable[dict[str, Any]],
    *,
    target_date: Optional[dt.date] = None,
    title_keywords: Sequence[str] = DEFAULT_TITLE_KEYWORDS,
    flair_keywords: Sequence[str] = DEFAULT_FLAIR_KEYWORDS,
) -> Optional[dict[str, Any]]:
    """Pick the post that best matches "today's workout" out of a listing.

    Prefers a post created on ``target_date`` (UTC) whose title or flair
    mentions a workout keyword; falls back to the most recent matching post
    if nothing was posted on that exact date yet.
    """
    target_date = target_date or dt.date.today()
    candidates: list[tuple[dt.date, dict[str, Any]]] = []

    for post in posts:
        title = (post.get("title") or "").lower()
        flair = (post.get("link_flair_text") or "").lower()
        matches = any(kw in title for kw in title_keywords) or any(kw in flair for kw in flair_keywords)
        if not matches:
            continue
        candidates.append((_post_date(post), post))

    same_day = [post for created, post in candidates if created == target_date]
    if same_day:
        return same_day[0]

    if candidates:
        candidates.sort(key=lambda cp: cp[0], reverse=True)
        return candidates[0][1]

    return None


def get_daily_workout_post(
    subreddit: str = "orangetheory",
    *,
    target_date: Optional[dt.date] = None,
    session: Optional[requests.Session] = None,
) -> Optional[dict[str, Any]]:
    """Fetch and return the raw post dict for today's daily workout thread."""
    session = session or requests.Session()

    posts = fetch_posts(subreddit, sort="new", limit=50, session=session)
    post = find_daily_workout_post(posts, target_date=target_date)
    if post is not None:
        return post

    # New listing may have scrolled past it; fall back to a search.
    posts = fetch_posts(subreddit, query="workout", sort="new", limit=25, session=session)
    return find_daily_workout_post(posts, target_date=target_date)
