#!/bin/bash
# Stop hook: detects unsummarised transcripts and chains the agent to summarise them.
#
# Three possible outcomes:
#   1. Whisper still running (.transcribing lock file exists) → tell agent to wait
#   2. Raw transcript exists but no summary → tell agent to summarise now
#   3. Nothing pending → exit quietly

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CASES_DIR="$PROJECT_ROOT/cases"

transcribing_cases=()
pending_cases=()
seen=""

for case_dir in "$CASES_DIR"/*/; do
  [ -d "$case_dir" ] || continue
  case_id="$(basename "$case_dir")"
  recordings_dir="$case_dir/assets/recordings"
  [ -d "$recordings_dir" ] || continue

  # Check if Whisper is still running
  for lock in "$recordings_dir"/*.transcribing; do
    if [ -f "$lock" ]; then
      transcribing_cases+=("$case_id")
      break
    fi
  done

  # Check for raw transcripts that haven't been summarised
  for transcript_file in "$recordings_dir"/*.transcript.txt; do
    [ -f "$transcript_file" ] || continue

    case "$seen" in
      *"|$case_id|"*) continue ;;
    esac
    seen="${seen}|${case_id}|"

    notes="$case_dir/notes.md"
    [ -f "$notes" ] || continue

    if grep -q '### Summary of Issue' "$notes" 2>/dev/null; then
      continue
    fi

    pending_cases+=("$case_id")
  done
done

# Case 1: Whisper is still running — tell agent to wait so the hook can re-check
if [ ${#transcribing_cases[@]} -gt 0 ] && [ ${#pending_cases[@]} -eq 0 ]; then
  cases_list=$(printf ', %s' "${transcribing_cases[@]}")
  cases_list="${cases_list:2}"

  jq -n --arg cases "$cases_list" '{
    "followup_message": ("TRANSCRIPTION IN PROGRESS: Whisper is still transcribing audio for case(s): " + $cases + ". Run `sleep 15` to wait for it to finish, then do nothing else — the stop hook will re-check automatically.")
  }'
  exit 0
fi

# Case 2: Raw transcript ready, needs summarisation — dispatch background subagent(s)
if [ ${#pending_cases[@]} -gt 0 ]; then
  cases_list=$(printf ', %s' "${pending_cases[@]}")
  cases_list="${cases_list:2}"

  jq -n --arg cases "$cases_list" '{
    "followup_message": ("PENDING TRANSCRIPT SUMMARISATION: Case(s) " + $cases + " have raw Zoom call transcripts that need summarisation. For each case: read the ## Zoom Call Transcript section in cases/<case-id>/notes.md, find the ### Raw Transcript block, and replace it with a structured summary (### Summary of Issue, ### Findings on Call, ### Workaround) following templates/customer-communication/zoom-call-transcript.md. Keep the metadata fields (Source File, Call Date, Raw transcript). See .cursor/rules/zoom-transcript.mdc for details.")
  }'
  exit 0
fi

# Case 3: Nothing to do
echo '{}'
exit 0
