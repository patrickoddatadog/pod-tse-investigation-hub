#!/usr/bin/env python3
"""
POD Ticket Dashboard — Local Web App

Run with: python app.py
Then open: http://localhost:5001
"""

import os
import re
import threading
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, abort, request, redirect, url_for, jsonify
import markdown
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension

BASE_DIR = Path(__file__).parent.resolve()
CASES_DIR = BASE_DIR / "cases"
ARCHIVE_DIR = BASE_DIR / "archive"
SOLUTIONS_DIR = BASE_DIR / "solutions"
TEMPLATES_DIR = BASE_DIR / "templates"
DOCS_DIR = BASE_DIR / "docs"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "web" / "templates"),
    static_folder=str(BASE_DIR / "web" / "static"),
)

MD_EXTENSIONS = [
    TableExtension(),
    FencedCodeExtension(),
    CodeHiliteExtension(css_class="codehilite", guess_lang=False),
    "nl2br",
]

log = logging.getLogger(__name__)

_transcription_status: dict[str, dict] = {}
_status_lock = threading.Lock()


def _set_status(case_id: str, state: str, **extra):
    with _status_lock:
        _transcription_status[case_id] = {"state": state, **extra}


def _get_status(case_id: str) -> dict:
    with _status_lock:
        return _transcription_status.get(case_id, {"state": "idle"})



def _strip_blockquote_instructions(text: str) -> str:
    """Remove blockquote lines (> ...) that contain template instructions."""
    return "\n".join(
        line for line in text.splitlines()
        if not line.strip().startswith(">")
    )


def render_md(text: str) -> str:
    return markdown.markdown(
        _strip_blockquote_instructions(text), extensions=MD_EXTENSIONS
    )


def parse_quick_info(readme_text: str) -> dict:
    """Extract Quick Info table fields from a case README.md."""
    info = {}
    table_pattern = re.compile(
        r"\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|"
    )
    for match in table_pattern.finditer(readme_text):
        key = match.group(1).strip()
        value = match.group(2).strip()
        if value and value != "Value":
            info[key] = value
    return info


_NOTES_META_PATTERNS = [
    (r"-\s*Customer:\s*\*\*(.+?)\*\*", "Customer"),
    (r"\*\*Customer:\*\*\s*(.+?)(?:\s*\(|$)", "Customer"),
    (r"-\s*Requester:\s*\*\*(.+?)\*\*", "Requester"),
    (r"\*\*Requester:\*\*\s*(.+?)$", "Requester"),
    (r"-\s*Product\s*Area:\s*\*?\*?(.+?)\*?\*?\s*$", "Product Area"),
    (r"-\s*Metric\s+affected:\s*`?(.+?)`?\s*$", "Product Area"),
    (r"-\s*Region:\s*(.+?)$", "Region"),
    (r"\*\*Assigned(?:\s+TSE)?:\*\*\s*(.+?)$", "Assigned TSE"),
]


def parse_notes_metadata(notes_text: str) -> dict:
    """Fallback: extract key metadata from notes.md when README.md is absent."""
    info: dict[str, str] = {}
    for pattern, key in _NOTES_META_PATTERNS:
        if key in info:
            continue
        m = re.search(pattern, notes_text, re.MULTILINE)
        if m:
            val = m.group(1).strip().rstrip("*").strip()
            if val:
                info[key] = val
    return info


_RESPONSE_HEADING_RE = re.compile(
    r"^##\s+(?:Draft|Proposed)\s+(?:Customer\s+)?(?:Response|Follow[- ]?Up\s+Message)",
    re.IGNORECASE,
)

_NEXT_STEPS_HEADING_RE = re.compile(
    r"^##\s+(?:Recommended\s+)?Next\s+Steps",
    re.IGNORECASE,
)

_LEADERSHIP_HEADING_RE = re.compile(
    r"^##\s+(?:TLDR\s+Handover|Leadership\s+Summary|Executive\s+Summary)",
    re.IGNORECASE,
)

_ZOOM_CALL_HEADING_RE = re.compile(
    r"^##\s+(?:(?:Proposed\s+)?Zoom\s+Call\s+Agenda|Zoom\s+Call|Call\s+Preparation)",
    re.IGNORECASE,
)

