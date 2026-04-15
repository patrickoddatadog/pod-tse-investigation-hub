# Leadership Summary

Use this template for the `## Leadership Summary` section in `notes.md`. This populates the POD Ticket Dashboard "Leadership Summary" tab.

**This is NOT the same as the TLDR Handover.** The TLDR Handover is a separate section — see `tldr-handover.md`.

## Audience

**Managers** who need to quickly triage and understand the ticket. They are **non-technical** — no jargon, no config values, no ticket IDs, no CLI commands.

## Required Sub-sections (exactly 3)

### Leadership Summary
- **≤45 words.** No exceptions.
- Non-technical, high-level. Plain English only.
- Answers: "What is happening and what is the fix?"
- No: ticket IDs, config values, CLI commands, product-specific jargon

### Investigation
- **≤50 words.** No exceptions.
- What the TSE has done so far, in plain language.
- No: bullet points, technical details, JIRA references

### Next Steps
- **≤50 words.** No exceptions.
- What happens next, in plain language.
- No: technical steps, commands, config changes

## Example

```
## Leadership Summary

### Leadership Summary
Customer is receiving false alerts saying all servers are down when they are actually running. The issue is a configuration problem with how the monitoring system authenticates. A simple settings change will resolve it.

### Investigation
Confirmed the alerts fired because the monitoring system could not verify its connection. Checked for platform outages and found none. Root cause is a settings issue on the customer's side.

### Next Steps
Waiting for the customer to verify one setting in their configuration. Once confirmed, we will guide them through a quick fix that carries no risk.
```