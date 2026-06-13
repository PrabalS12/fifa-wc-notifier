"""football-data.org v4 client for the FIFA World Cup (competition code: WC)."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import requests

BASE = "https://api.football-data.org/v4"
COMPETITION = "WC"
IST = ZoneInfo("Asia/Kolkata")


def to_ist_str(utc_iso: str) -> str:
    """'2026-06-13T19:00:00Z' -> '12:30 AM IST'."""
    d = dt.datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
    return d.astimezone(IST).strftime("%I:%M %p").lstrip("0") + " IST"


def _group_label(stage: str | None, group: str | None) -> str:
    raw = group or stage or ""
    return raw.replace("_", " ").title()


class Football:
    def __init__(self, api_key: str):
        self._headers = {"X-Auth-Token": api_key}

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = requests.get(f"{BASE}{path}", headers=self._headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def matches(self, date_from: dt.date, date_to: dt.date) -> list[dict]:
        data = self._get(
            f"/competitions/{COMPETITION}/matches",
            {"dateFrom": date_from.isoformat(), "dateTo": date_to.isoformat()},
        )
        return data.get("matches", [])

    def standings(self) -> list[dict]:
        """Return group tables: [{group, table:[{team, played, points, gd}]}]."""
        data = self._get(f"/competitions/{COMPETITION}/standings")
        groups: list[dict] = []
        for s in data.get("standings", []):
            if s.get("type") != "TOTAL":
                continue
            groups.append(
                {
                    "group": _group_label(s.get("stage"), s.get("group")),
                    "table": [
                        {
                            "team": row["team"]["name"],
                            "played": row["playedGames"],
                            "points": row["points"],
                            "gd": row["goalDifference"],
                        }
                        for row in s.get("table", [])
                    ],
                }
            )
        return groups

    def match_goals(self, match_id: int) -> list[dict]:
        """Best-effort scorer detail; free tier may omit it -> returns []."""
        try:
            data = self._get(f"/matches/{match_id}")
        except requests.RequestException:
            return []
        return data.get("goals") or []
