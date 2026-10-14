#!/usr/bin/env python3
"""Abridged reconstruction from the fixture inventory transcript.

uv run --python 3.13 --with Pillow==11.3.0 assets/build_demo.py
Add --check to compare deterministic rebuilds without writing.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "evidence/inventory/2026-10-13-fixture-inventory.txt"
BG, FG, MUTED, FAIL, OK = (
    "#0d1117",
    "#e6edf3",
    "#8b949e",
    "#ffa657",
    "#7ee787",
)
WIDTH, HEIGHT = 1500, 1400
FONT = ImageFont.load_default(size=26)
SMALL = ImageFont.load_default(size=22)


def session_lines(text):
    lines = [
        ("agent-he / v0.1.0", FG),
        (
            "Abridged reconstruction of the fixture inventory; not a screen recording",
            MUTED,
        ),
    ]
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("http://"):
            lines.append((stripped, FG))
        elif "FINDING" in stripped:
            lines.append((stripped, FAIL))
        elif stripped.startswith("lang:"):
            lines.append((stripped, OK))
        elif stripped.startswith("title:"):
            lines.append((stripped[:90], MUTED))
        elif stripped.startswith("social:"):
            lines.append((stripped, OK))
    # Cap for the canvas.
    return lines[:28]


def render(lines, visible):
    im = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(im)
    y = 55
    for index, (line, color) in enumerate(lines):
        if index >= visible:
            break
        if line.startswith("http://") and index > 1:
            y += 20
        visible_text = line.replace("—", "-").replace("→", "->")
        # Keep literal &#8211; so FINDING lines still show the
        # raw-entity defect the inventory reported.
        if "FINDING" not in line:
            visible_text = visible_text.replace("–", "-")
        draw.text(
            (60, y),
            visible_text,
            fill=color,
            font=FONT if index < 2 else SMALL,
        )
        y += 48 if index == 0 else 36
    assert y < HEIGHT - 45, "completed session exceeds the canvas"
    draw.text(
        (60, HEIGHT - 48),
        "Source: evidence/inventory/2026-10-13-fixture-inventory.txt",
        font=SMALL,
        fill=MUTED,
    )
    return im


def build():
    lines = session_lines(SOURCE.read_text())
    first_finding = next(
        i for i, (line, _) in enumerate(lines) if "FINDING" in line
    )
    good = next(i for i, (line, _) in enumerate(lines) if "good.html" in line)
    visible = [2, first_finding + 1, good + 2, len(lines)]
    frames = [render(lines, count) for count in visible]
    gif, poster = io.BytesIO(), io.BytesIO()
    frames[0].save(
        gif,
        format="GIF",
        append_images=frames[1:],
        save_all=True,
        duration=[1000, 2000, 2000, 5000],
        loop=0,
        optimize=False,
        disposal=1,
    )
    frames[-1].save(poster, format="PNG")
    assets = {"demo.gif": gif.getvalue(), "demo-poster.png": poster.getvalue()}
    manifest = {
        "kind": "abridged reconstruction of a fixture inventory",
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "dependency": "Pillow==11.3.0",
        "canvas": [WIDTH, HEIGHT],
        "cumulative_visible_lines": visible,
        "loop": 0,
        "assets": {
            name: hashlib.sha256(data).hexdigest() for name, data in assets.items()
        },
    }
    assets["demo.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return assets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    assets = build()
    if args.check:
        for name, data in assets.items():
            existing = (HERE / name).read_bytes()
            if existing != data:
                raise SystemExit(f"drift: {name}")
        print("demo assets match")
        return
    for name, data in assets.items():
        (HERE / name).write_bytes(data)
        print("wrote", name, len(data))


if __name__ == "__main__":
    main()