_ZOOM_TRANSCRIPT_HEADING_RE = re.compile(
    r"^##\s+Zoom\s+Call\s+Transcript",
    re.IGNORECASE,
)

_ESCALATION_SUMMARY_HEADING_RE = re.compile(
    r"^##\s+Escalation\s+Summary",
    re.IGNORECASE,
)



def _extract_section(text: str, heading_re) -> str:
    """Extract a markdown section matching heading_re, up to next ## or ---."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if heading_re.match(line.strip()):
            start = i
            break
    if start is None:
        return ""
    body_lines = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped.startswith("## ") or stripped == "---":
            break
        body_lines.append(line)
    return "\n".join(body_lines).strip()


def extract_proposed_response(notes_raw: str) -> str:
    return _extract_section(notes_raw, _RESPONSE_HEADING_RE)


def extract_issue_summary(readme_raw: str) -> str:
    """Pull the Issue Summary section from README.md."""
    return _extract_section(
        readme_raw,
        re.compile(r"^##\s+Issue\s+Summary", re.IGNORECASE),
    )


def extract_next_steps(notes_raw: str) -> str:
    """Pull the Next Steps / Recommended Next Steps section from notes.md."""
    return _extract_section(notes_raw, _NEXT_STEPS_HEADING_RE)


def extract_leadership_summary(notes_raw: str) -> str:
    result = _extract_section(
        notes_raw,
        re.compile(r"^##\s+Leadership\s+Summary", re.IGNORECASE),
    )
    if not result:
        result = _extract_section(notes_raw, _LEADERSHIP_HEADING_RE)
    return result


def extract_zoom_call(notes_raw: str) -> str:
    return _extract_section(notes_raw, _ZOOM_CALL_HEADING_RE)


def extract_zoom_transcript(notes_raw: str) -> str:
    """Extract the Zoom Call Transcript section, stripping any raw transcript block.

    The raw transcript is kept in notes.md for the agent to summarise, but should
    never be rendered on the web UI — only the structured summary is displayed.
    """
    section = _extract_section(notes_raw, _ZOOM_TRANSCRIPT_HEADING_RE)
    if not section:
        return ""

    lines = section.splitlines()
    filtered: list[str] = []
    in_raw_block = False
    for line in lines:
        if line.strip().startswith("### Raw Transcript"):
            in_raw_block = True
            continue
        if in_raw_block and line.strip().startswith("### "):
            in_raw_block = False
        if not in_raw_block:
            filtered.append(line)

    return "\n".join(filtered).strip()


def extract_escalation_summary(notes_raw: str) -> str:
    return _extract_section(notes_raw, _ESCALATION_SUMMARY_HEADING_RE)


def extract_important_links(notes_raw: str) -> str:
    """Pull the ### Important Links subsection from ## TLDR Handover."""
    tldr = _extract_section(
        notes_raw,
        re.compile(r"^##\s+TLDR\s+Handover", re.IGNORECASE),
    )
    if not tldr:
        return ""
    lines = tldr.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^###\s+Important\s+Links", line.strip(), re.IGNORECASE):
            start = i
            break
    if start is None:
        return ""
    body = []
    for line in lines[start + 1:]:
        if line.strip().startswith("### "):
            break
        body.append(line)
    return "\n".join(body).strip()


def has_pending_transcript(notes_raw: str) -> bool:
    """True when a raw transcript exists but hasn't been summarised yet."""
    section = _extract_section(notes_raw, _ZOOM_TRANSCRIPT_HEADING_RE)
    if not section:
        return False
    has_raw = "### Raw Transcript" in section
    has_summary = "### Summary of Issue" in section
    return has_raw and not has_summary


def _extract_raw_transcript(notes_raw: str) -> str:
    """Pull just the raw transcript text from the Zoom Call Transcript section."""
    section = _extract_section(notes_raw, _ZOOM_TRANSCRIPT_HEADING_RE)
    if not section:
        return ""
    lines = section.splitlines()
    in_raw = False
    raw_lines: list[str] = []
    for line in lines:
        if line.strip().startswith("### Raw Transcript"):
            in_raw = True
            continue
        if in_raw and line.strip().startswith("### "):
            break
        if in_raw:
            raw_lines.append(line)
    return "\n".join(raw_lines).strip()


