# Prod TSE Investigation Dashboard - Getting Started

## What Is This?

A structured workspace for Technical Support Engineers (TSEs) to investigate customer cases using [Cursor AI](https://cursor.com) with direct access to Zendesk, JIRA, Confluence, GitHub, and internal Datadog knowledge via MCP (Model Context Protocol).

**Key advantage:** Instead of manually switching between Zendesk, JIRA, Confluence, GitHub, and Slack to piece together context, Cursor AI fetches and analyzes everything for you in one place.

---

## Prerequisites

Before you begin, make sure you have the following installed:

| Requirement | Minimum Version | Check Command |
|---|---|---|
| **Python** | 3.9+ | `python3 --version` |
| **Git** | Any recent | `git --version` |
| **Cursor** | Latest | [Download Cursor](https://cursor.com) |

### Optional (for advanced features)

| Requirement | Purpose | Install |
|---|---|---|
| **uv** | MCP server runtime | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **ffmpeg** | Zoom call audio transcription (Whisper) | `brew install ffmpeg` |
| **OpenAI API key** | Transcript summarisation & escalation generation | [Get API key](https://platform.openai.com/api-keys) |

---

## Setup (5 minutes)

### 1. Clone and open in Cursor

```bash
git clone https://github.com/patrickoddatadog/prod-tse-investigation-dashboard.git
cd prod-tse-investigation-dashboard
```

Open the folder in [Cursor](https://cursor.com):

```bash
cursor .
```

Or use **File > Open Folder** and select the `prod-tse-investigation-dashboard` directory.

### 2. Tell Cursor: "Set me up"

That's it. The Cursor rules and MCP configuration handle the rest. On first use, the workspace configures:

- **Atlassian (JIRA + Confluence)** -- uses SSO, no token needed
- **Glean (Slack, internal docs)** -- uses SSO, no token needed
- **GitHub (optional)** -- needs a [PAT](https://github.com/settings/tokens?type=beta) with `Contents` + `Metadata` read permissions; authorize SSO for the DataDog org

### 3. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
# Zendesk Configuration
ZENDESK_SUBDOMAIN=yourcompany
ZENDESK_EMAIL=your.email@company.com
ZENDESK_API_TOKEN=paste_your_zendesk_token_here

# Atlassian Configuration (JIRA & Confluence)
ATLASSIAN_DOMAIN=yourcompany.atlassian.net
ATLASSIAN_EMAIL=your.email@company.com
ATLASSIAN_API_TOKEN=paste_your_atlassian_token_here

# JIRA Project Configuration
JIRA_PROJECT_KEY=SCRS

# GitHub Configuration (optional — for code research)
GITHUB_TOKEN=paste_your_github_token_here

# OpenAI Configuration (optional — for transcript summarisation)
OPENAI_API_KEY=paste_your_openai_api_key_here
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs: Flask, python-dotenv, markdown, pygments, openai-whisper, and openai.

### 5. Restart Cursor

Quit completely (**Cmd+Q**), then reopen the workspace. Atlassian and Glean will prompt a one-time SSO login on first use.

### 6. Test it

Ask Cursor:

> "Investigate ZD-2337222"

If you get results, you're all set.

---

## What You Can Do

| Goal | What to say in Cursor |
|---|---|
| Investigate a ticket | `"Investigate Zendesk ticket ZD-2488538"` |
| Search escalations | `"Search JIRA for APM memory leak issues"` |
| Find internal docs | `"Search Confluence for agent troubleshooting"` |
| Search code | `"Search dd-trace-py for this error message"` |
| Search everything | `"Search Glean for recent security product updates"` |
| Draft a response | `"Draft a customer response for this case"` |
| Prepare for a Zoom call | `"Prepare a Zoom call agenda for ZD-12345"` |
| Create an escalation | `"Create JIRA escalation for ZD-12345"` |

---

## Workspace Structure

```
prod-tse-investigation-dashboard/
├── .cursor/
│   ├── rules/               # AI behavior rules (investigation, comms, escalation)
│   ├── hooks/                # Auto-checks for pending transcripts & escalations
│   ├── hooks.json            # Hook configuration
│   └── skills/              # Reusable investigation skills
│       ├── _shared/          # Shared utilities (Zendesk API helper)
│       └── zendesk-ticket/   # Ticket investigation, classification, attachments, pool
├── app.py                    # POD Ticket Dashboard (Flask web app)
├── cases/                    # Active customer cases (gitignored)
│   ├── .template/            # Template for new case folders
│   └── ZD-XXXXXX/            # One folder per Zendesk ticket
│       ├── notes.md           # Investigation notes (all tabs rendered from this)
│       └── assets/            # Logs, screenshots, recordings
├── archive/                  # Resolved cases by month (gitignored)
├── docs/                     # Escalation criteria, product docs
├── templates/                # Customer communication & escalation templates
│   ├── customer-communication/
│   └── escalation/
├── scripts/                  # CLI tools & utilities
│   ├── jira_client.py         # JIRA search & escalation creation
│   ├── zendesk_client.py      # Zendesk CLI tool
│   ├── zendesk_mcp_server.py  # Zendesk MCP server
│   ├── transcribe.py          # Whisper transcription for Zoom recordings
│   └── start-server.sh        # Auto-restart wrapper for the web dashboard
├── reference/                # JIRA project codes, reference materials
├── web/                      # Web dashboard templates & static assets
│   ├── templates/             # Jinja2 HTML templates
│   └── static/                # CSS
├── requirements.txt
├── .env.example              # Template for environment variables
└── .gitignore                # Protects customer data from being committed
```

---

## POD Ticket Dashboard (Local Web UI)

The workspace includes a browser-based dashboard for visualizing investigations without using the terminal. It's entirely optional — the workspace works fully through Cursor alone.

### Start the dashboard

```bash
# Option 1: Direct
python3 app.py

# Option 2: Auto-restart wrapper
./scripts/start-server.sh
```

Then open: **http://localhost:8501**

### Dashboard features

- **Case list** with status, priority, customer, and product area filters
- **Case detail** with tabbed views:
  - **Overview** -- issue summary and proposed customer response
  - **Investigation Notes** -- full notes rendered from `notes.md`
  - **Zoom Call** -- call preparation agenda
  - **Zoom Call Transcript** -- upload audio, auto-transcribe with Whisper, summarise with OpenAI
  - **Leadership Summary** -- non-technical summary for managers
  - **TLDR Handover** -- technical handover for other TSEs
  - **Escalation** -- generate JIRA-ready escalation summaries with one click
- **Known Issues** -- centralized list of tracked bugs and workarounds
- **Archive** -- searchable resolved cases by month
- **Docs** -- escalation criteria and product documentation
- **Comms Templates** -- customer communication templates

---

## Investigation Workflow

### Starting a case

**Option 1: Ask Cursor** (recommended)

> "Investigate Zendesk ticket 12345"

Cursor will:
1. Fetch the ticket via Glean
2. Search for similar historical cases
3. Check known issues
4. Create a case folder in `cases/ZD-12345/`
5. Generate investigation notes with all mandatory sections

**Option 2: Manual**

```bash
cp -r cases/.template cases/ZD-12345
```

### During investigation

- Ask Cursor to search Confluence, JIRA, GitHub, or Glean for context
- Drop logs, screenshots, and recordings into `cases/ZD-12345/assets/`
- Document findings in `notes.md` -- the dashboard renders each `##` section as a separate tab
- Use templates from `templates/customer-communication/` for responses

### Zoom call recording workflow

1. Upload an audio/video file via the dashboard's Zoom Call Transcript tab
2. Whisper automatically transcribes the recording
3. Click **Summarise** to generate a structured summary via OpenAI
4. The summary appears in `notes.md` and the dashboard

### Escalation workflow

1. Complete your investigation and document findings in `notes.md`
2. Mark escalation in the Escalation Notes section: `[x] Yes`
3. Open the Escalation tab in the dashboard and click **Generate Escalation Summary**
4. Review the generated JIRA-ready summary
5. Create the JIRA ticket: ask Cursor `"Create JIRA escalation for ZD-12345"`

### Archiving a resolved case

```bash
python3 scripts/zendesk_client.py archive 12345
```

---

## Cursor Rules & Hooks

The workspace ships with pre-configured AI rules that shape Cursor's behavior:

| Rule | Purpose |
|---|---|
| `investigation-workflow` | Step-by-step process for investigating tickets |
| `mandatory-outputs` | Ensures all required sections exist in `notes.md` |
| `customer-communication` | Brief-first tone, template usage |
| `escalation-criteria` | When and how to escalate |
| `risk-assessment` | Rollback/risk checklist for config change recommendations |
| `zoom-transcript` | Auto-summarisation pipeline for call recordings |
| `api-access-constraints` | Read/write boundaries for each external service |
| `tse-context` | Role context and workspace layout |
| `output-standards` | File structure and customer data protection |

### Hooks

Session hooks run automatically to catch pending work:

- **On session start:** Checks for unsummarised transcripts and pending escalation summaries
- **On stop:** Ensures the agent doesn't end a session with pending transcript summarisation

---

## API Access Summary

| Service | Default Access | Notes |
|---|---|---|
| **Glean** | Read | Searches Zendesk, Slack, internal docs |
| **Atlassian (JIRA)** | Read; Write for escalations | Confirm before creating JIRA tickets |
| **Atlassian (Confluence)** | Read | Internal documentation |
| **GitHub** | Read-only | Code research only -- never creates branches, PRs, or issues |
| **Slack** | Via Glean search | Never access Slack URLs directly; use Glean instead |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "I don't have access to JIRA" | Restart Cursor (Cmd+Q), SSO will re-prompt |
| GitHub not working | Token expired -- tell Cursor `"reconfigure my workspace"` |
| Cursor slow on first open | Wait for indexing to finish |
| MCP not loading | Verify `.cursor/mcp.json` exists; check `uvx --version`; restart Cursor |
| Zendesk 401 errors | Regenerate your API token in Zendesk Admin |
| Zendesk 403 errors | Ensure you're using an API token, not OAuth |
| Zendesk 429 errors | Rate limited -- wait 60 seconds |
| Dashboard won't start | Check `python3 --version` (need 3.9+); check port 8501 isn't in use |
| Whisper transcription fails | Ensure `ffmpeg` is installed: `brew install ffmpeg` |
| OpenAI summarisation fails | Verify `OPENAI_API_KEY` is set in `.env` |

For anything else: tell Cursor `"Help me troubleshoot my MCP setup"`

---

## Customer Data Safety

- All `cases/` folders are **gitignored** -- customer data never leaves your machine
- All `archive/` folders are **gitignored**
- `.env` credentials are **gitignored**
- Never commit customer data, logs, screenshots, or PII
- The workspace is designed so only templates, rules, scripts, and documentation are version-controlled

---

## Need Help?

- **Ask Cursor** -- it knows how the workspace works and can self-diagnose issues
- **Slack:** #support-team
- **Repo:** [github.com/patrickoddatadog/prod-tse-investigation-dashboard](https://github.com/patrickoddatadog/prod-tse-investigation-dashboard)
