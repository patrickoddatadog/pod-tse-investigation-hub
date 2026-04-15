# POD TSE Investigation Hub

AI-powered investigation workspace for Technical Support Engineers at Datadog. Combines [Cursor AI](https://cursor.com) with MCP integrations (Glean, JIRA, Confluence, GitHub) and a local web dashboard to streamline ticket investigation, customer communication, and engineering escalation.

> **New here?** Follow the **[Setup Guide](SETUP.md)** (5 minutes) or jump to **[Quick Start](QUICK_START.md)**.

---

## Quick Start

```bash
# 1. Clone and open in Cursor
git clone https://github.com/patrickoddatadog/pod-tse-investigation-hub.git
cd pod-tse-investigation-hub
cursor .

# 2. Set up credentials
cp .env.example .env
# Edit .env with your Zendesk, Atlassian, GitHub, and OpenAI tokens

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Restart Cursor (Cmd+Q, reopen)
# Atlassian and Glean use SSO — they'll prompt on first use
```

Then ask Cursor:
> "Investigate Zendesk ticket 2864882"

---

## What It Does

| Capability | How |
|---|---|
| **Investigate tickets** | Ask Cursor to investigate any Zendesk ticket — it fetches context via Glean, searches for similar cases, and creates structured investigation notes |
| **Web dashboard** | Local Flask app at `localhost:8501` with tabbed case views (overview, investigation, Zoom prep, leadership summary, handover, escalation) |
| **Zoom transcription** | Upload call recordings — Whisper transcribes, OpenAI summarises for a technical audience |
| **Auto-generated outputs** | Every investigation produces a customer response draft, Zoom prep, leadership summary, TLDR handover, and escalation summary |
| **One-click escalation** | Generate JIRA-ready escalation summaries from investigation notes |
| **Customer communication** | Pre-built templates for acknowledgments, info requests, solutions, escalation notices |

---

## Structure

```
pod-tse-investigation-hub/
├── .cursor/
│   ├── rules/                # AI behavior rules (9 rules)
│   ├── hooks/                # Session hooks (transcript & escalation checks)
│   ├── skills/               # Investigation skills (investigator, classifier, pool, attachments)
│   └── hooks.json
├── app.py                    # POD Ticket Dashboard (Flask)
├── cases/                    # Active cases (gitignored)
│   ├── .template/            # Template for new case folders
│   └── ZD-XXXXXX/            # One folder per ticket
├── archive/                  # Resolved cases (gitignored)
├── templates/                # Customer communication & escalation templates
├── docs/                     # Escalation criteria, product docs
├── scripts/                  # CLI tools (JIRA, Zendesk, transcription, server)
├── web/                      # Dashboard HTML templates & CSS
├── reference/                # JIRA project codes
├── requirements.txt
└── .env.example
```

See [STRUCTURE.md](STRUCTURE.md) for the full breakdown of every file.

---

## POD Ticket Dashboard

Local web UI for visualizing investigations. Optional — the workspace works fully through Cursor alone.

```bash
python3 app.py
# or
./scripts/start-server.sh
```

Then open **http://localhost:8501**.

**Dashboard tabs** (each renders a `##` section from `notes.md`):
- **Overview** — issue summary and proposed customer response
- **Investigation Notes** — full investigation documentation
- **Zoom Call** — call preparation agenda
- **Zoom Call Transcript** — upload audio, auto-transcribe, summarise
- **Leadership Summary** — non-technical summary for managers
- **TLDR Handover** — technical handover for other TSEs
- **Escalation** — generate JIRA-ready escalation summaries

---

## Investigation Workflow

**Ask Cursor:**
> "Investigate Zendesk ticket 12345"

Cursor will:
1. Fetch the ticket via Glean
2. Search for similar historical cases in JIRA, Confluence, and the archive
3. Create a case folder in `cases/ZD-12345/`
4. Generate `notes.md` with all mandatory sections

**During investigation:**
- Ask Cursor to search Confluence, JIRA, GitHub, Glean, or Slack (via Glean)
- Drop logs, screenshots, recordings into `cases/ZD-12345/assets/`
- Document findings in `notes.md` — the dashboard renders each section as a tab

**Zoom call workflow:**
1. Upload audio via the dashboard's Zoom Call Transcript tab
2. Whisper transcribes automatically
3. Click **Summarise** for an OpenAI-generated structured summary

**Escalation workflow:**
1. Document findings in `notes.md`
2. Click **Generate Escalation Summary** on the Escalation tab
3. Ask Cursor: `"Create JIRA escalation for ZD-12345"`

---

## Cursor Rules, Skills & Hooks

### Rules (`.cursor/rules/`)

| Rule | Purpose |
|------|---------|
| `investigation-workflow` | Step-by-step investigation process |
| `mandatory-outputs` | Ensures all required sections in `notes.md` |
| `customer-communication` | Brief-first tone, template usage |
| `escalation-criteria` | When and how to escalate |
| `risk-assessment` | Rollback/risk checklist for config changes |
| `zoom-transcript` | Auto-summarisation pipeline |
| `api-access-constraints` | Read/write boundaries per service |
| `tse-context` | Role context and workspace layout |
| `output-standards` | File structure and data protection |

### Skills (`.cursor/skills/`)

| Skill | Purpose |
|-------|---------|
| `investigator` | Full end-to-end ticket investigation |
| `classifier` | Ticket classification and routing |
| `attachment-downloader` | Download Zendesk ticket attachments |
| `pool` | Ticket pool management |

### Hooks

Session hooks run automatically to flag unsummarised transcripts and pending escalation summaries.

---

## API Access

| Service | Access | Auth |
|---------|--------|------|
| **Glean** | Read (Zendesk, Slack, internal docs) | SSO |
| **Atlassian (JIRA)** | Read; Write for escalations | SSO |
| **Atlassian (Confluence)** | Read | SSO |
| **GitHub** | Read-only (code research) | PAT (optional) |
| **Slack** | Via Glean search | SSO |

---

## Customer Data Safety

- All `cases/` and `archive/` folders are **gitignored** — customer data never leaves your machine
- `.env` credentials are **gitignored**
- Only templates, rules, scripts, and documentation are version-controlled
- Never commit customer data, logs, screenshots, or PII

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| JIRA/Confluence not working | Restart Cursor (Cmd+Q) — SSO will re-prompt |
| GitHub not working | Regenerate PAT |
| Zendesk 401/403 | Regenerate API token in Zendesk Admin |
| Dashboard won't start | Check `python3 --version` (need 3.9+); check port 8501 |
| Whisper fails | Install ffmpeg: `brew install ffmpeg` |
| OpenAI summarisation fails | Check `OPENAI_API_KEY` in `.env` |

---

## Contributing

1. Improve templates and rules
2. Create anonymized troubleshooting docs from resolved cases
3. Enhance the dashboard or scripts
4. Keep documentation updated

See [GIT_STRATEGY.md](GIT_STRATEGY.md) for what to commit and what to keep local.

---

## Documentation

- **[SETUP.md](SETUP.md)** — Full setup guide (prerequisites, environment, MCP)
- **[QUICK_START.md](QUICK_START.md)** — Quick reference for daily use
- **[STRUCTURE.md](STRUCTURE.md)** — Complete directory and file breakdown
- **[GIT_STRATEGY.md](GIT_STRATEGY.md)** — What to commit / not commit
- **[GITHUB_SETUP.md](GITHUB_SETUP.md)** — Repository management and push workflow
- **[docs/escalation-criteria.md](docs/escalation-criteria.md)** — When to escalate to Engineering

---

**Questions?** Ask Cursor — it knows how the workspace works. Or reach out in #support-team.