def _replace_raw_with_summary(notes_raw: str, summary: str) -> str:
    """Replace the ### Raw Transcript block in notes.md with a structured summary."""
    lines = notes_raw.splitlines()

    section_start = None
    for i, line in enumerate(lines):
        if _ZOOM_TRANSCRIPT_HEADING_RE.match(line.strip()):
            section_start = i
            break
    if section_start is None:
        return notes_raw

    raw_start = None
    section_end = None
    for i in range(section_start + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("## ") or stripped == "---":
            section_end = i
            break
        if stripped.startswith("### Raw Transcript"):
            raw_start = i

    if raw_start is None:
        return notes_raw

    end = section_end if section_end is not None else len(lines)
    new_lines = lines[:raw_start] + summary.splitlines() + [""] + lines[end:]
    return "\n".join(new_lines)


_SUMMARY_SYSTEM_PROMPT = """\
You are a technical support engineer summarising a Zoom call transcript for an engineering audience.

Produce exactly three markdown sections — no other text, no introduction, no preamble:

### Summary of Issue
Concise description (2-3 sentences) of the core problem the customer described.

### Findings on Call
Key technical details: configurations discussed, error messages, diagnostic steps, \
environment details (versions, infrastructure), relevant timeline.

### Workaround
Any workaround discussed or agreed upon. Write "None identified" if none was discussed.

Rules:
- Be concise and technical — strip small talk, pleasantries, filler.
- Preserve exact error messages, metric names, config values, and version numbers.
- If the transcript is unclear on a point, note it.
- Do not invent details not in the transcript.
"""


def _summarise_transcript(raw_text: str) -> str:
    """Call OpenAI to produce a structured summary of a raw transcript."""
    import openai

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.environ.get("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")
    client = openai.OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()




_ESCALATION_SYSTEM_PROMPT = """\
You are a Technical Support Engineer preparing a JIRA escalation ticket for Engineering.

Given the full case context (README and investigation notes), produce a structured \
escalation summary in markdown. Use exactly this format — no other text, no preamble:

### Title
[No more than 7 words. Ideally less. E.g. "SAML - XML Metadata file failing to upload"]

### Environment
- **Customer:** [Company name + Org ID + ZD ticket link if available]
- **Region:** [Datadog region if known, else "Unknown"]


### Issue Description
[Clear description of what's happening]

### Expected Behavior
[What should happen]

### Impact
[How this affects the customer — data loss, missing monitors, can't deploy, etc.]

### Reproduction Steps
1. [Step 1]
2. [Step 2]
(Only if reproducible — write "Not yet reproduced" otherwise)

### Investigation Summary
[What the TSE has investigated and ruled out]

### Screenshots/Evidence
[Reference any files in cases/ZD-xxxxxx/assets if present, otherwise "None attached"]

### Additional Context
*This is Mandatory*
- Similar cases: [Link to related tickets]
- Documentation checked: [What docs were reviewed]
- Confluence searches: [What was searched for]

Rules:
- Be concise and factual — strip speculation and filler.
- Preserve exact error messages, metric names, config values, and version numbers.
- The Title must be 7 words or fewer.
- Do NOT include "Datadog Agent Version" unless the case specifically involves the Datadog Agent.
- If information is missing for a field, write "Not available in case notes".
- Do not invent details not present in the case data.
"""


def _generate_escalation_summary(readme_raw: str, notes_raw: str) -> str:
    """Call OpenAI to produce a structured escalation summary from case data."""
    import openai

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.environ.get("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")
    client = openai.OpenAI(api_key=api_key)

    case_context = f"## README.md\n\n{readme_raw}\n\n---\n\n## Investigation Notes (notes.md)\n\n{notes_raw}"

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _ESCALATION_SYSTEM_PROMPT},
            {"role": "user", "content": case_context},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def _write_escalation_section(notes_path: Path, summary: str) -> str:
    """Write or replace the ## Escalation Summary section in notes.md."""
    notes_raw = notes_path.read_text(encoding="utf-8")
    lines = notes_raw.splitlines()

    section_start = None
    section_end = None
    for i, line in enumerate(lines):
        if _ESCALATION_SUMMARY_HEADING_RE.match(line.strip()):
            section_start = i
            continue
        if section_start is not None and section_end is None:
            stripped = line.strip()
            if stripped.startswith("## ") or stripped == "---":
                section_end = i
                break

    new_section_body = ["", summary, "", "---"]

    if section_start is not None:
        end = section_end if section_end is not None else len(lines)
        lines[section_start + 1:end] = new_section_body
    else:
        escalation_notes_idx = None
        for i, line in enumerate(lines):
            if re.match(r"^##\s+Escalation\s+Notes", line.strip(), re.IGNORECASE):
                escalation_notes_idx = i
                break

        insert_at = escalation_notes_idx if escalation_notes_idx is not None else len(lines)
        insert_block = ["", "## Escalation Summary"] + new_section_body + [""]
        lines[insert_at:insert_at] = insert_block

    updated = "\n".join(lines)
    notes_path.write_text(updated, encoding="utf-8")
    return updated


