"""Highlights links. Default: zero-cost YouTube search URL. Optional: Data API top video."""

from __future__ import annotations

from urllib.parse import quote_plus

import requests


def _query(home: str, away: str) -> str:
    return f"{home} vs {away} highlights FIFA World Cup 2026"


def _search_url(home: str, away: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(_query(home, away))}"


def highlights_url(home: str, away: str, api_key: str | None = None) -> str:
    """Direct top-video URL when an API key is set, else a search URL (always resolves)."""
    if not api_key:
        return _search_url(home, away)
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "type": "video",
                "maxResults": 1,
                "q": _query(home, away),
                "key": api_key,
            },
            timeout=20,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if items:
            return f"https://www.youtube.com/watch?v={items[0]['id']['videoId']}"
    except (requests.RequestException, KeyError, IndexError):
        pass
    return _search_url(home, away)
