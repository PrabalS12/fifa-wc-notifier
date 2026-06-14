# ⚽ FIFA World Cup 2026 — WhatsApp Notifier

Two free, hands-off daily WhatsApp **image cards** about WC 2026:

- **🌙 9 PM IST — Tonight's Slate:** tonight's matches (9 PM→11 AM IST window) with star players,
  a form/h2h/stakes one-liner, match-of-the-night, group standings, and a fun fact.
- **☀️ 11 AM IST — Morning Recap:** scores + **scorers** (minute, penalty/own-goal) from the
  matches that finished overnight, updated standings, and a storyline.

Each run renders **one image card** and sends it via WhatsApp — images sidestep the text-template
restrictions (no newlines/tables allowed in template text params) and look like a polished sports
card. Minimal by design: a single Python package run by **GitHub Actions cron** — no server, no
Docker. Match data: **ESPN's public API (no key)**. Narrative: **Gemini**. Delivery: **Meta
WhatsApp Cloud API** (image-header template).

## How it works

```
GitHub Actions cron ──> python main.py {preview|recap}
                              │
                              └─ src/pipeline.py  (gather → enrich → render → deliver)
                                   ├─ clients/football.py   ESPN: fixtures, scores, scorers, standings, venues
                                   ├─ services/content.py   Gemini → structured enrichment (stars, one-liner, fun fact)
                                   ├─ services/card.py       build card dict + render HTML→PNG (Playwright/Chromium)
                                   │     └─ templates/card.html.j2 · services/flags.py (flag images)
                                   └─ clients/whatsapp.py    upload PNG → send image template
```

## Project structure

```
fifa-wc/
├── main.py                      # entry: python main.py {preview|recap} [--dry-run]
├── prompts/{preview,recap}/{system,user}.md   # Gemini enrichment prompts
├── templates/card.html.j2       # the card layout (HTML/CSS)
└── src/
    ├── config.py                # pydantic-settings (env / .env)
    ├── models.py                # Fixture, Goal, MatchResult, GroupStanding, TeamStanding
    ├── pipeline.py              # Notifier — orchestration
    ├── log.py
    ├── clients/                 # football.py (ESPN data), whatsapp.py (media upload + send)
    └── services/                # content.py (Gemini), card.py (render), flags.py
```

## Setup

### 1. Keys
- **Google AI Studio** — `GEMINI_API_KEY` (the only required key).
- Match data: **none** — ESPN's public endpoints need no key.

### 2. WhatsApp Cloud API (free, no ban risk)
1. Meta app → add **WhatsApp** product → create a business portfolio.
2. Copy the test number's **Phone Number ID** (`WHATSAPP_PHONE_NUMBER_ID`); note the **WABA ID**
   and **App ID** (needed once for the template).
3. Add your number(s) as **verified recipients** (`WHATSAPP_RECIPIENT`, comma-separated).
4. **Image template** `wc_card` (category MARKETING — correct for a digest; UTILITY is for
   transactions only and Meta will reclassify/penalize otherwise): an `IMAGE` header + a short
   static body, created via the API (the header example needs a `header_handle` from the
   [Resumable Upload API](https://developers.facebook.com/docs/graph-api/guides/upload)). See
   `scripts`/git history for the exact create call. Get it approved.
5. Generate a **permanent System User token** → `WHATSAPP_TOKEN`.

### 3. Run on GitHub Actions
1. Push to GitHub. Add each `.env.example` variable as a repo secret.
2. Schedules fire at 15:30 & 05:30 UTC (9 PM / 11 AM IST); the workflow installs Chromium +
   an emoji font for rendering. Test via **Actions → WC Notifier → Run workflow**.

## Local testing

```bash
uv sync
uv run playwright install chromium      # one-time
cp .env.example .env                     # fill in values
uv run python main.py preview --dry-run  # renders samples/preview_card.png (no send)
uv run python main.py recap --dry-run
```

To actually send without an approved template: message the bot first (opens a 24h window), set
`WHATSAPP_USE_TEMPLATE=false`, and the image delivers free-form.

## Notes
- **Category:** a sports digest is MARKETING by Meta's definition; that's submitted intentionally.
  Approval is Meta's manual queue (minutes to ~a day on an unverified test account).
- **Data:** ESPN is current and free; scorer/venue fields populate as a match updates.
- **Flags** render as images (flagcdn) so they're correct on any renderer; decorative emoji use a
  color-emoji font (installed in CI).
- **Resilience:** Gemini enrichment retries then degrades — the card still renders from ESPN data
  alone if the LLM is unavailable.