def get_case_dirs():
    if not CASES_DIR.exists():
        return []
    return sorted(
        [
            d
            for d in CASES_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )


def get_archive_dirs():
    if not ARCHIVE_DIR.exists():
        return []
    months = []
    for d in sorted(ARCHIVE_DIR.iterdir(), reverse=True):
        if d.is_dir():
            files = sorted(d.glob("ZD-*.md"))
            months.append({"name": d.name, "path": d, "files": files})
    return months


def load_case(case_id: str) -> Optional[dict]:
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        return None

    readme_path = case_dir / "README.md"
    notes_path = case_dir / "notes.md"

    readme_raw = readme_path.read_text() if readme_path.exists() else ""
    notes_raw = notes_path.read_text() if notes_path.exists() else ""

    info = parse_quick_info(readme_raw)

    if notes_raw:
        notes_meta = parse_notes_metadata(notes_raw)
        for key, val in notes_meta.items():
            if key not in info:
                info[key] = val

    status = info.get("Status", "Unknown")
    priority = info.get("Priority", "Unknown")

    proposed_raw = extract_proposed_response(notes_raw)
    summary_raw = extract_issue_summary(readme_raw)
    next_steps_raw = extract_next_steps(notes_raw)
    leadership_raw = extract_leadership_summary(notes_raw)
    zoom_raw = extract_zoom_call(notes_raw)
    zoom_transcript_raw = extract_zoom_transcript(notes_raw)
    escalation_raw = extract_escalation_summary(notes_raw)
    important_links_raw = extract_important_links(notes_raw)

    requester = (
        info.get("Requester", "")
        or info.get("Contact", "")
    )
    if requester:
        requester = re.sub(r"\s*\(.*?\)\s*", "", requester).strip()
        requester = re.sub(r"\s*\S+@\S+\s*", "", requester).strip()
    if not requester:
        customer = info.get("Customer", "")
        paren = re.search(r"\(([^)]+)\)", customer)
        if paren:
            val = paren.group(1)
            if not re.match(r"(?i)(org.?id|visa|inc|ltd|llc|ag)\b", val):
                requester = val

    return {
        "id": case_id,
        "dir": case_dir,
        "info": info,
        "status": status,
        "requester": requester,
        "priority": priority,
        "customer": info.get("Customer") or info.get("Org") or info.get("Organization") or info.get("Company") or "Unknown",
        "product_area": info.get("Product Area", "—"),
        "assigned": info.get("Assigned TSE", "—"),
        "started": info.get("Started", "—"),
        "readme_raw": readme_raw,
        "readme_html": render_md(readme_raw),
        "notes_raw": notes_raw,
        "notes_html": render_md(notes_raw),
        "has_notes": bool(notes_raw.strip()),
        "proposed_response_raw": proposed_raw,
        "proposed_response_html": render_md(proposed_raw) if proposed_raw else "",
        "issue_summary_raw": summary_raw,
        "issue_summary_html": render_md(summary_raw) if summary_raw else "",
        "next_steps_raw": next_steps_raw,
        "next_steps_html": render_md(next_steps_raw) if next_steps_raw else "",
        "leadership_raw": leadership_raw,
        "leadership_html": render_md(leadership_raw) if leadership_raw else "",
        "zoom_raw": zoom_raw,
        "zoom_html": render_md(zoom_raw) if zoom_raw else "",
        "zoom_transcript_raw": zoom_transcript_raw,
        "zoom_transcript_html": render_md(zoom_transcript_raw) if zoom_transcript_raw else "",
        "transcript_pending": has_pending_transcript(notes_raw),
        "escalation_raw": escalation_raw,
        "escalation_html": render_md(escalation_raw) if escalation_raw else "",
        "important_links_raw": important_links_raw,
        "important_links_html": render_md(important_links_raw) if important_links_raw else "",
        "last_modified": datetime.fromtimestamp(case_dir.stat().st_mtime),
    }


# ── Routes ──────────────────────────────────────────────────────────────────


@app.route("/")
def dashboard():
    cases = []
    for d in get_case_dirs():
        case = load_case(d.name)
        if case:
            cases.append(case)

    status_filter = request.args.get("status", "").lower()
    priority_filter = request.args.get("priority", "").lower()
    search_query = request.args.get("q", "").lower()

    filtered = cases
    if status_filter:
        filtered = [c for c in filtered if c["status"].lower() == status_filter]
    if priority_filter:
        filtered = [c for c in filtered if c["priority"].lower() == priority_filter]
    if search_query:
        filtered = [
            c
            for c in filtered
            if search_query in c["id"].lower()
            or search_query in c["customer"].lower()
            or search_query in c["product_area"].lower()
            or search_query in c["readme_raw"].lower()
        ]

    statuses = sorted(set(c["status"] for c in cases))
    priorities = sorted(set(c["priority"] for c in cases))

    stats = {
        "total": len(cases),
        "investigating": sum(1 for c in cases if "investigat" in c["status"].lower()),
        "escalated": sum(1 for c in cases if "escalat" in c["status"].lower()),
        "resolved": sum(1 for c in cases if "resolv" in c["status"].lower()),
    }

    return render_template(
        "dashboard.html",
        cases=filtered,
        stats=stats,
        statuses=statuses,
        priorities=priorities,
        current_status=status_filter,
        current_priority=priority_filter,
        current_query=request.args.get("q", ""),
    )


@app.route("/case/<case_id>")
def case_detail(case_id: str):
    case = load_case(case_id)
    if not case:
        abort(404)

    assets = []
    assets_dir = case["dir"] / "assets"
    if assets_dir.exists():
        for f in sorted(assets_dir.rglob("*")):
            if f.is_file():
                assets.append(str(f.relative_to(case["dir"])))

    recordings_dir = case["dir"] / "assets" / "recordings"
    recordings = []
    if recordings_dir.exists():
        for f in sorted(recordings_dir.iterdir()):
            if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in AUDIO_VIDEO_EXTENSIONS:
                recordings.append({"name": f.name, "size": f.stat().st_size})

    transcribing = any(
        (recordings_dir / (r["name"] + ".transcribing")).exists()
        for r in recordings
    ) if recordings_dir.exists() else False

    return render_template(
        "case_detail.html",
        case=case,
        assets=assets,
        recordings=recordings,
        transcribing=transcribing,
    )


AUDIO_VIDEO_EXTENSIONS = {
    ".mp3", ".mp4", ".m4a", ".wav", ".webm", ".ogg", ".mov", ".avi", ".mkv",
}


def _write_transcript_section(case_dir: Path, filename: str, raw_transcript: str = ""):
    """Write the raw Whisper transcript into the ## Zoom Call Transcript section of notes.md.

    The Cursor agent (via the zoom-transcript rule) will then read this raw
    transcript and replace it with a structured summary using the
    zoom-call-transcript template.
    """
    notes_path = case_dir / "notes.md"
    if not notes_path.exists():
        return

    notes = notes_path.read_text(encoding="utf-8")
    lines = notes.splitlines()

    section_start = None
    section_end = None
    for i, line in enumerate(lines):
        if _ZOOM_TRANSCRIPT_HEADING_RE.match(line.strip()):
            section_start = i
            continue
        if section_start is not None and section_end is None:
            stripped = line.strip()
            if stripped.startswith("## ") or stripped == "---":
                section_end = i
                break

    today = datetime.now().strftime("%Y-%m-%d")
    transcript_file = Path(filename).stem + ".transcript.txt"

    new_section_body = [
        "",
        f"**Source File:** {filename}",
        f"**Call Date:** {today}",
        f"**Raw transcript:** `assets/recordings/{transcript_file}`",
        "",
    ]

    if raw_transcript:
        new_section_body.extend([
            "### Raw Transcript",
            "",
            raw_transcript,
            "",
        ])

    if section_start is not None:
        end = section_end if section_end is not None else len(lines)
        lines[section_start + 1 : end] = new_section_body
    else:
        lines.append("")
        lines.append("## Zoom Call Transcript")
        lines.extend(new_section_body)

    notes_path.write_text("\n".join(lines), encoding="utf-8")



def _run_whisper(file_path: Path, case_dir: Path):
    """Run Whisper transcription in a background thread and update notes.md."""
    case_id = case_dir.name
    lock_file = file_path.parent / (file_path.name + ".transcribing")
    try:
        lock_file.touch()

        _set_status(case_id, "transcribing", filename=file_path.name)
        from scripts.transcribe import transcribe
        raw_text = transcribe(str(file_path))

        out_path = file_path.parent / (file_path.stem + ".transcript.txt")
        out_path.write_text(raw_text, encoding="utf-8")

        _write_transcript_section(case_dir, file_path.name, raw_transcript=raw_text)
        _set_status(case_id, "done", filename=file_path.name)

    except Exception as e:
        log.error("Transcription pipeline failed for %s: %s", file_path.name, e)
        _set_status(case_id, "error", filename=file_path.name, error=str(e))
    finally:
        lock_file.unlink(missing_ok=True)


@app.route("/case/<case_id>/upload-recording", methods=["POST"])
def upload_recording(case_id: str):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        abort(404)

    f = request.files.get("recording")
    if not f or not f.filename:
        return redirect(url_for("case_detail", case_id=case_id))

    ext = Path(f.filename).suffix.lower()
    if ext not in AUDIO_VIDEO_EXTENSIONS:
        return redirect(url_for("case_detail", case_id=case_id))

    recordings_dir = case_dir / "assets" / "recordings"
    recordings_dir.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r"[^\w.\-]", "_", f.filename)
    saved_path = recordings_dir / safe_name
    f.save(str(saved_path))

    thread = threading.Thread(
        target=_run_whisper,
        args=(saved_path, case_dir),
        daemon=True,
    )
    thread.start()

    return redirect(url_for("case_detail", case_id=case_id) + "#panel-transcript")


