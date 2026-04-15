#!/usr/bin/env python3
"""
Whisper transcription for Zoom call recordings.

Usage:
    python scripts/transcribe.py <audio_or_video_file>
    python scripts/transcribe.py cases/ZD-2529804/assets/recordings/call.mp4

Outputs the raw transcript to stdout AND writes a .txt file next to the source.
Uses the "base" model by default (good speed/accuracy tradeoff).
Set WHISPER_MODEL env var to override (tiny, base, small, medium, large).
"""

import sys
import os
from pathlib import Path
from typing import Optional

def transcribe(file_path: str, model_name: Optional[str] = None) -> str:
    import whisper

    model_name = model_name or os.environ.get("WHISPER_MODEL", "base")
    model = whisper.load_model(model_name)
    result = model.transcribe(file_path)
    return result["text"]


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/transcribe.py <audio_or_video_file>", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"File not found: {src}", file=sys.stderr)
        sys.exit(1)

    print(f"Transcribing {src.name} with Whisper...", file=sys.stderr)
    text = transcribe(str(src))

    out_path = src.parent / (src.stem + ".transcript.txt")
    out_path.write_text(text, encoding="utf-8")
    print(f"Transcript written to {out_path}", file=sys.stderr)

    print(text)


if __name__ == "__main__":
    main()
