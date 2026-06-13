# ⚽ FIFA World Cup 2026 — WhatsApp Notifier

Two free, hostless daily WhatsApp messages about WC 2026:

- **🌙 9 PM IST — Tonight's Slate:** what's kicking off overnight (IST), group context, what's at
  stake, star players, fun facts.
- **☀️ 11 AM IST — Morning Recap:** scores + scorers from the matches that finished while you
  slept, updated group standings, and ▶️ YouTube highlight links.

Built to be minimal: a single Python package run by **GitHub Actions cron** — no server, no
Docker. WhatsApp delivery uses the **official Meta Cloud API test number** (no ban risk; free to
your own verified number). Content is written by **Gemini** from live football data.

## How it works

```
GitHub Actions cron ──> python main.py {preview|recap}
                              │
                              └─ src/pipeline.py  (gather → compose → deliver)
                                   ├─ clients/football.py   (football-data.org: fixtures, results, standings)
                                   ├─ clients/youtube.py    (highlight links)
                                   ├─ clients/whatsapp.py   (Meta Cloud API send)
                                   └─ services/content.py   (Gemini → message; prompts/ as .md; fallback)
```

## Project structure

```
fifa-wc/
├── main.py                 # entry point: python main.py {preview|recap}
├── prompts/                # LLM prompts as markdown (system + user per mode)
│   ├── preview/{system,user}.md
│   └── recap/{system,user}.md
└── src/
    ├── config.py           # pydantic-settings (env vars / .env)
    ├── models.py           # Fixture, MatchResult, GroupStanding, TeamStanding
    ├── pipeline.py         # Notifier — orchestration
    ├── log.py
    ├── clients/            # external I/O: football-data.org, WhatsApp, YouTube
    └── services/           # prompt loading + content composition (Gemini)
```

## Setup

### 1. API keys
- **football-data.org** — register for a free key (`FOOTBALL_DATA_API_KEY`).
- **Google AI Studio** — create `GEMINI_API_KEY`.
- **(optional) YouTube Data API** — `YOUTUBE_API_KEY` for direct video links instead of search URLs.

### 2. WhatsApp Cloud API (free, no ban risk)
1. Create a Meta app at developers.facebook.com → add the **WhatsApp** product.
2. Note the **test number's Phone Number ID** (`WHATSAPP_PHONE_NUMBER_ID`).
3. Add **your own number** as a verified recipient (`WHATSAPP_RECIPIENT`, e.g. `9198XXXXXXXX`).
4. Create a **utility message template** named `wc_update` with a single body variable `{{1}}`
   and get it approved. Match `WHATSAPP_TEMPLATE_LANG` to the template's language (e.g. `en_US`).
5. Generate a **permanent System User access token** (the default token expires in 24h and will
   break the daily cron) → `WHATSAPP_TOKEN`.

### 3. Run it on GitHub Actions
1. Push this repo to GitHub.
2. Settings → Secrets and variables → Actions → add every variable from `.env.example`.
3. The schedules in `.github/workflows/notify.yml` fire at 15:30 & 05:30 UTC (9 PM / 11 AM IST).
   Note: GitHub cron can drift 5–30 min under load.
4. Test immediately via **Actions → WC Notifier → Run workflow** (pick `preview` or `recap`).

## Local testing

```bash
uv sync
cp .env.example .env   # fill in values (loaded automatically by pydantic-settings)
uv run python main.py preview
uv run python main.py recap
```

Tip: to test without an approved template, message your bot first (opens a 24h window), set
`WHATSAPP_USE_TEMPLATE=false`, and free-form text will deliver.

## Notes & limits
- **Template formatting:** unprompted messages require a template; body variables may restrict
  newlines/length. If newlines are rejected, the message still sends — keep it compact.
- **Scorers:** football-data.org free tier may omit per-goal scorers; the recap degrades to
  scoreline-only. Set `YOUTUBE_API_KEY` and/or upgrade the data source if you want richer detail.
- **Reliability:** any data/LLM failure degrades to a short fallback message rather than going
  silent.

## Roadmap (Phase 2)
Interactive on-demand commands (`today`, `standings`, `group F`) via a free serverless webhook
(Cloudflare Worker / Vercel) — the only piece that needs an always-on listener, intentionally
kept out of v1.
