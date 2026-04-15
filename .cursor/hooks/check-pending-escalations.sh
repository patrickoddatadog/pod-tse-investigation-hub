#!/bin/bash
# Stop hook: detects cases marked for escalation that lack a generated escalation summary.
#
# Two outcomes:
#   1. Case has "Escalated: [x] Yes" in notes.md but no ## Escalation Summary content → prompt agent
#   2. Nothing pending → exit quietly

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CASES_DIR="$PROJECT_ROOT/cases"

pending_cases=()

for case_dir in "$CASES_DIR"/*/; do
  [ -d "$case_dir" ] || continue
  case_id="$(basename "$case_dir")"

  notes="$case_dir/notes.md"
  [ -f "$notes" ] || continue

  has_escalation_marker=false
  if grep -qiE '\[x\]\s*Yes' "$notes" 2>/dev/null; then
    section=$(sed -n '/^## Escalation Notes/,/^## /p' "$notes" 2>/dev/null | head -5)
    if echo "$section" | grep -qiE '\[x\]\s*Yes'; then
      has_escalation_marker=true
    fi
  fi

  $has_escalation_marker || continue

  if grep -q '^## Escalation Summary' "$notes" 2>/dev/null; then
    summary_content=$(sed -n '/^## Escalation Summary/,/^## \|^---$/p' "$notes" | tail -n +2 | head -5)
    if [ -n "$(echo "$summary_content" | tr -d '[:space:]')" ]; then
      if ! echo "$summary_content" | grep -q 'Click "Generate Escalation Summary"'; then
        continue
      fi
    fi
  fi

  pending_cases+=("$case_id")
done

if [ ${#pending_cases[@]} -gt 0 ]; then
  cases_list=$(printf ', %s' "${pending_cases[@]}")
  cases_list="${cases_list:2}"

  jq -n --arg cases "$cases_list" '{
    "followup_message": ("PENDING ESCALATION SUMMARY: Case(s) " + $cases + " are marked for escalation but have no generated escalation summary. The TSE should open each case in the POD Ticket Dashboard, go to the Escalation tab, and click Generate Escalation Summary to create a JIRA-ready writeup. Alternatively, ensure the investigation notes are complete before generating.")
  }'
  exit 0
fi

echo '{}'
exit 0
