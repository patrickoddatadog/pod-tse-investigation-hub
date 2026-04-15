# TSE Investigation Hub - Structure

This document explains the structure and purpose of the TSE Investigation Hub workspace.

---

## Directory Structure

### TSE Investigation Hub (`tse-investigation-hub/`)
```
tse-investigation-hub/
├── cases/                    # Customer cases (Zendesk tickets)
│   ├── .template/
│   └── ZD-XXXXXX/           # Zendesk ticket folders
├── templates/                # Customer communication templates
│   ├── customer-communication/
│   └── escalation/
├── solutions/                # Known issues & workarounds
├── docs/escalation-criteria.md  # When to escalate to Engineering
└── scripts/
    ├── zendesk_client.py
    ├── zendesk_mcp_server.py
    └── jira_client.py       # For creating escalations
```

---

## TSE Workflow
```
1. Customer opens Zendesk ticket
2. TSE investigates (uses TSE hub)
3. TSE tries standard troubleshooting
4. If stuck → TSE escalates to Engineering (creates JIRA)
5. TSE keeps customer updated
6. When resolved → TSE closes Zendesk ticket
```

---

## Product Coverage

### All Products
```
docs/
├── apm/                  # Application Performance Monitoring
├── infrastructure/       # Infrastructure monitoring, agents
├── logs/                 # Log management
├── rum/                  # Real User Monitoring
├── synthetics/           # Synthetic monitoring
├── network/              # Network monitoring
├── security/             # Security products
│   ├── appsec/
│   ├── siem/
│   ├── cws/
│   └── cspm/
├── platform/             # Billing, API, auth
└── common/               # Cross-product (agent, integrations)
```

---

## MCP Configuration

### TSE Hub MCP Config
```json
{
  "mcpServers": {
    "zendesk": {
      "command": "python3",
      "args": ["scripts/zendesk_mcp_server.py", ...]
    },
    "atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian", "--read-only"]
    },
    "github": { ... },
    "glean": { ... }
  }
}
```

---

## Key Focus Areas

- **Customer communication** guidelines (clear, empathetic, no jargon)
- **Risk assessment** for customer-facing recommendations
- **Escalation criteria** (when to escalate to Engineering)
- **Time management** (don't spend too long on escalatable issues)
- **Solution documentation** (help future TSEs)

---

## Shared Resources

- **Known issues documentation** (maintained collaboratively)
- **Troubleshooting guides** (adapted as needed)
- **Investigation techniques** (same methodologies)
- **Escalation learnings** (documented for future reference)

---

**Summary:** The TSE Investigation Hub supports customer-facing Technical Support Engineers working with Zendesk tickets across all Datadog products. TSEs escalate complex issues to Engineering via JIRA when needed.
