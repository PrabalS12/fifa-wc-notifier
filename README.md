# ⚽ FIFA World Cup 2026 — WhatsApp Notifier

Two free, hostless daily WhatsApp messages about WC 2026:

- **🌙 9 PM IST — Tonight's Slate:** matches kicking off overnight (9 PM→11 AM IST), star players,
  form/h2h/stakes one-liner, match-of-the-night, group standings, a fun fact.
- **☀️ 11 AM IST — Morning Recap:** scores + **scorers** (with minutes, pens/OGs) from the matches
  that finished while you slept, updated standings, and ▶️ highlight links.

Each run sends **2 messages** (matches, then a monospace standings table). Minimal by design: a
single Python package run by **GitHub Actions cron** — no server, no Docker. Match data comes from
**ESPN's public API (no key)**; the narrative is written by **Gemini**; delivery uses the **Meta
WhatsApp Cloud API** test number (no ban risk, free to verified numbers).

## How it works

```
GitHub Actions cron ──> python main.py {preview|recap}
                              │
                              └─ src/pipeline.py  (gather → compose → deliver)
                                   ├─ clients/football.py   (ESPN: fixtures, scores, scorers, standings, venues)
                                   ├─ clients/youtube.py    (highlight links)
                                   ├─ clients/whatsapp.py   (Meta Cloud API send — one or more messages)
                                   └─ services/content.py   (Gemini narrative + code-built standings table)
```

## Project structure

```
fifa-wc/
├── main.py                 # entry point: python main.py {preview|recap} [--dry-run]
├── prompts/                # LLM prompts as markdown (system + user per mode)
│   ├── preview/{system,user}.md
│   └── recap/{system,user}.md
└── src/
    ├── config.py           # pydantic-settings (env vars / .env)
    ├── models.py           # Fixture, Goal, MatchResult, GroupStanding, TeamStanding
    ├── pipeline.py         # Notifier — orchestration
    ├── log.py
    ├── clients/            # external I/O: ESPN data, WhatsApp, YouTube
    └── services/           # prompt loading + content composition (Gemini)
```

## Setup

### 1. Keys
- **Google AI Studio** — create `GEMINI_API_KEY` (only required key for content).
- **(optional) YouTube Data API** — `YOUTUBE_API_KEY` for direct highlight-video links instead of
  search URLs.
- Match data: **none** — ESPN's public endpoints need no key.

### 2. WhatsApp Cloud API (free, no ban risk)
1. Create a Meta app at developers.facebook.com → add the **WhatsApp** product → create a business
   portfolio when prompted.
2. Copy the **test number's Phone Number ID** (`WHATSAPP_PHONE_NUMBER_ID`).
3. Add your number(s) as **verified recipients** (`WHATSAPP_RECIPIENT`, comma-separated for several).
4. Create + get approved a **utility template** named `wc_update` whose body wraps a single
   variable, e.g. `⚽\n{{1}}\n_FIFA World Cup 2026_` (a variable cannot be the only content, nor at
   the very start/end). Match `WHATSAPP_TEMPLATE_LANG` to its language (`en_US`).
5. Generate a **permanent System User access token** (the default expires in 24h) → `WHATSAPP_TOKEN`.

### 3. Run it on GitHub Actions
1. Push to GitHub.
2. Settings → Secrets and variables → Actions → add each variable from `.env.example`
   (`GEMINI_API_KEY`, `WHATSAPP_*`, optional `YOUTUBE_API_KEY`/`GEMINI_MODEL`).
3. Schedules in `.github/workflows/notify.yml` fire at 15:30 & 05:30 UTC (9 PM / 11 AM IST).
   GitHub cron can drift 5–30 min under load.
4. Test via **Actions → WC Notifier → Run workflow**.

## Local testing

```bash
uv sync
cp .env.example .env        # fill in values (loaded automatically by pydantic-settings)
uv run python main.py preview --dry-run   # prints the messages instead of sending
uv run python main.py recap --dry-run
```

To send for real without an approved template: message your bot first (opens a 24h window), set
`WHATSAPP_USE_TEMPLATE=false`, and free-form text delivers.

## Notes & limits
- **Template wrapper:** unprompted messages must use a template; its static wrapper appears on each
  message. Keep it minimal (see step 4).
- **Data:** ESPN provides scores, scorers, standings, and venues, current and free. Scorer/venue
  fields populate as ESPN updates a match.
- **Resilience:** Gemini calls retry transient errors, then fall back to a plain (still formatted)
  layout so a message always goes out.

## Roadmap (Phase 2)
Interactive on-demand commands (`today`, `standings`, `group F`) via a free serverless webhook —
the only piece that needs an always-on listener, intentionally kept out of v1. Direct YouTube
highlight videos via the YouTube Data API key.
