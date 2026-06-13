"""Entrypoint: `python -m fifa_wc [preview|recap]`.

preview -> upcoming matches (run 9 PM IST). recap -> finished matches (run 11 AM IST).
"""

from __future__ import annotations

import datetime as dt
import sys

from . import config, content, whatsapp
from .football import IST, Football, _group_label, to_ist_str
from .youtube import highlights_url

UPCOMING_STATUSES = ("SCHEDULED", "TIMED")


def _date_label(now: dt.datetime) -> str:
    return now.astimezone(IST).strftime("%a, %d %b")


def _kickoff(m: dict) -> dt.datetime:
    return dt.datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))


def gather_preview(fb: Football, now: dt.datetime) -> list[dict]:
    """Matches kicking off within the next ~30h (i.e. overnight IST)."""
    matches = fb.matches((now - dt.timedelta(hours=6)).date(), (now + dt.timedelta(days=2)).date())
    items = []
    for m in matches:
        if m.get("status") not in UPCOMING_STATUSES:
            continue
        if not (now - dt.timedelta(hours=1) <= _kickoff(m) <= now + dt.timedelta(hours=30)):
            continue
        items.append(
            {
                "home": m["homeTeam"].get("name") or "TBD",
                "away": m["awayTeam"].get("name") or "TBD",
                "group": _group_label(m.get("stage"), m.get("group")),
                "kickoff_ist": to_ist_str(m["utcDate"]),
            }
        )
    items.sort(key=lambda x: x["kickoff_ist"])
    return items


def gather_recap(fb: Football, cfg: config.Config, now: dt.datetime) -> list[dict]:
    """Matches that finished in roughly the last 30h."""
    matches = fb.matches((now - dt.timedelta(days=2)).date(), now.date())
    items = []
    for m in matches:
        if m.get("status") != "FINISHED":
            continue
        if _kickoff(m) < now - dt.timedelta(hours=30):
            continue
        home, away = m["homeTeam"].get("name") or "TBD", m["awayTeam"].get("name") or "TBD"
        full = m.get("score", {}).get("fullTime", {})
        scorers = []
        for g in fb.match_goals(m["id"]):
            name = (g.get("scorer") or {}).get("name")
            if not name:
                continue
            minute = g.get("minute")
            scorers.append(f"{name} {minute}'" if minute else name)
        items.append(
            {
                "home": home,
                "away": away,
                "score": f"{full.get('home', '?')}-{full.get('away', '?')}",
                "scorers": scorers,
                "group": _group_label(m.get("stage"), m.get("group")),
                "link": highlights_url(home, away, cfg.youtube_api_key),
            }
        )
    return items


def _relevant_standings(fb: Football, items: list[dict]) -> list[dict]:
    groups = {m["group"] for m in items if m["group"].startswith("Group")}
    if not groups:
        return []
    return [g for g in fb.standings() if g["group"] in groups]


def main(argv: list[str]) -> int:
    mode = (argv[1] if len(argv) > 1 else "preview").lower()
    if mode not in ("preview", "recap"):
        print("usage: python -m fifa_wc [preview|recap]", file=sys.stderr)
        return 2

    cfg = config.load()
    fb = Football(cfg.football_api_key)
    now = dt.datetime.now(dt.timezone.utc)
    label = _date_label(now)

    try:
        items = gather_preview(fb, now) if mode == "preview" else gather_recap(fb, cfg, now)
        standings = _relevant_standings(fb, items)
        text = content.build_message(cfg, mode, label, items, standings)
    except Exception as exc:  # noqa: BLE001 - degrade to a short message rather than going silent
        text = f"⚽ WC {mode} update unavailable right now ({exc.__class__.__name__}). Back soon!"

    whatsapp.send(cfg, text)
    print(f"[fifa_wc] sent {mode} message ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
