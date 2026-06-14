"""Gemini enrichment for the card: star players, one-liners, fun fact, storyline.

Returns structured data (not formatted text) — the card renderer places it into HTML.
Returns None on failure so the pipeline still renders a card from the ESPN data alone.
"""

from __future__ import annotations

import json
import time

from google import genai
from google.genai import types
from pydantic import BaseModel

from src.config import Settings
from src.log import get_logger
from src.models import Fixture, MatchResult
from src.services.prompts import load

logger = get_logger(__name__)


class MatchEnrichment(BaseModel):
    """Per-fixture narrative for the preview card, keyed by home team."""

    home: str
    stars: str
    note: str


class PreviewEnrichment(BaseModel):
    """Narrative for the preview card."""

    match_of_night: str
    fun_fact: str
    matches: list[MatchEnrichment]


class RecapEnrichment(BaseModel):
    """Narrative for the recap card."""

    storyline: str


class ContentWriter:
    """Calls Gemini for structured card enrichment."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def enrich_preview(self, fixtures: list[Fixture]) -> PreviewEnrichment | None:
        """Stars, one-liners, match-of-night, and a fun fact for tonight's fixtures."""
        data = [{"home": f.home, "away": f.away, "group": f.group} for f in fixtures]
        return self._call("preview", data, PreviewEnrichment)

    def enrich_recap(self, results: list[MatchResult]) -> RecapEnrichment | None:
        """A one-line storyline for last night's results."""
        data = [{"home": r.home, "away": r.away, "score": r.score} for r in results]
        return self._call("recap", data, RecapEnrichment)

    def _call(self, mode: str, data: list[dict], schema: type[BaseModel]) -> BaseModel | None:
        prompt = load(mode)
        user = prompt.user.substitute(data=json.dumps(data, ensure_ascii=False))
        config = types.GenerateContentConfig(
            system_instruction=prompt.system,
            response_mime_type="application/json",
            response_schema=schema,
            thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
        )
        for attempt in range(3):
            try:
                resp = self._client.models.generate_content(
                    model=self._settings.gemini_model, contents=user, config=config
                )
                return schema.model_validate_json(resp.text or "")
            except Exception:  # noqa: BLE001 — retry transient errors, then degrade gracefully
                logger.warning("Gemini enrichment attempt %d failed", attempt + 1, exc_info=True)
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
        return None
