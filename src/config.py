"""Application settings loaded from environment variables (and an optional .env)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Secrets and tunables. Field names map to UPPER_SNAKE_CASE env vars."""

    gemini_api_key: str
    gemini_model: str = "gemini-3.1-flash-lite"

    # Optional so --dry-run works with only the data + LLM keys; required for a real send.
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    # One number, or several comma-separated, e.g. "9198...,9199...".
    whatsapp_recipient: str = ""
    whatsapp_template_name: str = "wc_update"
    whatsapp_template_lang: str = "en_US"
    # Set to false only for local testing inside an open 24h window (sends free-form text).
    whatsapp_use_template: bool = True

    youtube_api_key: str | None = None

    @computed_field
    @property
    def whatsapp_recipients(self) -> list[str]:
        """Recipient numbers parsed from the comma-separated WHATSAPP_RECIPIENT."""
        return [n.strip() for n in self.whatsapp_recipient.split(",") if n.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache settings once."""
    return Settings()
