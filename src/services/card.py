"""Render a notification card (HTML/CSS) to a PNG via headless Chromium."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from src.models import Fixture, Goal, GroupStanding, MatchResult
from src.services.content import PreviewEnrichment, RecapEnrichment
from src.services.flags import flag_url

_TEMPLATES = Path(__file__).resolve().parents[2] / "templates"
_env = Environment(loader=FileSystemLoader(_TEMPLATES), autoescape=select_autoescape(["html"]))


def _groups(standings: list[GroupStanding]) -> list[dict]:
    return [
        {
            "name": g.group,
            "rows": [
                {"team": t.team, "pl": t.played, "gd": f"{t.goal_difference:+d}", "pts": t.points}
                for t in g.table
            ],
        }
        for g in standings
    ]


def build_preview_card(
    date_label: str,
    fixtures: list[Fixture],
    standings: list[GroupStanding],
    enrich: PreviewEnrichment | None,
) -> dict:
    """Assemble the preview card dict from fixtures, standings, and Gemini enrichment."""
    by_home = {m.home: m for m in (enrich.matches if enrich else [])}
    matches = []
    for f in fixtures:
        e = by_home.get(f.home)
        meta = f"🕒 {f.kickoff_ist} · {f.group}" + (f" · {f.venue}" if f.venue else "")
        matches.append(
            {
                "home": f.home,
                "away": f.away,
                "home_flag": flag_url(f.home),
                "away_flag": flag_url(f.away),
                "meta": meta,
                "stars": e.stars if e else "",
                "note": e.note if e else "",
            }
        )
    return {
        "emoji": "🌙",
        "title": "TONIGHT'S SLATE",
        "date": date_label,
        "match_of_night": enrich.match_of_night if enrich else "",
        "matches": matches,
        "groups": _groups(standings),
        "fact": f"💡 {enrich.fun_fact}" if enrich and enrich.fun_fact else "",
    }


def build_recap_card(
    date_label: str,
    results: list[MatchResult],
    standings: list[GroupStanding],
    enrich: RecapEnrichment | None,
) -> dict:
    """Assemble the recap card dict from results, standings, and Gemini enrichment."""
    matches = []
    for r in results:
        home = [_goal(g) for g in r.goals if g.side == "home"]
        away = [_goal(g) for g in r.goals if g.side == "away"]
        scorers = "  |  ".join(part for part in [" · ".join(home), " · ".join(away)] if part)
        matches.append(
            {
                "home": r.home,
                "away": r.away,
                "home_flag": flag_url(r.home),
                "away_flag": flag_url(r.away),
                "score": r.score.replace("-", "–"),
                "scorers": scorers,
            }
        )
    return {
        "emoji": "☀️",
        "title": "MORNING RECAP",
        "date": date_label,
        "match_of_night": "",
        "matches": matches,
        "groups": _groups(standings),
        "fact": f"🔥 {enrich.storyline}" if enrich and enrich.storyline else "",
    }


def _goal(goal: Goal) -> str:
    tag = f" ({goal.note})" if goal.note else ""
    return f"{goal.scorer} {goal.minute}{tag}"


def render_card(card: dict) -> bytes:
    """Render the card dict to PNG bytes (cropped to the card element, retina-scaled)."""
    html = _env.get_template("card.html.j2").render(**card)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=2)
        page.set_content(html, wait_until="networkidle")  # waits for flag images to load
        element = page.query_selector("#card")
        png = element.screenshot(type="png")
        browser.close()
    return png