@app.route("/case/<case_id>/transcription-status")
def transcription_status(case_id: str):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        abort(404)

    status = _get_status(case_id)

    if status["state"] == "idle":
        recordings_dir = case_dir / "assets" / "recordings"
        if recordings_dir.exists():
            for f in recordings_dir.iterdir():
                if f.name.endswith(".transcribing"):
                    status = {"state": "transcribing", "filename": f.name.replace(".transcribing", "")}
                    break

    transcript_html = ""
    transcript_raw = ""
    pending = False
    if status["state"] == "done":
        notes_path = case_dir / "notes.md"
        if notes_path.exists():
            notes_raw = notes_path.read_text(encoding="utf-8")
            pending = has_pending_transcript(notes_raw)
            section = extract_zoom_transcript(notes_raw)
            if section:
                transcript_html = render_md(section)
                transcript_raw = section

    return jsonify({**status, "transcript_html": transcript_html, "transcript_raw": transcript_raw, "transcript_pending": pending})


@app.route("/case/<case_id>/summarise-transcript", methods=["POST"])
def summarise_transcript(case_id: str):
    """Summarise a pending transcript using OpenAI."""
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        abort(404)

    notes_path = case_dir / "notes.md"
    if not notes_path.exists():
        return jsonify({"error": "notes.md not found"}), 404

    notes_raw = notes_path.read_text(encoding="utf-8")
    if not has_pending_transcript(notes_raw):
        return jsonify({"error": "No pending transcript to summarise"}), 400

    raw_text = _extract_raw_transcript(notes_raw)
    if not raw_text:
        return jsonify({"error": "Raw transcript is empty"}), 400

    try:
        summary = _summarise_transcript(raw_text)
    except Exception as e:
        log.error("Transcript summarisation failed for %s: %s", case_id, e)
        return jsonify({"error": f"Summarisation failed: {e}"}), 500

    updated_notes = _replace_raw_with_summary(notes_raw, summary)
    notes_path.write_text(updated_notes, encoding="utf-8")

    section = extract_zoom_transcript(updated_notes)
    transcript_html = render_md(section) if section else ""

    return jsonify({"transcript_html": transcript_html, "transcript_raw": section})


