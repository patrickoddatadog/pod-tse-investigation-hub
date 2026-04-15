Investigate Zendesk ticket #{{TICKET_ID}} (Subject: {{SUBJECT}}).

## Step 0: AI Compliance Check (MANDATORY)

```bash
.cursor/skills/_shared/zd-api.sh ticket {{TICKET_ID}}
```

If the output contains `ai_optout:true`, **STOP NOW**. Tell the user: "Ticket #{{TICKET_ID}}: AI processing is blocked — this customer has opted out of GenAI (oai_opted_out). Handle manually without AI." Do NOT proceed to any further steps.

## Step 1: Read the ticket

### Primary: Chrome JS (real-time)

```bash
.cursor/skills/_shared/zd-api.sh read {{TICKET_ID}} 0
```

This returns ticket metadata (filtered tags) + all comments (full body with `0`). For triage-only, omit `0` to get 500-char truncated comments.

### Fallback: Glean MCP

If Chrome is unavailable (ERROR output):
- Tool: user-glean_ai-code-read_document
- urls: ["https://datadog.zendesk.com/agent/tickets/{{TICKET_ID}}"]

Extract: customer name, org, priority, full problem description, any error messages or logs shared.
Identify the **product area** (agent, logs, APM, infra, NDM, DBM, containers, etc.) for later searches.

## Step 2: Download and analyze attachments

Use the `zendesk-attachment-downloader` skill to list and download attachments from the ticket.

### 2a: List attachments

```bash
.cursor/skills/_shared/zd-api.sh attachments {{TICKET_ID}}
```

If `ERROR: No Zendesk tab found in Chrome`: Skip attachment download and note "Chrome not available for attachment download" in the report. Continue to Step 3.
If `NO_ATTACHMENTS`: Note in the report. Continue to Step 3.

### 2b: Download agent flares

If any attachment filename matches `datadog-agent-*.zip`:

1. Download it:
```bash
.cursor/skills/_shared/zd-api.sh download '{CONTENT_URL}' '{FILENAME}'
```

2. Wait for download and move to case assets:
```bash
sleep 3
mkdir -p cases/ZD-{{TICKET_ID}}/assets/flare
mv ~/Downloads/{FLARE_FILENAME} cases/ZD-{{TICKET_ID}}/assets/
unzip -o cases/ZD-{{TICKET_ID}}/assets/{FLARE_FILENAME} -d cases/ZD-{{TICKET_ID}}/assets/flare/
```

3. Find the flare root:
```bash
find cases/ZD-{{TICKET_ID}}/assets/flare -name "status.log" -maxdepth 3
```

4. Analyze the flare:
   - Read `status.log` for agent version, running checks, errors, and warnings
   - If the ticket mentions **network issues** → check `netstat.log`, `connectivity.log`, `route.log` in the flare
   - If the ticket mentions **high resource usage** → check `expvar.log`, `runtime_config_dump.yaml`
   - For general issues → scan `config-check.log` and `diagnose.log`

5. Include flare findings in the investigation report under the "Flare Analysis" section.

### 2c: Download other attachments (optional)

Download screenshots, log files, or config files if they appear relevant to the investigation. Note their filenames in the report.

Clean up temp files:
```bash
rm -f /tmp/zd_list_attachments.scpt /tmp/zd_download.scpt
```

## Step 2.5: Check local knowledge base

Before searching external sources, check the workspace's own knowledge:

1. Search `solutions/known-issues.md` for matching product/symptoms:
```bash
rg -i "KEYWORD1|KEYWORD2" solutions/known-issues.md
```

2. Search `archive/` for similar historical cases:
```bash
rg -ril "KEYWORD1|KEYWORD2" archive/
```

3. If matches found, read the relevant files and reference them in the report under "Local Knowledge Base Matches". These are trusted — they come from previously resolved cases and confirmed known issues.

Use the product area and key error messages/symptoms from Step 1 as keywords.

## Step 3: Search for similar past tickets
- Tool: user-glean_ai-code-search
- query: keywords from the ticket subject/description
- app: zendesk

Look for resolved tickets with similar symptoms. Note ticket IDs and solutions.

