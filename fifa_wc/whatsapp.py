"""Send a message via the Meta WhatsApp Cloud API."""

from __future__ import annotations

import requests

GRAPH = "https://graph.facebook.com/v21.0"


def send(cfg, text: str) -> dict:
    url = f"{GRAPH}/{cfg.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {cfg.whatsapp_token}",
        "Content-Type": "application/json",
    }

    if cfg.whatsapp_use_template:
        # Required for business-initiated (unprompted) messages outside the 24h window.
        payload = {
            "messaging_product": "whatsapp",
            "to": cfg.whatsapp_recipient,
            "type": "template",
            "template": {
                "name": cfg.whatsapp_template_name,
                "language": {"code": cfg.whatsapp_template_lang},
                "components": [
                    {"type": "body", "parameters": [{"type": "text", "text": text}]}
                ],
            },
        }
    else:
        # Free-form text — only delivers inside an open 24h customer-service window.
        payload = {
            "messaging_product": "whatsapp",
            "to": cfg.whatsapp_recipient,
            "type": "text",
            "text": {"body": text},
        }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 300:
        raise RuntimeError(f"WhatsApp send failed [{resp.status_code}]: {resp.text}")
    return resp.json()
