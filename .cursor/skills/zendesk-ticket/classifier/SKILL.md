---
name: zendesk-ticket-classifier
description: Classify a Zendesk ticket by nature (bug, question, feature request, incident, etc.) with confirmation checks. Use when the user mentions classify ticket, ticket type, ticket nature, what kind of ticket, categorize ticket, or triage ticket.
---

# Ticket Classifier

Classifies a Zendesk ticket into one of 7 categories based on its content, with confirmation checks to avoid misclassification.

Classifies by **WHAT** type of ticket it is (bug? question? incident?). Results are persisted to `cases/ZD-{id}/meta.json` so the TSE Hub dashboard can display the issue type.

## How to Use

Just say: **"classify ticket #1234567"** or **"what type of ticket is ZD-1234567?"**

## When This Skill is Activated

Triggers on:
- "classify ticket #XYZ"
- "what kind of ticket is #XYZ"
- "categorize ZD-XYZ"
- "triage ticket #XYZ"
- Called by `zendesk-ticket-investigator` during investigations

Then:
1. Extract the ticket ID
2. **Run the AI Compliance Check below FIRST**
3. Follow the steps in `classify-prompt.md`
4. Return the classification with confidence and evidence

## Think fast (time-limited runs)

When the request is a **triage run** (e.g. "Triage Zendesk ticket #N", "Perform ALL of the following steps", or the prompt lists skills: classifier, info-needed, routing, difficulty, eta), you are in **think-fast** mode:

- **Minimize reasoning** — One short decision step, then output. No long chain-of-thought.
- **Skip optional work** — Do Steps 0, 1, 1b, 2, and 4 only; skip Step 3 (confirmation checks). At most one quick check if needed.
- **Concise output** — Category + key evidence in a few lines. Add: *"Confirmation checks deferred to investigation (time-limited run)."*
- **No retries** — If zd-api.sh or a tool fails, use fallback once and continue; do not retry.

This keeps the run under the timeout. For a single-ticket "classify ticket #X" in chat with no time pressure, you may use the full path (including confirmation checks).

## Fast path (Kanban triage / time-limited runs)

**Use the fast path whenever** the user message is a triage request — e.g. "Triage Zendesk ticket #N", "Perform ALL of the following steps" (with classify as one step), or the prompt lists multiple skills (classifier, info-needed, routing, difficulty, eta). In those cases the run is time-limited; do not run confirmation checks.

When this skill is run from **Kanban triage** or any **time-limited context** (e.g. ~2 min timeout):

- Do **Steps 0, 1, 1b, 2, and 4 only**. **Skip Step 3 (confirmation checks)** or run at most one quick check.
- Output the classification with evidence from signal words; add a line: *"Confirmation checks deferred to investigation (time-limited run)."*
- This avoids timeout while still delivering a usable category for the board.

## If zd-api.sh fails (exit 1 or no output)

`zd-api.sh` uses Chrome + osascript. If Chrome has no Zendesk tab open, or the script fails, it returns **exit code 1** and no output. **Do not fail the skill.**

- **Compliance:** You cannot confirm `oai_opted_out`. In the output state: *"Compliance check skipped (Zendesk API unavailable — ensure Chrome has a Zendesk tab open). Verify manually before using AI output."* Then proceed.
- **Ticket content:** Use **Glean MCP** (read_document with the ticket URL) or the **case notes** (`cases/ZD-{TICKET_ID}/notes.md`) if they exist. State in output: *"Ticket content via fallback (Glean or case notes)."*
- Return a classification based on the content you have. The triage column still gets a category; the TSE can refine after.

## AI Compliance Check (MANDATORY — FIRST STEP)

**Before processing ANY ticket data**, check for the `oai_opted_out` tag:

```bash
.cursor/skills/_shared/zd-api.sh ticket {TICKET_ID}
```

If the output contains `ai_optout:true`:
1. **STOP IMMEDIATELY** — do NOT process ticket data through the LLM
2. Do NOT generate any classification or report
3. Tell the user: **"Ticket #{TICKET_ID}: AI processing is blocked — this customer has opted out of GenAI (oai_opted_out). Handle manually without AI."**
4. Exit the skill

This is a legal/compliance requirement. No exceptions.

## Categories

| Category | Description |
|----------|-------------|
| `billing-question` | Billing inquiry, pricing, plan changes, usage questions |
| `billing-bug` | Wrong charges, invoice errors, billing system issues |
| `technical-question` | How-to, configuration guidance, best practices, feature clarification |
| `technical-bug` | Errors, crashes, unexpected behavior, regressions |
| `configuration-troubleshooting` | Setup, installation, config issues — product works but setup is wrong |
| `feature-request` | Customer wants new functionality that doesn't exist |
| `incident` | Production outage, service degradation, multiple users affected |

