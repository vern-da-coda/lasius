#!/usr/bin/env python3
"""
Lasius Hexapod Audio Briefing Generator (`scripts/dev/generate_audio_briefing.py`).

Purpose & Role:
    Converts the domain documentation podcast manuscript (`docs/audio_briefing_domain.md`)
    into high-quality spoken audio (MP3) using Microsoft Edge Neural TTS.

Usage:
    python3 scripts/dev/generate_audio_briefing.py             # Generates data/audio/lasius_domain_briefing.mp3
    python3 scripts/dev/generate_audio_briefing.py --voice de-DE-FlorianMultilingualNeural
    python3 scripts/dev/generate_audio_briefing.py --play     # Generate and start playback immediately
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import re
import shutil
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

try:
    import edge_tts
except ImportError:
    print("❌ Error: edge-tts is not installed. Run: uv pip install edge-tts")
    sys.exit(1)


def clean_markdown_for_speech(content: str) -> str:
    """Prepares Markdown text for natural Text-to-Speech narration."""
    lines = content.splitlines()
    cleaned_lines = []
    skip_header = True

    for line in lines:
        stripped = line.strip()

        # Skip initial navigation links and disclaimers before the real text
        if skip_header:
            if stripped.startswith("## Willkommen zum Lasius Deep Dive"):
                skip_header = False
                cleaned_lines.append("Lasius Hexapod. Das Große Audio-Briefing.")
                cleaned_lines.append("")
                cleaned_lines.append("Willkommen zum Lasius Deep Dive.")
            continue

        # Skip horizontal dividers
        if stripped in ["---", "***", "___"]:
            cleaned_lines.append("")
            continue

        # Replace markdown headers with clean pauses / spoken section titles
        if stripped.startswith("#"):
            header_text = re.sub(r"^#+\s*", "", stripped)
            cleaned_lines.append("")
            cleaned_lines.append(f"{header_text}.")
            cleaned_lines.append("")
            continue

        # Remove markdown emphasis symbols (*, _)
        cleaned = re.sub(r"[*_]{1,2}(.*?)[*_]{1,2}", r"\1", stripped)
        # Remove markdown links: [text](url) -> text
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)

        cleaned_lines.append(cleaned)

    return "\n".join(cleaned_lines)


async def synthesize_audio(text: str, voice: str, output_mp3: Path, output_vtt: Path):
    print(f"🎙️ Synthesizing speech with voice: {voice}")
    print(f"📄 Text length: {len(text):,} characters (~{len(text.split()):,} words)")
    print(f"💾 Target output: {output_mp3}")

    output_mp3.parent.mkdir(parents=True, exist_ok=True)

    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()

    with open(output_mp3, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    try:
        subs = submaker.generate_subs()
        with open(output_vtt, "w", encoding="utf-8") as file:
            file.write(subs)
        print(f"📝 Subtitles saved to: {output_vtt}")
    except Exception:
        pass

    size_mb = output_mp3.stat().st_size / (1024 * 1024)
    print(f"✅ Audio generation complete! File size: {size_mb:.2f} MB")


def play_audio(mp3_path: Path):
    print(f"\n▶ Starting playback of {mp3_path}...")
    if shutil.which("ffplay"):
        subprocess.run(["ffplay", "-nodisp", "-autoexit", str(mp3_path)])
    elif shutil.which("cvlc"):
        subprocess.run(["cvlc", "--play-and-exit", str(mp3_path)])
    elif shutil.which("paplay"):
        subprocess.run(["paplay", str(mp3_path)])
    else:
        print("ℹ️ Kein Standard-Player (ffplay/cvlc) gefunden. Öffne die Datei manuell mit deinem Mediaplayer.")


def main():
    parser = argparse.ArgumentParser(description="Generate Lasius Audio Briefing with Edge-TTS")
    parser.add_argument(
        "--input",
        type=str,
        default=str(REPO_ROOT / "docs/audio_briefing_domain.md"),
        help="Input markdown manuscript path",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(REPO_ROOT / "data/audio/lasius_domain_briefing.mp3"),
        help="Output MP3 file path",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default="de-DE-KillianNeural",
        help="Neural voice (default: de-DE-KillianNeural, alt: de-DE-FlorianMultilingualNeural, de-DE-SeraphinaMultilingualNeural)",
    )
    parser.add_argument(
        "--play",
        action="store_true",
        help="Play audio file immediately after synthesis finishes",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_mp3 = Path(args.output)
    output_vtt = output_mp3.with_suffix(".vtt")

    if not input_path.is_file():
        print(f"❌ Error: Input file not found at '{input_path}'")
        sys.exit(1)

    raw_text = input_path.read_text(encoding="utf-8")
    spoken_text = clean_markdown_for_speech(raw_text)

    asyncio.run(synthesize_audio(spoken_text, args.voice, output_mp3, output_vtt))

    if args.play:
        play_audio(output_mp3)


if __name__ == "__main__":
    main()