@app.route("/case/<case_id>/generate-escalation", methods=["POST"])
def generate_escalation(case_id: str):
    """Generate a JIRA-ready escalation summary from the case data using OpenAI."""
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        abort(404)

    readme_path = case_dir / "README.md"
    notes_path = case_dir / "notes.md"

    if not notes_path.exists():
        return jsonify({"error": "notes.md not found"}), 404

    readme_raw = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    notes_raw = notes_path.read_text(encoding="utf-8")

    try:
        summary = _generate_escalation_summary(readme_raw, notes_raw)
    except Exception as e:
        log.error("Escalation summary generation failed for %s: %s", case_id, e)
        return jsonify({"error": f"Generation failed: {e}"}), 500

    updated_notes = _write_escalation_section(notes_path, summary)
    section = extract_escalation_summary(updated_notes)
    escalation_html = render_md(section) if section else ""

    return jsonify({"escalation_html": escalation_html, "escalation_raw": section})


@app.route("/case/<case_id>/remove", methods=["POST"])
def remove_case(case_id: str):
    """Permanently delete a case folder from the cases directory."""
    import shutil

    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        return jsonify({"error": "Case not found"}), 404

    if case_dir == CASES_DIR or not str(case_dir).startswith(str(CASES_DIR)):
        return jsonify({"error": "Invalid case path"}), 400

    try:
        shutil.rmtree(case_dir)
    except Exception as e:
        log.error("Failed to remove case %s: %s", case_id, e)
        return jsonify({"error": f"Deletion failed: {e}"}), 500

    return jsonify({"status": "removed", "case_id": case_id})


