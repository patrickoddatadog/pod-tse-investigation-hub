# Zendesk Attachment Downloader — Execution Prompt

Follow these steps exactly. Use the Shell tool with `required_permissions: ["all"]` for all commands.

## Step 1: Extract ticket ID

Extract the Zendesk ticket ID from the user's message. It may appear as:
- `#1234567`, `ZD-1234567`, `1234567`
- A URL like `https://datadog.zendesk.com/agent/tickets/1234567`

## Step 1b: AI Compliance Check (MANDATORY)

```bash
.cursor/skills/_shared/zd-api.sh ticket {TICKET_ID}
```

If the output contains `ai_optout:true`, **STOP NOW**. Tell the user: "Ticket #{TICKET_ID}: AI processing is blocked — this customer has opted out of GenAI (oai_opted_out). Handle manually without AI." Do NOT proceed to download or analyze any attachments.

## Step 2: List attachments on the ticket

```bash
.cursor/skills/_shared/zd-api.sh attachments {TICKET_ID}
```

Output format: `filename | size MB | content_type | content_url`

If the result is `NO_ATTACHMENTS`, tell the user. If it starts with `ERROR:`, report the error.

## Step 3: Display attachment list

Show the user a table:

```
| # | File | Size | Type |
|---|------|------|------|
| 1 | flare-2024-hostname.zip | 52.3 MB | application/zip |
| 2 | screenshot.png | 0.5 MB | image/png |
```

## Step 4: Download attachments

For each attachment to download:

```bash
.cursor/skills/_shared/zd-api.sh download "{CONTENT_URL}" "{FILENAME}"
```

If there are multiple attachments, download them sequentially with a 2-second delay between each.

## Step 5: Verify downloads and move to case assets

Wait 3 seconds, then move downloaded files to the case directory:

```bash
mkdir -p cases/ZD-{TICKET_ID}/assets
ls -la ~/Downloads/{FILENAME}
mv ~/Downloads/{FILENAME} cases/ZD-{TICKET_ID}/assets/
```

If there are multiple attachments, move each one after verifying it exists.

## Step 6: Handle agent flares

If any downloaded file matches the pattern `datadog-agent-*.zip`:

1. Extract the flare into the case assets:
   ```bash
   mkdir -p cases/ZD-{TICKET_ID}/assets/flare
   unzip -o cases/ZD-{TICKET_ID}/assets/{FLARE_FILENAME} -d cases/ZD-{TICKET_ID}/assets/flare/
   ```

2. Find the flare root (the directory containing `status.log`):
   ```bash
   find cases/ZD-{TICKET_ID}/assets/flare -name "status.log" -maxdepth 3
   ```

3. Tell the user the flare is extracted and offer to analyze key files:
   - `status.log` — agent version, running checks, errors
   - `config-check.log` — check configuration validation
   - `diagnose.log` — connectivity diagnostics

   Note: If `cases/ZD-{TICKET_ID}/notes.md` exists, flare findings should be appended as a timeline entry in that file (under `## Timeline`), preserving all existing sections.

## Step 7: Summary

```
## Download Summary — Ticket #{TICKET_ID}

| File | Size | Status | Location |
|------|------|--------|----------|
| flare-2024-hostname.zip | 52.3 MB | Downloaded + Extracted | cases/ZD-{TICKET_ID}/assets/flare/ |
| screenshot.png | 0.5 MB | Downloaded | cases/ZD-{TICKET_ID}/assets/ |
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| "No Zendesk tab found" | Chrome not open or no Zendesk tab | Ask user to open `datadog.zendesk.com` in Chrome |
| "Executing JavaScript through AppleScript is turned off" | Chrome setting not enabled | Guide user: View > Developer > Allow JavaScript from Apple Events |
| "ERROR: HTTP 404" | Ticket not found or no access | Verify ticket ID and Zendesk permissions |
| "ERROR: HTTP 401/403" | Session expired | Ask user to log into Zendesk in Chrome |
| Download file not found | Download blocked or failed | Check Chrome download settings, try direct `curl` with content_url |
