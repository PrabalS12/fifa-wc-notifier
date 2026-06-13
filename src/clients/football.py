"""football-data.org v4 client for the FIFA World Cup (competition code: WC)."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import requests

from src.models import Fixture, GroupStanding, MatchResult, TeamStanding

BASE = "https://api.football-data.org/v4"
COMPETITION = "WC"
IST = ZoneInfo("Asia/Kolkata")
UPCOMING_STATUSES = {"SCHEDULED", "TIMED"}


class FootballClient:
    """Thin synchronous wrapper over the football-data.org REST API."""

    def __init__(self, api_key: str) -> None:
        self._headers = {"X-Auth-Token": api_key}

    def upcoming_fixtures(self, now: dt.datetime) -> list[Fixture]:
        """Fixtures kicking off within the next ~30h (i.e. overnight IST)."""
        lower, upper = now - dt.timedelta(hours=1), now + dt.timedelta(hours=30)
        raw = self._matches(
            (now - dt.timedelta(hours=6)).date(), (now + dt.timedelta(days=2)).date()
        )
        fixtures = [
            Fixture(
                home=_team(m, "homeTeam"),
                away=_team(m, "awayTeam"),
                group=_group(m),
                kickoff_ist=_to_ist(_kickoff(m)),
            )
            for m in raw
            if m.get("status") in UPCOMING_STATUSES and lower <= _kickoff(m) <= upper
        ]
        return sorted(fixtures, key=lambda f: f.kickoff_ist)

    def recent_results(self, now: dt.datetime) -> list[MatchResult]:
        """Matches that finished within roughly the last 30h (highlight links added later)."""
        cutoff = now - dt.timedelta(hours=30)
        results = []
        for m in self._matches((now - dt.timedelta(days=2)).date(), now.date()):
            if m.get("status") != "FINISHED" or _kickoff(m) < cutoff:
                continue
            full = m.get("score", {}).get("fullTime", {})
            results.append(
                MatchResult(
                    home=_team(m, "homeTeam"),
                    away=_team(m, "awayTeam"),
                    score=f"{full.get('home', '?')}-{full.get('away', '?')}",
                    scorers=self._scorers(m["id"]),
                    group=_group(m),
                )
            )
        return results

    def standings(self, groups: set[str]) -> list[GroupStanding]:
        """Group tables, filtered to the given group labels (empty set -> no call)."""
        if not groups:
            return []
        data = self._get(f"/competitions/{COMPETITION}/standings")
        tables = []
        for s in data.get("standings", []):
            if s.get("type") != "TOTAL":
                continue
            label = _label(s.get("group") or s.get("stage"))
            if label not in groups:
                continue
            tables.append(
                GroupStanding(
                    group=label,
                    table=[
                        TeamStanding(
                            team=row["team"]["name"],
                            played=row["playedGames"],
                            points=row["points"],
                            goal_difference=row["goalDifference"],
                        )
                        for row in s.get("table", [])
                    ],
                )
            )
        return tables

    # --- internal ---------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = requests.get(f"{BASE}{path}", headers=self._headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _matches(self, date_from: dt.date, date_to: dt.date) -> list[dict]:
        data = self._get(
            f"/competitions/{COMPETITION}/matches",
            {"dateFrom": date_from.isoformat(), "dateTo": date_to.isoformat()},
        )
        return data.get("matches", [])

    def _scorers(self, match_id: int) -> list[str]:
        """Best-effort goal scorers; the free tier may omit them, returning []."""
        try:
            goals = self._get(f"/matches/{match_id}").get("goals") or []
        except requests.RequestException:
            return []
        scorers = []
        for goal in goals:
            name = (goal.get("scorer") or {}).get("name")
            if name:
                minute = goal.get("minute")
                scorers.append(f"{name} {minute}'" if minute else name)
        return scorers


def _kickoff(match: dict) -> dt.datetime:
    return dt.datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))


def _to_ist(when: dt.datetime) -> str:
    return when.astimezone(IST).strftime("%I:%M %p").lstrip("0") + " IST"


def _team(match: dict, side: str) -> str:
    return match[side].get("name") or "TBD"


def _label(raw: str | None) -> str:
    return (raw or "").replace("_", " ").title()


def _group(match: dict) -> str:
    return _label(match.get("group") or match.get("stage"))
