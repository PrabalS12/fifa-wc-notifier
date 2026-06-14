"""Orchestrates a single notification run: gather -> render card -> deliver image."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from src.clients import FootballData, WhatsAppClient
from src.clients.football import IST
from src.config import Settings
from src.log import get_logger
from src.models import Fixture, MatchResult
from src.services import ContentWriter, build_preview_card, build_recap_card, render_card

logger = get_logger(__name__)


class Notifier:
    """Builds and sends one preview or recap image card."""

    def __init__(self, settings: Settings, dry_run: bool = False) -> None:
        self._settings = settings
        self._dry_run = dry_run
        self._football = FootballData()
        self._whatsapp = WhatsAppClient(settings)
        self._writer = ContentWriter(settings)

    def run(self, mode: str) -> None:
        """Gather data for `mode`, render the card, and deliver it (or save it, if dry-run)."""
        now = dt.datetime.now(dt.UTC)
        date_label = now.astimezone(IST).strftime("%a, %d %b")

        matches, card = self._build(mode, date_label, now)
        if not matches:
            logger.info("no matches for %s — nothing to send", mode)
            return

        png = render_card(card)

        if self._dry_run:
            out = Path("samples") / f"{mode}_card.png"
            out.parent.mkdir(exist_ok=True)
            out.write_bytes(png)
            logger.info("dry-run — wrote %s (%d bytes)", out, len(png))
            return

        media_id = self._whatsapp.upload_media(png)
        self._whatsapp.send_image(media_id)
        count = len(self._settings.whatsapp_recipients)
        logger.info("sent %s card to %d recipient(s)", mode, count)

    def _build(self, mode: str, date_label: str, now: dt.datetime) -> tuple[list, dict]:
        if mode == "preview":
            fixtures = self._football.upcoming_fixtures(now)
            standings = self._football.standings(_group_labels(fixtures))
            enrich = self._writer.enrich_preview(fixtures)
            return fixtures, build_preview_card(date_label, fixtures, standings, enrich)
        results = self._football.recent_results(now)
        standings = self._football.standings(_group_labels(results))
        enrich = self._writer.enrich_recap(results)
        return results, build_recap_card(date_label, results, standings, enrich)


def _group_labels(matches: list[Fixture] | list[MatchResult]) -> set[str]:
    return {m.group for m in matches if m.group.startswith("Group")}
