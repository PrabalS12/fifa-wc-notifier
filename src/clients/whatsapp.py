"""Deliver a message via the Meta WhatsApp Cloud API."""

from __future__ import annotations

import requests

from src.config import Settings

GRAPH = "https://graph.facebook.com/v25.0"


class WhatsAppClient:
    """Sends template or free-form messages through the Cloud API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send(self, messages: str | list[str]) -> list[dict]:
        """Send each message to every recipient, in order. Raises on the first non-2xx."""
        if isinstance(messages, str):
            messages = [messages]
        s = self._settings
        if not (s.whatsapp_token and s.whatsapp_phone_number_id and s.whatsapp_recipients):
            raise RuntimeError(
                "WhatsApp credentials missing (token / phone_number_id / recipient). "
                "Set them, or use --dry-run."
            )
        url = f"{GRAPH}/{s.whatsapp_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {s.whatsapp_token}",
            "Content-Type": "application/json",
        }
        responses = []
        for recipient in s.whatsapp_recipients:
            for text in messages:
                payload = self._payload(text, recipient)
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code >= 300:
                    raise RuntimeError(
                        f"WhatsApp send to {recipient} failed [{resp.status_code}]: {resp.text}"
                    )
                responses.append(resp.json())
        return responses

    def _payload(self, text: str, recipient: str) -> dict:
        s = self._settings
        if s.whatsapp_use_template:
            # Required for business-initiated (unprompted) messages outside the 24h window.
            return {
                "messaging_product": "whatsapp",
                "to": recipient,
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
            "to": recipient,
            "type": "text",
            "text": {"body": text},
        }
