---
name: zendesk-ticket-investigator
description: Investigate a Zendesk ticket by reading its content, searching for similar past tickets, checking internal docs, and gathering customer context. Use when the user mentions investigate ticket, look into ticket, ticket investigation, analyze ticket, or provides a Zendesk ticket number to investigate.
---

# Ticket Investigator

Deep investigation skill for a specific Zendesk ticket. Reads the ticket, searches for similar past cases, checks internal documentation, gathers customer context, and writes a structured investigation report.

Can be used standalone or triggered by the user during an investigation workflow.

## How to Use

Just say: **"investigate ticket #1234567"** or **"look into ZD-1234567"**

The agent will:
1. Read the ticket from Zendesk via Glean
2. Search for similar resolved tickets
3. Search internal docs (Confluence)
4. Look up customer context (Salesforce)
5. Write case files to `cases/ZD-{id}/` (README.md, notes.md, response.md, meta.json)

## When This Skill is Activated

If an agent receives a message matching any of these patterns:
- "investigate ticket #XYZ"
- "look into ticket XYZ"
- "analyze ZD-XYZ"
- "what's ticket #XYZ about?"

Then:
1. Extract the ticket ID from the message
2. **Run the AI Compliance Check below FIRST**
3. Follow the steps in `investigate-prompt.md` in this folder
4. Write case files to `cases/ZD-{TICKET_ID}/`

## AI Compliance Check (MANDATORY — FIRST STEP)

**Before processing ANY ticket data**, check for the `oai_opted_out` tag:

```bash
.cursor/skills/_shared/zd-api.sh ticket {TICKET_ID}
```

If the output contains `ai_optout:true`:
1. **STOP IMMEDIATELY** — do NOT process ticket data through the LLM
2. Do NOT generate any analysis, investigation, or report
3. Tell the user: **"Ticket #{TICKET_ID}: AI processing is blocked — this customer has opted out of GenAI (oai_opted_out). Handle manually without AI."**
4. Exit the skill

This is a legal/compliance requirement. No exceptions.

## Investigation Steps

1. **Read ticket** — Full content via Chrome JS (real-time) or Glean fallback (`user-glean_ai-code-read_document`)
2. **Download attachments** — List and download attachments via Chrome JS (flares, logs, screenshots). Flares are extracted to `cases/ZD-{id}/assets/flare/` and analyzed directly (status.log, config-check.log, etc.).
2.5. **Local knowledge base** — Search `solutions/known-issues.md` and `archive/` for matching patterns before going external
3. **Similar tickets** — Search Zendesk for resolved tickets with matching symptoms
4. **Internal docs** — Search Confluence for runbooks, troubleshooting guides, known issues
5. **Public docs** — Search docs.datadoghq.com for relevant product documentation
6. **GitHub code** — Search DataDog GitHub repos for config parameters, error messages, source code
7. **Customer context** — Search Salesforce for org tier, MRR, top75, recent escalations
8. **Write case** — Create `cases/ZD-{id}/` with README.md, notes.md, response.md, meta.json, and assets/

## Reference Sources

### Public Documentation
- https://docs.datadoghq.com — Main doc site (agent, logs, APM, infra, containers, etc.)

### Key GitHub Repositories
| Repo | What |
|------|------|
| [datadog-agent](https://github.com/DataDog/datadog-agent) | Core agent, config parameters, checks |
| [integrations-core](https://github.com/DataDog/integrations-core) | Official integration checks |
| [integrations-extras](https://github.com/DataDog/integrations-extras) | Community integrations |
| [helm-charts](https://github.com/DataDog/helm-charts) | Kubernetes Helm charts |
| [datadog-operator](https://github.com/DataDog/datadog-operator) | Kubernetes operator |
| [documentation](https://github.com/DataDog/documentation) | Source for docs.datadoghq.com |

### APM Tracers
| Language | Repo |
|----------|------|
| Python | [dd-trace-py](https://github.com/DataDog/dd-trace-py) |
| Java | [dd-trace-java](https://github.com/DataDog/dd-trace-java) |
| Node.js | [dd-trace-js](https://github.com/DataDog/dd-trace-js) |
| Go | [dd-trace-go](https://github.com/DataDog/dd-trace-go) |
| .NET | [dd-trace-dotnet](https://github.com/DataDog/dd-trace-dotnet) |
| Ruby | [dd-trace-rb](https://github.com/DataDog/dd-trace-rb) |

### Agent Config Parameters
Key files for parameter lookup in `datadog-agent`:
- `pkg/config/setup/config.go` — All config parameters with defaults
- `cmd/agent/dist/datadog.yaml` — Default config template
- `comp/core/config/` — Config component

### Internal Documentation
- Confluence — Runbooks, troubleshooting guides, known issues
- Salesforce — Customer tier, MRR, top75, escalation history

## Output

Case files are saved to `cases/ZD-{TICKET_ID}/` in the workspace root:

| File | Purpose |
|------|---------|
| `README.md` | Quick reference card (ticket metadata, environment, links, related cases) |
| `notes.md` | Investigation timeline with timestamped entries |
| `response.md` | Customer response draft with TL;DR, response text, and internal notes |
| `meta.json` | Machine-readable metadata (`status`, `assignee`, `priority`, `issue_type`) |
| `assets/` | Downloaded attachments (flares, logs, screenshots) |
| `assets/flare/` | Extracted flare contents (when applicable) |

The TSE Hub web dashboard at `http://localhost:5099` automatically reads these files and displays the case.

**Timeline entries** (appended on each investigation):
- Timestamped sections: `### YYYY-MM-DD HH:MM — Initial Investigation (Agent)`
- Each entry contains: problem summary, key details, attachments, similar tickets, docs, assessment
- Re-investigations append new entries without overwriting previous ones

**`meta.json` status** is kept in sync with the Investigation Decision:
- `ready_to_review` / `investigation` / `reproduction` → `"status": "investigating"`
- `waiting` → `"status": "waiting-on-customer"`

## Attachment Downloads

Attachments are downloaded via `osascript` + Chrome JS (using `.cursor/skills/_shared/zd-api.sh`). Downloads land in `~/Downloads/` first, then are moved to `cases/ZD-{id}/assets/`.

**Prerequisites:** Chrome must be running with a Zendesk tab open and "Allow JavaScript from Apple Events" enabled (one-time setup — see `zendesk-attachment-downloader/SKILL.md`).

When a flare `.zip` is found, the investigator will:
1. Download and move it to `cases/ZD-{id}/assets/`
2. Extract to `cases/ZD-{id}/assets/flare/`
3. Analyze `status.log`, `config-check.log`, `diagnose.log`, and other relevant files directly
4. Include flare findings in the investigation report

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — skill definition |
| `investigate-prompt.md` | Step-by-step investigation prompt template |
