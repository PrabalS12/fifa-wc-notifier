"""Orchestrates a single notification run: gather -> compose -> deliver."""

from __future__ import annotations

import datetime as dt
from dataclasses import replace

from src.clients import FootballClient, WhatsAppClient, highlights_url
from src.clients.football import IST
from src.config import Settings
from src.log import get_logger
from src.models import Fixture, MatchResult
from src.services import ContentWriter

logger = get_logger(__name__)


class Notifier:
    """Builds and sends one preview or recap message."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._football = FootballClient(settings.football_data_api_key)
        self._whatsapp = WhatsAppClient(settings)
        self._writer = ContentWriter(settings)

    def run(self, mode: str) -> None:
        """Gather data for `mode`, compose the message, and deliver it."""
        now = dt.datetime.now(dt.UTC)
        date_label = now.astimezone(IST).strftime("%a, %d %b")
        try:
            matches = self._gather(mode, now)
            standings = self._football.standings(_group_labels(matches))
            text = self._writer.build(mode, date_label, matches, standings)
        except Exception as exc:  # noqa: BLE001 — degrade to a short note rather than go silent
            logger.exception("failed to build %s message", mode)
            text = f"⚽ WC {mode} update unavailable ({exc.__class__.__name__}). Back soon!"

        self._whatsapp.send(text)
        logger.info("sent %s message (%d chars)", mode, len(text))

    def _gather(self, mode: str, now: dt.datetime) -> list[Fixture] | list[MatchResult]:
        if mode == "preview":
            return self._football.upcoming_fixtures(now)
        key = self._settings.youtube_api_key
        return [
            replace(r, highlights_url=highlights_url(r.home, r.away, key))
            for r in self._football.recent_results(now)
        ]


def _group_labels(matches: list[Fixture] | list[MatchResult]) -> set[str]:
    return {m.group for m in matches if m.group.startswith("Group")}
