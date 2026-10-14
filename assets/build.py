#!/usr/bin/env python3
"""Build the 1280x640 social preview with Pillow.

uv run --python 3.13 --with Pillow==11.3.0 assets/build.py
"""

import argparse
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1280, 640
BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#7ee787"


def build():
    im = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(im)
    title = ImageFont.load_default(size=64)
    body = ImageFont.load_default(size=32)
    draw.text((80, 180), "agent-he", fill=ACCENT, font=title)
    draw.text(
        (80, 280),
        "Heuristic evaluation, run by an agent,",
        fill=FG,
        font=body,
    )
    draw.text(
        (80, 330),
        "with measured evidence.",
        fill=FG,
        font=body,
    )
    draw.text(
        (80, 520),
        "trycopilotai/agent-he",
        fill=MUTED,
        font=body,
    )
    return im


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    im = build()
    out = HERE / "social-preview.png"
    if args.check:
        existing = Image.open(out)
        if list(existing.getdata()) != list(im.getdata()):
            raise SystemExit("social-preview drift")
        print("social-preview matches")
        return
    im.save(out, format="PNG")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    (HERE / "social-preview.sha256").write_text(digest + "\n")
    print("wrote", out, digest)


if __name__ == "__main__":
    main()