## Step 3: Search internal documentation
- Tool: user-glean_ai-code-search
- query: relevant product/feature keywords
- app: confluence

Look for runbooks, troubleshooting guides, known issues, escalation paths.

## Step 4: Search public documentation
- Tool: user-glean_ai-code-search
- query: relevant product/feature keywords
- app: glean help docs

Also check the public docs site directly if needed:
- Tool: user-glean_ai-code-read_document
- urls: ["https://docs.datadoghq.com/RELEVANT_PATH"]

Key doc paths by product area:
| Product | Doc URL |
|---------|---------|
| Agent | https://docs.datadoghq.com/agent/ |
| Logs | https://docs.datadoghq.com/logs/ |
| APM / Tracing | https://docs.datadoghq.com/tracing/ |
| Infrastructure | https://docs.datadoghq.com/infrastructure/ |
| NDM / SNMP | https://docs.datadoghq.com/network_monitoring/devices/ |
| DBM | https://docs.datadoghq.com/database_monitoring/ |
| Containers | https://docs.datadoghq.com/containers/ |
| Cloud Integrations | https://docs.datadoghq.com/integrations/ |
| Metrics | https://docs.datadoghq.com/metrics/ |
| Monitors | https://docs.datadoghq.com/monitors/ |
| Security | https://docs.datadoghq.com/security/ |

## Step 5: Search GitHub code & config parameters
Search the Datadog GitHub repos for relevant code, config parameters, or error messages.

- Tool: user-glean_ai-code-search
- query: error message or config parameter name
- app: github

Key GitHub repositories:
| Repo | URL | What it contains |
|------|-----|-----------------|
| datadog-agent | https://github.com/DataDog/datadog-agent | Core agent code, config parameters, checks |
| integrations-core | https://github.com/DataDog/integrations-core | Official integration checks (Python) |
| integrations-extras | https://github.com/DataDog/integrations-extras | Community integrations |
| documentation | https://github.com/DataDog/documentation | Source for docs.datadoghq.com |
| datadog-api-client-go | https://github.com/DataDog/datadog-api-client-go | Go API client |
| datadog-api-client-python | https://github.com/DataDog/datadog-api-client-python | Python API client |
| helm-charts | https://github.com/DataDog/helm-charts | Helm charts for K8s deployment |
| datadog-operator | https://github.com/DataDog/datadog-operator | Kubernetes operator |
| dd-trace-py | https://github.com/DataDog/dd-trace-py | Python APM tracer |
| dd-trace-java | https://github.com/DataDog/dd-trace-java | Java APM tracer |
| dd-trace-js | https://github.com/DataDog/dd-trace-js | Node.js APM tracer |
| dd-trace-rb | https://github.com/DataDog/dd-trace-rb | Ruby APM tracer |
| dd-trace-go | https://github.com/DataDog/dd-trace-go | Go APM tracer |
| dd-trace-dotnet | https://github.com/DataDog/dd-trace-dotnet | .NET APM tracer |

For config parameter lookup, key files in datadog-agent:
| File | What it contains |
|------|-----------------|
| `pkg/config/setup/config.go` | All agent config parameters with defaults |
| `cmd/agent/dist/datadog.yaml` | Default config template |
| `comp/core/config/` | Config component code |
| `pkg/logs/` | Logs agent code |
| `pkg/collector/` | Check collector code |

To search a specific repo for a parameter or error:
- Tool: user-github-search_code or user-github-2-search_code
- q: "parameter_name repo:DataDog/datadog-agent"

**IMPORTANT — Always build full GitHub links:**
When you find relevant code files, ALWAYS construct a clickable GitHub URL in the report using this format:
```
https://github.com/DataDog/{REPO}/blob/main/{FILE_PATH}
```
Example: if you find `_get_replication_role()` in `integrations-core/postgres/datadog_checks/postgres/postgres.py`, write:
```markdown
- [`postgres.py → _get_replication_role()`](https://github.com/DataDog/integrations-core/blob/main/postgres/datadog_checks/postgres/postgres.py) — Determines replication role via `SELECT pg_is_in_recovery()`
```
NEVER reference code files as plain text without a link. The TSE needs to click through to read the actual source.

