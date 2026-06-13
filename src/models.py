"""Domain models passed between clients, content, and delivery."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fixture:
    """An upcoming match shown in the preview."""

    home: str
    away: str
    group: str
    kickoff_ist: str


@dataclass(frozen=True)
class MatchResult:
    """A finished match shown in the recap."""

    home: str
    away: str
    score: str
    scorers: list[str]
    group: str
    highlights_url: str = ""


@dataclass(frozen=True)
class TeamStanding:
    """A single row in a group table."""

    team: str
    played: int
    points: int
    goal_difference: int


@dataclass(frozen=True)
class GroupStanding:
    """A group's standings table."""

    group: str
    table: list[TeamStanding]
