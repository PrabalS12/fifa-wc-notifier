"""Domain models passed between the data client, content, and delivery."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Fixture:
    """An upcoming match shown in the preview."""

    home: str
    away: str
    group: str
    kickoff_ist: str
    venue: str = ""


@dataclass(frozen=True)
class Goal:
    """A single goal in a finished match."""

    scorer: str
    minute: str
    side: str  # "home" or "away"
    note: str = ""  # "P" (penalty), "OG" (own goal), or ""


@dataclass(frozen=True)
class MatchResult:
    """A finished match shown in the recap."""

    home: str
    away: str
    score: str
    goals: list[Goal] = field(default_factory=list)
    group: str = ""


@dataclass(frozen=True)
class TeamStanding:
    """A single row in a group table."""

    team: str
    played: int
    goal_difference: int
    points: int


@dataclass(frozen=True)
class GroupStanding:
    """A group's standings table."""

    group: str
    table: list[TeamStanding]