## Step 6: Customer context
- Tool: user-glean_ai-code-search
- query: customer org name
- app: salescloud

Check for customer tier, MRR, top75 status, recent escalations.

## Step 7: Write investigation report

The investigation produces a **case directory** at `cases/ZD-{{TICKET_ID}}/` with multiple files that the TSE Hub web dashboard reads. This replaces the old single-file approach.

### 7a: Check if the case already exists

```bash
ls cases/ZD-{{TICKET_ID}}/notes.md 2>/dev/null
```

### 7b: If the case does NOT exist — create the full case structure

Create the directory and all files:

```bash
mkdir -p cases/ZD-{{TICKET_ID}}/assets
```

**File 1: `cases/ZD-{{TICKET_ID}}/meta.json`** — Case metadata for the dashboard:

```json
{
  "status": "investigating",
  "assignee": "",
  "priority": "PRIORITY_FROM_TICKET"
}
```

Map the Zendesk priority tag to one of: `low`, `normal`, `high`, `urgent`. If no priority tag, use `normal`.

**File 2: `cases/ZD-{{TICKET_ID}}/README.md`** — Quick reference card:

```markdown
# Case: ZD-{{TICKET_ID}}

## Quick Info

| Field | Value |
|-------|-------|
| **Zendesk ID** | ZD-{{TICKET_ID}} |
| **Customer** | ORG_NAME |
| **Product Area** | PRODUCT_AREA |
| **Priority** | PRIORITY |
| **Status** | STATUS |
| **Assigned TSE** | (leave blank) |
| **Started** | YYYY-MM-DD |

---

## Issue Summary

**What's Happening:**
(Brief description from ticket)

**Customer Impact:**
(How this affects their business)

---

## Environment

- **Datadog Agent:** (version if known)
- **Host OS:** (if known)
- **Deployment Method:** (Docker, K8s, VM, etc. if known)

---

## Investigation Links

- **Zendesk Ticket:** https://datadog.zendesk.com/agent/tickets/{{TICKET_ID}}
- **Related JIRA:** (if any found)

---

## Related Cases

- **Similar Historical Cases:**
  (list from investigation, or "None found")

- **Related Known Issues:**
  (matches from solutions/known-issues.md, or "None found")

---

**Last Updated:** YYYY-MM-DD
```

**File 3: `cases/ZD-{{TICKET_ID}}/notes.md`** — Investigation timeline:

```markdown
# Investigation Notes: ZD-{{TICKET_ID}}

## Ticket Summary
| Field | Value |
|-------|-------|
| **Customer** | ORG_NAME |
| **Priority** | PRIORITY |
| **Status** | STATUS |
| **Product** | PRODUCT_AREA |
| **Tier** | TIER |
| **MRR** | MRR_RANGE |
| **Complexity** | COMPLEXITY |
| **Type** | ISSUE_TYPE |
| **Created** | CREATED_DATE |

---

## Timeline

### YYYY-MM-DD HH:MM — Initial Investigation (Agent)

**Problem Summary**
(2-3 sentences describing the issue)

**Key Details**
- Error messages, logs, config snippets from the ticket

**Attachments**
| File | Size | Type | Notes |
|------|------|------|-------|
| filename | size MB | type | downloaded / analyzed / skipped |

**Flare Analysis** _(if applicable)_
- Hostname:
- Agent version:
- Key findings from status.log

**Similar Past Tickets**
| Ticket | Subject | Resolution |
|--------|---------|------------|
| #ID | subject | how it was resolved |

**Local Knowledge Base Matches**
- Known issues: (matches from solutions/known-issues.md, or "No matches")
- Historical cases: (matches from archive/, or "No matches")

**Relevant Documentation**
- Public: [Doc title](https://docs.datadoghq.com/...) - brief description
- Internal: [Doc title](confluence_url) - brief description

**Relevant Code**
- [`file.py → function_name()`](https://github.com/DataDog/REPO/blob/main/path/to/file.py) — what this code does

_(Every code reference MUST include a clickable GitHub link. Never write file names as plain text.)_

**Initial Assessment**
- Category: (agent, logs, APM, infra, etc.)
- Likely cause:
- Suggested first steps:
  1. ...
  2. ...
  3. ...
```

