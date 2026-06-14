"""Deliver an image card via the Meta WhatsApp Cloud API."""

from __future__ import annotations

import requests

from src.config import Settings

GRAPH = "https://graph.facebook.com/v25.0"


class WhatsAppClient:
    """Uploads a PNG and sends it as a template (unprompted) or free-form image."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def upload_media(self, png: bytes, filename: str = "card.png") -> str:
        """Upload PNG bytes to the Cloud API media store; returns a reusable media ID."""
        s = self._settings
        resp = requests.post(
            f"{GRAPH}/{s.whatsapp_phone_number_id}/media",
            headers={"Authorization": f"Bearer {s.whatsapp_token}"},
            data={"messaging_product": "whatsapp", "type": "image/png"},
            files={"file": (filename, png, "image/png")},
            timeout=60,
        )
        if resp.status_code >= 300:
            raise RuntimeError(f"WhatsApp media upload failed [{resp.status_code}]: {resp.text}")
        return resp.json()["id"]

    def send_image(self, media_id: str) -> list[dict]:
        """Send the uploaded image to every recipient. Raises on the first non-2xx."""
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
            payload = self._payload(media_id, recipient)
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code >= 300:
                raise RuntimeError(
                    f"WhatsApp send to {recipient} failed [{resp.status_code}]: {resp.text}"
                )
            responses.append(resp.json())
        return responses

    def _payload(self, media_id: str, recipient: str) -> dict:
        s = self._settings
        if s.whatsapp_use_template:
            # Unprompted (outside 24h window) must use an approved template; the image goes in
            # the header parameter, which has none of the text restrictions.
            return {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "template",
                "template": {
                    "name": s.whatsapp_template_name,
                    "language": {"code": s.whatsapp_template_lang},
                    "components": [
                        {
                            "type": "header",
                            "parameters": [{"type": "image", "image": {"id": media_id}}],
                        }
                    ],
                },
            }
        # Free-form image — only delivers inside an open 24h window (used for testing).
        return {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "image",
            "image": {"id": media_id},
        }