## Decision Tree

```
Ticket comes in
  ├── Mentions billing/pricing/invoice?
  │     ├── Reports wrong charge/discrepancy → billing-bug
  │     └── Asks for info/clarification → billing-question
  ├── Asks "how to" / "is it possible" / "can I"?
  │     ├── Feature doesn't exist → feature-request
  │     └── Feature exists, needs guidance → technical-question
  ├── Reports error/crash/broken behavior?
  │     ├── Config looks wrong → configuration-troubleshooting
  │     └── Config looks correct → technical-bug
  ├── Just installed / setting up / first time?
  │     └── → configuration-troubleshooting
  └── Production impact / outage / urgent?
        ├── Multiple orgs or status page confirms → incident
        └── Single customer only → technical-bug
```

## Confirmation Checks per Category

### billing-question
- No error/bug reported in ticket
- Contains: "how much", "what plan", "upgrade", "pricing", "subscription"
- Product is working fine, customer just needs billing info
- **Verify:** Search Salesforce for customer's current plan
- **Risk:** Could be `feature-request` if asking about a feature on a higher plan

### billing-bug
- Customer reports incorrect amount, duplicate charge, wrong plan applied
- Evidence of discrepancy between expected and actual billing
- **Verify:** Check Salesforce for actual plan, invoice history
- **Verify:** Check org usage metrics (`datadog.estimated_usage.*`)
- **Risk:** Could be `billing-question` if customer misunderstands pricing model

### technical-question
- Contains questions, not complaints about broken behavior
- No logs, stack traces, or error messages
- Customer wants guidance, best practices, or clarification
- **Verify:** Check if the answer exists in public docs (docs.datadoghq.com)
- **Verify:** Search Confluence for existing guides on the topic
- **Risk:** Could be `configuration-troubleshooting` if they're asking "how to" because setup fails

### technical-bug
- Error message, logs, or stack traces present
- "It used to work", "it should do X but does Y", "regression"
- Customer's config looks correct but it still fails
- **Verify:** Search GitHub issues in DataDog repos for the same error
- **Verify:** Search Zendesk for similar tickets — many reports = likely real bug
- **Verify:** Check Confluence/release notes for known issues
- **Risk:** Could be `configuration-troubleshooting` if config is actually wrong

### configuration-troubleshooting
- "Just installed", "trying to configure", "first time", "setting up"
- Customer shares config (datadog.yaml, Helm values, Docker env vars)
- Likely misconfiguration: missing API key, wrong endpoint, permissions, wrong integration config
- **Verify:** Review shared config against docs' expected config
- **Verify:** Check agent status/flare for config validation errors
- **Verify:** Compare config against `datadog-agent` defaults
- **Risk:** Could be `technical-bug` if config is correct but still fails

### feature-request
- Customer asks for something not currently available
- No bug reported — product works as designed, customer wants more
- **Verify:** Search public docs — does the feature actually exist?
- **Verify:** Search JIRA for existing feature requests (same ask from others)
- **Risk:** Could be `technical-question` if the feature exists and customer doesn't know

### incident
- Production impact: "outage", "down", "all monitors firing", "data loss"
- Multiple users/systems affected, not just one dashboard
- Urgency language: "P1", "SEV", "urgent", "critical", "production"
- **Verify:** Check Datadog status page (https://status.datadoghq.com)
- **Verify:** Query org metrics for data gaps (`agent.running`, `datadog.agent.running`)
- **Verify:** Check if other customers opened similar tickets at same time
- **Risk:** Could be `technical-bug` if only one customer is affected

## Output Format

```markdown
## Classification: ZD-{TICKET_ID}

| Field | Value |
|-------|-------|
| **Category** | `{category}` |
| **Confidence** | High / Medium / Low |
| **Signals** | key phrases and evidence found |

### Evidence
- [list of specific signals found in the ticket]

### Confirmation Checks Performed
- [x] Check 1 — result
- [x] Check 2 — result
- [ ] Check 3 — could not verify (reason)

### Misclassification Risk
- Could also be `{other_category}` because: {reason}

### Suggested Actions
- {action based on category}
```

## Integration with Other Skills

- **`zendesk-ticket-investigator`** → calls classifier as first step → includes category in report
- **`zendesk-ticket-pool`** → pool output shows issue type when available from `meta.json`
- Classification is persisted to `cases/ZD-{id}/meta.json` for the TSE Hub dashboard

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — skill definition |
| `classify-prompt.md` | Step-by-step classification prompt |
