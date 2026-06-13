"""World Cup data client.

Backed by ESPN's public soccer JSON feed (no key, current, no season limits).
The provider is an internal detail; callers only see domain models.
"""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import requests

from src.models import Fixture, Goal, GroupStanding, MatchResult, TeamStanding

_BASE = "https://site.api.espn.com/apis"
_SCOREBOARD = f"{_BASE}/site/v2/sports/soccer/fifa.world/scoreboard"
_STANDINGS = f"{_BASE}/v2/sports/soccer/fifa.world/standings"
_SEASON = 2026
IST = ZoneInfo("Asia/Kolkata")


class FootballData:
    """Reads World Cup fixtures, results, and standings."""

    def __init__(self, season: int = _SEASON) -> None:
        self._season = season
        self._group_by_team: dict[str, str] | None = None

    # --- public API -------------------------------------------------------

    def upcoming_fixtures(self, now: dt.datetime) -> list[Fixture]:
        """Matches kicking off between now (9 PM IST) and ~11 AM IST next day."""
        lower, upper = now - dt.timedelta(hours=1), now + dt.timedelta(hours=14)
        fixtures = []
        for event in self._events_between(now, now + dt.timedelta(days=2)):
            kickoff = _kickoff(event)
            if event["status"]["type"]["state"] != "pre" or not lower <= kickoff <= upper:
                continue
            home, away = _sides(event)
            fixtures.append(
                Fixture(
                    home=home["team"]["displayName"],
                    away=away["team"]["displayName"],
                    group=self._group_of(home["team"]["displayName"]),
                    kickoff_ist=_to_ist(kickoff),
                    venue=_venue(event),
                )
            )
        return sorted(fixtures, key=lambda f: f.kickoff_ist)

    def recent_results(self, now: dt.datetime) -> list[MatchResult]:
        """Finished matches from the overnight window (~9 PM IST prev day to 11 AM IST)."""
        cutoff = now - dt.timedelta(hours=14)
        results = []
        for event in self._events_between(now - dt.timedelta(days=2), now):
            if event["status"]["type"]["state"] != "post" or _kickoff(event) < cutoff:
                continue
            home, away = _sides(event)
            results.append(
                MatchResult(
                    home=home["team"]["displayName"],
                    away=away["team"]["displayName"],
                    score=f"{home.get('score', '?')}-{away.get('score', '?')}",
                    goals=_goals(event, home["id"]),
                    group=self._group_of(home["team"]["displayName"]),
                )
            )
        return results

    def standings(self, groups: set[str]) -> list[GroupStanding]:
        """Group tables, filtered to the given group labels (empty set -> nothing)."""
        if not groups:
            return []
        return [g for g in self._all_standings() if g.group in groups]

    # --- internal ---------------------------------------------------------

    def _get(self, url: str, params: dict | None = None) -> dict:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _events_between(self, start: dt.datetime, end: dt.datetime) -> list[dict]:
        events: list[dict] = []
        day = start.date()
        while day <= end.date():
            data = self._get(_SCOREBOARD, {"dates": day.strftime("%Y%m%d")})
            events.extend(data.get("events", []))
            day += dt.timedelta(days=1)
        return events

    def _all_standings(self) -> list[GroupStanding]:
        data = self._get(_STANDINGS, {"season": self._season})
        groups = []
        for child in data.get("children", []):
            entries = child.get("standings", {}).get("entries", [])
            table = sorted(
                (_standing_row(e) for e in entries),
                key=lambda r: (r.points, r.goal_difference, r.team),
                reverse=True,
            )
            groups.append(GroupStanding(group=child.get("name", ""), table=table))
        return groups

    def _group_of(self, team: str) -> str:
        if self._group_by_team is None:
            self._group_by_team = {
                row.team: g.group for g in self._all_standings() for row in g.table
            }
        return self._group_by_team.get(team, "")


def _sides(event: dict) -> tuple[dict, dict]:
    competitors = event["competitions"][0]["competitors"]
    home = next(c for c in competitors if c["homeAway"] == "home")
    away = next(c for c in competitors if c["homeAway"] == "away")
    return home, away


def _venue(event: dict) -> str:
    return event["competitions"][0].get("venue", {}).get("fullName", "")


def _kickoff(event: dict) -> dt.datetime:
    return dt.datetime.fromisoformat(event["date"].replace("Z", "+00:00"))


def _to_ist(when: dt.datetime) -> str:
    return when.astimezone(IST).strftime("%I:%M %p").lstrip("0") + " IST"


def _goals(event: dict, home_id: str) -> list[Goal]:
    goals = []
    for detail in event["competitions"][0].get("details", []):
        if not detail.get("scoringPlay"):
            continue
        athletes = detail.get("athletesInvolved") or []
        scorer = athletes[0]["displayName"] if athletes else detail.get("type", {}).get("text", "")
        kind = detail.get("type", {}).get("text", "")
        goals.append(
            Goal(
                scorer=scorer,
                minute=detail.get("clock", {}).get("displayValue", ""),
                side="home" if str(detail.get("team", {}).get("id")) == str(home_id) else "away",
                note="OG" if "Own" in kind else ("P" if "Penalty" in kind else ""),
            )
        )
    return goals


def _standing_row(entry: dict) -> TeamStanding:
    stats = {s["name"]: s for s in entry.get("stats", [])}

    def val(name: str) -> int:
        return int(stats.get(name, {}).get("value", 0))

    return TeamStanding(
        team=entry["team"]["displayName"],
        played=val("gamesPlayed"),
        goal_difference=val("pointDifferential"),
        points=val("points"),
    )
