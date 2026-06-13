"""Compose the two WhatsApp messages per run.

Message 1 is the Gemini-written narrative (matches / results — facts copied verbatim,
star players, one-liners, fun fact). Message 2 is the deterministic monospace standings
table plus the fun-fact/storyline. Each message is kept within the WhatsApp body limit.
Falls back to a plain layout if the LLM call fails.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict

from google import genai
from google.genai import types

from src.config import Settings
from src.log import get_logger
from src.models import Fixture, GroupStanding, MatchResult
from src.services.prompts import load

logger = get_logger(__name__)

MAX_CHARS = 1024  # WhatsApp body / template-parameter ceiling
FACT_MARKER = "[[FACT]]"


class ContentWriter:
    """Turns structured match data into engaging, WhatsApp-formatted messages."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def build(
        self,
        mode: str,
        date_label: str,
        matches: list[Fixture] | list[MatchResult],
        standings: list[GroupStanding],
    ) -> list[str]:
        """Return [matches message, standings message] for this run."""
        narrative, fact = self._narrative(mode, date_label, matches)
        matches_msg = _clip(narrative) if narrative else _fallback(mode, date_label, matches)
        standings_msg = _standings_message(standings, fact)
        return [m for m in (matches_msg, standings_msg) if m]

    def _narrative(self, mode: str, date_label: str, matches: list) -> tuple[str, str]:
        """Return (matches message, fun-fact/storyline); empty strings on failure."""
        payload = {"date": date_label, "matches": [asdict(m) for m in matches]}
        prompt = load(mode)
        user = prompt.user.substitute(date=date_label, data=json.dumps(payload, ensure_ascii=False))
        config = types.GenerateContentConfig(
            system_instruction=prompt.system,
            thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
        )
        for attempt in range(3):
            try:
                resp = self._client.models.generate_content(
                    model=self._settings.gemini_model, contents=user, config=config
                )
                text = (resp.text or "").strip()
                if FACT_MARKER in text:
                    main, fact = text.split(FACT_MARKER, 1)
                    return main.strip(), fact.strip()
                return text, ""
            except Exception:  # noqa: BLE001 — retry transient errors, then fall back
                logger.warning("Gemini attempt %d failed", attempt + 1, exc_info=True)
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
        return "", ""


# --- standings table (deterministic, monospace) ---------------------------


def _short(name: str) -> str:
    return name if len(name) <= 13 else name[:12] + "."


def _standings_message(standings: list[GroupStanding], fact: str) -> str:
    blocks = []
    for group in standings:
        rows = [f"📊 *{group.group}*", "```", f"{'Team':<13}{'Pl':>2}{'GD':>4}{'Pts':>4}"]
        rows += [
            f"{_short(t.team):<13}{t.played:>2}{t.goal_difference:>+4}{t.points:>4}"
            for t in group.table
        ]
        rows.append("```")
        blocks.append("\n".join(rows))
    if fact:
        blocks.append(fact)
    return _clip("\n\n".join(blocks))


# --- helpers --------------------------------------------------------------


def _clip(text: str) -> str:
    """Trim to MAX_CHARS at a line boundary so a message never cuts mid-line."""
    text = text.strip()
    if len(text) <= MAX_CHARS:
        return text
    head = text[:MAX_CHARS]
    cut = head.rfind("\n")
    return (head[:cut] if cut > 0 else head).rstrip()


def _fallback(mode: str, date_label: str, matches: list) -> str:
    lines: list[str] = []
    if mode == "preview":
        lines.append(f"🌙 *Tonight's World Cup* — {date_label}")
        if not matches:
            lines.append("😴 No matches tonight.")
        for m in matches:
            lines.append(f"\n{m.home} vs {m.away} · *{m.kickoff_ist}* · {m.group}")
    else:
        lines.append(f"☀️ *Morning Recap* — {date_label}")
        if not matches:
            lines.append("😴 No matches overnight.")
        for m in matches:
            scorers = " · ".join(f"{g.scorer} {g.minute}" for g in m.goals) or "scores in"
            line = f"\n*{m.home} {m.score} {m.away}*\n⚽ {scorers}"
            if m.highlights_url:
                line += f"\n▶️ {m.highlights_url}"
            lines.append(line)
    return _clip("\n".join(lines))
