"""Configuration loaded from environment variables (fail-fast on missing secrets)."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


def _require(name: str) -> str:
    val = (os.environ.get(name) or "").strip()
    if not val:
        raise ConfigError(
            f"Missing required environment variable: {name}. "
            "See .env.example for the full list."
        )
    return val


def _optional(name: str, default: str = "") -> str:
    return (os.environ.get(name) or "").strip() or default


@dataclass(frozen=True)
class Config:
    football_api_key: str
    gemini_api_key: str
    gemini_model: str
    whatsapp_token: str
    whatsapp_phone_number_id: str
    whatsapp_recipient: str
    whatsapp_template_name: str
    whatsapp_template_lang: str
    whatsapp_use_template: bool
    youtube_api_key: str | None


def load() -> Config:
    return Config(
        football_api_key=_require("FOOTBALL_DATA_API_KEY"),
        gemini_api_key=_require("GEMINI_API_KEY"),
        gemini_model=_optional("GEMINI_MODEL", "gemini-3-flash-preview"),
        whatsapp_token=_require("WHATSAPP_TOKEN"),
        whatsapp_phone_number_id=_require("WHATSAPP_PHONE_NUMBER_ID"),
        whatsapp_recipient=_require("WHATSAPP_RECIPIENT"),
        whatsapp_template_name=_optional("WHATSAPP_TEMPLATE_NAME", "wc_update"),
        whatsapp_template_lang=_optional("WHATSAPP_TEMPLATE_LANG", "en_US"),
        # Set WHATSAPP_USE_TEMPLATE=false only for local testing inside an open 24h window.
        whatsapp_use_template=_optional("WHATSAPP_USE_TEMPLATE", "true").lower() != "false",
        youtube_api_key=_optional("YOUTUBE_API_KEY") or None,
    )
