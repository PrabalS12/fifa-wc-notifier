"""Deliver a message via the Meta WhatsApp Cloud API."""

from __future__ import annotations

import requests

from src.config import Settings

GRAPH = "https://graph.facebook.com/v21.0"


class WhatsAppClient:
    """Sends template or free-form messages through the Cloud API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send(self, text: str) -> dict:
        """Send `text` to the configured recipient. Raises on a non-2xx response."""
        s = self._settings
        if not (s.whatsapp_token and s.whatsapp_phone_number_id and s.whatsapp_recipient):
            raise RuntimeError(
                "WhatsApp credentials missing (token / phone_number_id / recipient). "
                "Set them, or use --dry-run."
            )
        url = f"{GRAPH}/{self._settings.whatsapp_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self._settings.whatsapp_token}",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, headers=headers, json=self._payload(text), timeout=30)
        if resp.status_code >= 300:
            raise RuntimeError(f"WhatsApp send failed [{resp.status_code}]: {resp.text}")
        return resp.json()

    def _payload(self, text: str) -> dict:
        s = self._settings
        if s.whatsapp_use_template:
            # Required for business-initiated (unprompted) messages outside the 24h window.
            return {
                "messaging_product": "whatsapp",
                "to": s.whatsapp_recipient,
                "type": "template",
                "template": {
                    "name": s.whatsapp_template_name,
                    "language": {"code": s.whatsapp_template_lang},
                    "components": [
                        {"type": "body", "parameters": [{"type": "text", "text": text}]}
                    ],
                },
            }
        return {
            "messaging_product": "whatsapp",
            "to": s.whatsapp_recipient,
            "type": "text",
            "text": {"body": text},
        }