@app.route("/known-issues")
def known_issues():
    ki_path = SOLUTIONS_DIR / "known-issues.md"
    content = ""
    if ki_path.exists():
        content = render_md(ki_path.read_text())
    return render_template("known_issues.html", content=content)


@app.route("/comms-templates")
def comms_templates():
    groups = {}
    if TEMPLATES_DIR.exists():
        for subdir in sorted(TEMPLATES_DIR.iterdir()):
            if subdir.is_dir():
                files = []
                for f in sorted(subdir.glob("*.md")):
                    files.append(
                        {
                            "name": f.stem.replace("-", " ").title(),
                            "filename": f.name,
                            "subdir": subdir.name,
                            "content_html": render_md(f.read_text()),
                            "content_raw": f.read_text(),
                        }
                    )
                if files:
                    groups[subdir.name.replace("-", " ").title()] = files
    return render_template("comms_templates.html", groups=groups)


@app.route("/archive")
def archive():
    months = get_archive_dirs()
    archive_data = []
    for m in months:
        entries = []
        for f in m["files"]:
            raw = f.read_text()
            entries.append(
                {
                    "name": f.stem,
                    "filename": f.name,
                    "month": m["name"],
                    "html": render_md(raw),
                }
            )
        archive_data.append({"name": m["name"], "entries": entries})
    return render_template("archive.html", months=archive_data)


@app.route("/archive/<month>/<filename>")
def archive_detail(month: str, filename: str):
    fpath = ARCHIVE_DIR / month / filename
    if not fpath.exists():
        abort(404)
    raw = fpath.read_text()
    return render_template(
        "archive_detail.html",
        month=month,
        filename=filename,
        content=render_md(raw),
    )


@app.route("/docs")
def docs():
    content_map = {}

    esc_path = DOCS_DIR / "escalation-criteria.md"
    if esc_path.exists():
        content_map["Escalation Criteria"] = render_md(esc_path.read_text())

    if DOCS_DIR.exists():
        for item in sorted(DOCS_DIR.iterdir()):
            if item.is_dir():
                for f in sorted(item.glob("*.md")):
                    label = f"{item.name.title()} / {f.stem.replace('-', ' ').title()}"
                    content_map[label] = render_md(f.read_text())

    return render_template("docs.html", content_map=content_map)


@app.route("/health")
def health():
    return {"status": "ok", "app": "pod-ticket-dashboard", "port": 8501}


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    print("\n  POD Ticket Dashboard")
    print("  http://localhost:8501\n")
    app.run(debug=True, port=8501)
