"""Turn structured match data into an engaging WhatsApp message via Gemini.

Falls back to a clean deterministic layout if the LLM call fails, so a message
always goes out.
"""

from __future__ import annotations

import json

from google import genai
from google.genai import types

MAX_CHARS = 950  # stay comfortably under WhatsApp's template body limit

_SYSTEM = (
    "You are a witty football broadcaster writing a SHORT WhatsApp message for a fan in "
    "India about the FIFA World Cup 2026. Vivid and fun, but tight. Hard rules:\n"
    "- Plain text only. No markdown, no code fences, no bold/asterisks.\n"
    "- Lead each line with an emoji; exactly one line per match.\n"
    "- Use ONLY facts present in the JSON. Never invent scores, scorers, times, or stats.\n"
    "- Reproduce the highlight URLs EXACTLY as given; never fabricate a link.\n"
    "- At most ONE short fun fact or star-player nod per match, and only for globally famous "
    "players you are confident currently represent that team; otherwise skip it.\n"
    "- No filler. Omit any section that has no data. Keep the whole message under "
    f"{MAX_CHARS} characters."
)

_PREVIEW_SHAPE = """Write a PREVIEW. Layout:
First line: 🌙 TONIGHT'S SLATE — <date>
Per match: <Team A> vs <Team B> · ⏰ <kickoff_ist> · <group> — <one punchy line on what's at stake>
Then standings (only the groups provided): 📊 <Group>: <Team> <pts> · ...
Last line: one hype sign-off."""

_RECAP_SHAPE = """Write a RECAP of matches that just finished. Layout:
First line: ☀️ MORNING RECAP — <date>
Per match: <Team A> <score> <Team B> · ⚡ <scorers, or 'no goals'> · ▶️ <link>
Then standings (only the groups provided): 📊 <Group>: <Team> <pts> · ...
Last line: one sharp storyline takeaway."""


def build_message(cfg, mode: str, date_label: str, items: list[dict], standings: list[dict]) -> str:
    shape = _PREVIEW_SHAPE if mode == "preview" else _RECAP_SHAPE
    payload = {"date": date_label, "matches": items, "standings": standings}
    prompt = f"{shape}\n\nDATA (JSON):\n{json.dumps(payload, ensure_ascii=False)}"
    try:
        client = genai.Client(api_key=cfg.gemini_api_key)
        resp = client.models.generate_content(
            model=cfg.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM,
                thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
            ),
        )
        text = (resp.text or "").strip()
        if text:
            return text[:MAX_CHARS]
    except Exception:  # noqa: BLE001 - any LLM failure must not block the notification
        pass
    return _fallback(mode, date_label, items, standings)


def _standings_lines(standings: list[dict]) -> list[str]:
    lines = []
    for g in standings:
        snapshot = " · ".join(f"{r['team']} {r['points']}" for r in g["table"][:4])
        if snapshot:
            lines.append(f"📊 {g['group']}: {snapshot}")
    return lines


def _fallback(mode: str, date_label: str, items: list[dict], standings: list[dict]) -> str:
    lines: list[str] = []
    if mode == "preview":
        lines.append(f"🌙 TONIGHT'S SLATE — {date_label}")
        if not items:
            lines.append("😴 No World Cup matches tonight. Rest up!")
        for m in items:
            lines.append(f"⚽ {m['home']} vs {m['away']} · ⏰ {m['kickoff_ist']} · {m['group']}")
    else:
        lines.append(f"☀️ MORNING RECAP — {date_label}")
        if not items:
            lines.append("😴 No matches finished overnight.")
        for m in items:
            scorers = ", ".join(m.get("scorers") or []) or "no goals"
            lines.append(f"⚽ {m['home']} {m['score']} {m['away']} · ⚡ {scorers}")
            lines.append(f"   ▶️ {m['link']}")
    lines.extend(_standings_lines(standings))
    return "\n".join(lines)[:MAX_CHARS]
