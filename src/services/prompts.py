"""Markdown prompt templates loaded from the prompts/ directory."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path
from string import Template

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


@dataclass(frozen=True)
class Prompt:
    """A system + user prompt pair for one notification mode."""

    system: str
    user: Template


@cache
def load(mode: str) -> Prompt:
    """Load the prompt pair for 'preview' or 'recap' (cached after first read)."""
    return Prompt(system=_read(mode, "system"), user=Template(_read(mode, "user")))


def _read(mode: str, name: str) -> str:
    path = PROMPTS_DIR / mode / f"{name}.md"
    return path.read_text(encoding="utf-8")