At the end of `notes.md`, ALWAYS include the Investigation Decision:

```markdown

## Investigation Decision
- Next: <ready_to_review|waiting|reproduction|investigation>
- Reason: <one-line explanation of why this is the right next step>
```

Rules for Next:
- **"ready_to_review"** — investigation is complete and a response can be drafted for the customer
- **"waiting"** — need more info from the customer before proceeding
- **"reproduction"** — need to reproduce the issue in a test environment
- **"investigation"** — need more investigation time (e.g. waiting on internal research, flare analysis pending)

**Also update `meta.json` status** based on the Investigation Decision:
- `ready_to_review` or `investigation` → `"status": "investigating"`
- `waiting` → `"status": "waiting-on-customer"`
- `reproduction` → `"status": "investigating"`

**File 4: `cases/ZD-{{TICKET_ID}}/response.md`** — Customer response draft:

```markdown
# Customer Response: ZD-{{TICKET_ID}}

## TL;DR

(2-3 sentence summary: what's happening and what the next step is)

---

## Response Draft

(Plain text response the TSE can copy-paste to the customer. Start with a greeting using the customer's first name. Direct, professional tone. Include specific commands and doc links as needed.)

---

## Internal Notes

**Response type:** Initial response / Follow-up / Solution / Escalation notice
**Risk level:** N/A / Low / Medium / High

**Before sending, verify:**
- [ ] TL;DR is clear and concise
- [ ] No internal jargon or Datadog-internal references
- [ ] Action items are specific and achievable
- [ ] Risk callouts included (if recommending config changes)
```

Replace `YYYY-MM-DD HH:MM` with the current date and time.

### 7c: If the case ALREADY exists — append a new timeline entry

Read the existing `cases/ZD-{{TICKET_ID}}/notes.md`. Pay attention to these sections that may already exist:
- `## Review History` — contains TSE feedback and prior agent revisions. **Read this carefully** — if the TSE requested changes, address them in your new entry.
- `## Session Context` — contains CLI agent session transcript. **Preserve as-is** — do not modify or remove.
- `## Chat TLDR` — contains summary of prior interactive chat sessions. **Preserve as-is** — do not modify or remove.

Then **append** a new timeline entry under `## Timeline`:

```markdown

### YYYY-MM-DD HH:MM — Re-investigation (Agent)

**Trigger:** (why this re-investigation happened: customer replied, TSE requested, etc.)

**New Findings**
- What changed since the last entry
- New information from the customer
- Updated analysis based on new data

**Updated Assessment**
- Likely cause: (updated if changed)
- Next steps:
  1. ...
  2. ...
```

Only include sections that have new information. Do NOT duplicate the header or Ticket Summary.

After appending, update the `## Investigation Decision` section in `notes.md` and update `meta.json` status accordingly.

Also update `cases/ZD-{{TICKET_ID}}/response.md` with a revised customer response draft if the investigation produced new findings.

The expected section order at the end of `notes.md` is:
1. `## Investigation Decision` — routing decision
2. `## Review History` — preserved (if present)
3. `## Session Context` — preserved as-is (if present)
4. `## Chat TLDR` — preserved as-is (if present)

### 7d: Update the Ticket Summary status

If the ticket status has changed since the header was written (e.g. Open → Pending → Solved), update the `| **Status** |` row in the Ticket Summary table in `notes.md` to reflect the current status. Also update `meta.json`.

## Rules
- Keep it factual — only include what you found, don't speculate
- If no similar tickets found, say so
- If no docs found, say so
- ALWAYS include links to relevant public docs, internal docs, and GitHub code
- NEVER reference code files without a clickable GitHub link (e.g. `https://github.com/DataDog/REPO/blob/main/path/to/file`)
- Be concise but thorough
- NEVER overwrite previous timeline entries — always append
- Use the current timestamp for each new entry
- NEVER delete or modify existing `## Review History`, `## Session Context`, or `## Chat TLDR` sections
- All case files go in `cases/ZD-{{TICKET_ID}}/` — never write to `investigations/`