"""Client for pulling posts from a subreddit via Reddit's API.

Reddit's old unauthenticated ``https://www.reddit.com/r/<sub>/<sort>.json``
endpoints now return ``403 Blocked`` for most automated/cloud traffic
(confirmed from a GitHub Actions runner). The supported path is OAuth
"application only" auth, which needs a free script-type app registered at
https://www.reddit.com/prefs/apps (no Reddit login/password required to use
it, just the app's client id/secret).

Set ``REDDIT_CLIENT_ID`` and ``REDDIT_CLIENT_SECRET`` env vars to use OAuth.
If they're unset, this falls back to the public ``.json`` endpoints, which
may still work from some networks but are not reliable.
"""
from __future__ import annotations

import datetime as dt
import os
from typing import Any, Iterable, Optional, Sequence

import requests

DEFAULT_USER_AGENT = "python:otf-workout-table:1.0 (by /u/otf-workout-bot)"
DEFAULT_TITLE_KEYWORDS = ("workout",)
DEFAULT_FLAIR_KEYWORDS = ("workout",)

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
OAUTH_BASE_URL = "https://oauth.reddit.com"
PUBLIC_BASE_URL = "https://www.reddit.com"


def get_access_token(
    client_id: str,
    client_secret: str,
    *,
    session: Optional[requests.Session] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: float = 15.0,
) -> str:
    """Exchange script-app credentials for an app-only OAuth access token."""
    session = session or requests.Session()
    resp = session.post(
        TOKEN_URL,
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": user_agent},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_posts(
    subreddit: str,
    *,
    sort: str = "new",
    limit: int = 50,
    query: Optional[str] = None,
    session: Optional[requests.Session] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    access_token: Optional[str] = None,
    timeout: float = 15.0,
) -> list[dict[str, Any]]:
    """Return raw post data dicts from a subreddit listing or search.

    Uses the authenticated ``oauth.reddit.com`` API when ``access_token`` is
    given, otherwise falls back to the public ``www.reddit.com`` endpoints.
    """
    session = session or requests.Session()
    base = f"{OAUTH_BASE_URL}/r/{subreddit}" if access_token else f"{PUBLIC_BASE_URL}/r/{subreddit}"
    suffix = "" if access_token else ".json"

    if query:
        url = f"{base}/search{suffix}"
        params: dict[str, Any] = {"q": query, "restrict_sr": "on", "sort": sort, "limit": limit}
    else:
        url = f"{base}/{sort}{suffix}"
        params = {"limit": limit}

    headers = {"User-Agent": user_agent}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    resp = session.get(url, params=params, headers=headers, timeout=timeout)
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
    """Fetch and return the raw post dict for today's daily workout thread.

    Uses OAuth (via ``REDDIT_CLIENT_ID``/``REDDIT_CLIENT_SECRET`` env vars)
    when available, since Reddit blocks most unauthenticated automated
    requests to the public ``.json`` endpoints.
    """
    session = session or requests.Session()

    access_token = None
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if client_id and client_secret:
        access_token = get_access_token(client_id, client_secret, session=session)

    posts = fetch_posts(subreddit, sort="new", limit=50, session=session, access_token=access_token)
    post = find_daily_workout_post(posts, target_date=target_date)
    if post is not None:
        return post

    # New listing may have scrolled past it; fall back to a search.
    posts = fetch_posts(
        subreddit, query="workout", sort="new", limit=25, session=session, access_token=access_token
    )
    return find_daily_workout_post(posts, target_date=target_date)
