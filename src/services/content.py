"""Compose the WhatsApp message — Gemini-written, with a deterministic fallback."""

from __future__ import annotations

import json
from dataclasses import asdict

from google import genai
from google.genai import types

from src.config import Settings
from src.log import get_logger
from src.models import Fixture, GroupStanding, MatchResult
from src.services.prompts import load

logger = get_logger(__name__)
MAX_CHARS = 950


class ContentWriter:
    """Turns structured match data into an engaging message via Gemini."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def build(
        self,
        mode: str,
        date_label: str,
        matches: list[Fixture] | list[MatchResult],
        standings: list[GroupStanding],
    ) -> str:
        """Return WhatsApp-ready text; falls back to a plain layout on any LLM failure."""
        payload = {
            "date": date_label,
            "matches": [asdict(m) for m in matches],
            "standings": [asdict(s) for s in standings],
        }
        return self._generate(mode, date_label, payload) or _fallback(
            mode, date_label, matches, standings
        )

    def _generate(self, mode: str, date_label: str, payload: dict) -> str:
        prompt = load(mode)
        user = prompt.user.substitute(
            date=date_label, data=json.dumps(payload, ensure_ascii=False)
        )
        try:
            resp = self._client.models.generate_content(
                model=self._settings.gemini_model,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=prompt.system,
                    thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
                ),
            )
            return (resp.text or "").strip()[:MAX_CHARS]
        except Exception:  # noqa: BLE001 — an LLM failure must not block delivery
            logger.warning("Gemini generation failed; using fallback", exc_info=True)
            return ""


def _fallback(
    mode: str,
    date_label: str,
    matches: list[Fixture] | list[MatchResult],
    standings: list[GroupStanding],
) -> str:
    lines: list[str] = []
    if mode == "preview":
        lines.append(f"🌙 TONIGHT'S SLATE — {date_label}")
        if not matches:
            lines.append("😴 No World Cup matches tonight. Rest up!")
        lines += [f"⚽ {m.home} vs {m.away} · ⏰ {m.kickoff_ist} · {m.group}" for m in matches]
    else:
        lines.append(f"☀️ MORNING RECAP — {date_label}")
        if not matches:
            lines.append("😴 No matches finished overnight.")
        for m in matches:
            scorers = ", ".join(m.scorers) or "no goals"
            lines.append(f"⚽ {m.home} {m.score} {m.away} · ⚡ {scorers}")
            lines.append(f"   ▶️ {m.highlights_url}")
    for group in standings:
        snapshot = " · ".join(f"{row.team} {row.points}" for row in group.table[:4])
        if snapshot:
            lines.append(f"📊 {group.group}: {snapshot}")
    return "\n".join(lines)[:MAX_CHARS]
