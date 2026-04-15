# Investigation Notes: ZD-XXXXXX

---

## Initial Assessment

**Date:** YYYY-MM-DD HH:MM

### What We Know
- [Fact 1]
- [Fact 2]
- [Fact 3]

### What We Don't Know Yet
- [Question 1]
- [Question 2]
- [Question 3]

### Initial Hypothesis
[What you think might be causing this]

---

## Investigation Log

### YYYY-MM-DD - Initial Review

**Actions Taken:**
- Reviewed ticket description
- Searched for similar cases in archive
- Checked `solutions/known-issues.md`

**Findings:**
- [What you learned]

**Next Steps:**
- [What to do next]

---

### YYYY-MM-DD - [Investigation Phase]

**Hypothesis:**
[What you're testing]

**Actions Taken:**
- [Action 1]
- [Action 2]
- [Action 3]

**Results:**
- [What happened]

**Findings:**
- [What you learned]

**Conclusions:**
- [What this tells us]

**Next Steps:**
- [Where to go from here]

---

## Customer Communications

### YYYY-MM-DD HH:MM - Initial Response
**Type:** Internal comment / Public comment
**Content:**
```
[What you said to customer]
```

**Customer Response:**
```
[What they said back]
```

---

### YYYY-MM-DD HH:MM - Information Request
**Type:** Public comment
**What I Asked For:**
- [Item 1]
- [Item 2]

**Customer Response:**
[Summary of what they provided]

---

## Evidence

### Logs

**Agent Log (host-123, 2026-02-04 10:00-11:00):**
```
[Relevant log snippets]
```

**Key Observations:**
- [What's notable about these logs]

---

### Configuration

**Agent Config (datadog.yaml):**
```yaml
[Relevant config sections]
```

**Issues Found:**
- [Any misconfigurations]

---

### Screenshots

See `assets/screenshots/`:
- `001-dashboard-view.png` - Shows missing data points
- `002-agent-status.png` - Agent status output

---

## Tests & Experiments

### Test 1: [Description]
**Date:** YYYY-MM-DD
**Hypothesis:** [What you're testing]
**Method:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:** [What should happen if hypothesis is correct]
**Actual Result:** [What actually happened]
**Conclusion:** [What this tells us]

---

### Test 2: [Description]
[Same format as above]

---

## Root Cause Analysis

### What We've Ruled Out
- ❌ [Possible cause 1] - [Why it's not this]
- ❌ [Possible cause 2] - [Why it's not this]
- ❌ [Possible cause 3] - [Why it's not this]

### Likely Root Cause
[What you believe is causing the issue]

**Evidence:**
- [Evidence 1]
- [Evidence 2]
- [Evidence 3]

**Why This Explains the Symptoms:**
[Connection between root cause and observed behavior]

---

## Solution

### Recommended Fix
[What needs to be done]

**Implementation Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:**
[What should happen after implementing fix]

**Risks:**
- [Risk 1 and mitigation]
- [Risk 2 and mitigation]

**Rollback Plan:**
[How to undo if something goes wrong]

---

## Draft Customer Response

> **Always include a draft customer-facing response.** Review and adapt before sending.
> Follow the Brief-First approach: TL;DR → Action items → Explanation → Technical details (if needed).
> Use templates from `templates/customer-communication/` as a starting point.

Hi [Customer Name],

[TL;DR — 2-3 sentences: what's happening and what the next step is]

[Action items or recommendations — bulleted, specific, actionable]

[Brief explanation — why this is happening, kept simple]

[Closing — offer further help, set expectations on next follow-up]

Best regards,
[Your Name]
Datadog Technical Support

---

## Zoom Call Preparation

### Answers to Customer Questions
- [Question 1]: [Answer]

### Agenda
1. [Agenda item 1]
2. [Agenda item 2]

### Resources
- [Doc title](URL)

### Key Points to Communicate
- [Key point 1]

---

## Leadership Summary

> Follow ONLY `templates/customer-communication/leadership-summary.md`.
> This is a SEPARATE section from TLDR Handover. It is for a **non-technical** audience (managers triaging tickets).
> **STRICT CONSTRAINTS:** Leadership Summary ≤45 words | Investigation ≤50 words | Next Steps ≤50 words. All non-technical.

### Leadership Summary
[≤45 words. Non-technical, high-level. No jargon, no ticket IDs, no config values.]

### Investigation
[≤50 words. Brief summary of what the TSE has done. Non-technical.]

### Next Steps
[≤50 words. Non-technical. What happens next in plain language.]

---

## TLDR Handover

> Follow ONLY `templates/customer-communication/tldr-handover.md`.
> This is a SEPARATE section from Leadership Summary. It is for **TSEs and managers** and CAN include technical detail.

### Leadership Summary
[Same ≤45 words non-technical summary as the Leadership Summary section above.]

### Investigation
[Technical details of what has been investigated — bullet points, include specifics.]

### Next Steps
[Technical next steps for the next TSE to follow.]

### Need from Customer
[What information or action is still needed from the customer.]

### Important Links
- [Link title](URL)

---

## Zoom Call Transcript

> Auto-populated when a recording is uploaded to `assets/recordings/`.
> Whisper extracts the transcript, then Cursor AI summarises it for a technical audience.
> The raw transcript is never shown here — only the structured summary.

**Source File:** [pending upload]
**Call Date:** YYYY-MM-DD

### Summary of Issue
[Auto-generated from Zoom call transcript]

### Findings on Call
[Auto-generated from Zoom call transcript]

### Workaround
[Auto-generated from Zoom call transcript]

---

## Escalation Summary

> Auto-generated via the **Generate Escalation Summary** button on the POD Ticket Dashboard "Escalation" tab.
> Uses OpenAI to synthesise README.md and investigation notes into a JIRA-ready escalation ticket.
> Can be regenerated at any time if investigation notes are updated.

[Click "Generate Escalation Summary" on the Escalation tab to populate this section]

---

## Escalation Notes

**Escalated:** [ ] Yes [ ] No

**If Yes:**

**Escalation Date:** YYYY-MM-DD
**JIRA Ticket:** SCRS-XXXX
**Reason for Escalation:**
[Why this needs engineering attention]

**What I've Provided to Engineering:**
- [List of logs, configs, evidence]
- [Summary of investigation]
- [What's been tried and ruled out]

**Engineering Feedback:**
[What engineering said, any new insights]

---

## Resolution

**Resolution Date:** YYYY-MM-DD

**Final Root Cause:**
[What actually caused the issue]

**Solution Implemented:**
[What was done to fix it]

**Outcome:**
[Confirmation that it's resolved]

**Customer Satisfaction:**
[Customer's response to resolution]

---

## Lessons Learned

### What Worked Well
- [Thing 1]
- [Thing 2]

### What Could Be Improved
- [Thing 1]
- [Thing 2]

### Knowledge to Share
- [ ] Create troubleshooting doc in `docs/`
- [ ] Update `solutions/known-issues.md`
- [ ] Share in team Slack channel
- [ ] Update internal documentation

### Similar Cases to Watch For
[Patterns or symptoms that might indicate similar issues]

---

## References

### Documentation Consulted
- [Doc 1] - [URL]
- [Doc 2] - [URL]

### Similar Cases
- ZD-XXXXX - [How it relates]
- SCRS-YYYY - [How it relates]

### Useful Resources
- [Resource 1]
- [Resource 2]

---

**Last Updated:** YYYY-MM-DD HH:MM

**ALWAYS consult .cursorrrules. THIS IS MANDATORY. NEVER SKIP consulting .cursorrrules**
