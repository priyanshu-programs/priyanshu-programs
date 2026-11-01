#!/usr/bin/env python3
"""Write info-card.svg, a two-column neofetch-style panel whose lines print in one by one.

Edit LEFT and RIGHT to change the content. STATIC=1 emits a frozen frame for previews.
"""
import os
import pathlib
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(os.environ.get("OUT", ROOT / "info-card.svg"))
STATIC = os.environ.get("STATIC") == "1"

TITLE = "priyanshu@github"
LEFT = [
    ("Role", ["Website Designer & Web Developer"]),
    ("Stack", ["TypeScript, Next.js, React", "Python, FastAPI, LangChain", "PostgreSQL"]),
    ("Web", ["priyanshuroy.com", "kinetiq.runs-on.dev"]),
]
RIGHT = [
    (
        "Building",
        [
            "Touchpoint - self-hostable business OS",
            "Tably - AI-native CRM",
            "Kinetiq - AI personal trainer",
            "Splintr - AI content syndication",
            "Lexio - RAG document chatbot",
        ],
    ),
    (
        "Highlights",
        [
            "Smart Bengal Hackathon Finalist '25",
            "(finals from 800+ submissions)",
            "Edunet x IBM Internship",
        ],
    ),
]

# Drawn 1:1 at the README's 860 width.
W = 860
PAD = 24
LINE, GAP = 23, 10
TOP = PAD + 54
COLUMNS = ((LEFT, PAD, PAD + 70), (RIGHT, 384, 484))  # (sections, key x, value x)
BG, BORDER, KEY, VAL = "#0d1117", "#30363d", "#39d353", "#d7dde4"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
STAGGER, DUR = 0.12, 0.45


def main():
    lines = []
    delay = 0.0
    bottom = TOP
    for sections, key_x, val_x in COLUMNS:
        y = TOP
        for key, values in sections:
            for i, value in enumerate(values):
                k = f'<text x="{key_x}" y="{y}" fill="{KEY}" font-weight="700">{escape(key)}</text>' if i == 0 else ""
                row = f'{k}<text x="{val_x}" y="{y}" fill="{VAL}">{escape(value)}</text>'
                lines.append(f"<g>{row}</g>" if STATIC else f'<g class="l" style="animation-delay:{delay:.2f}s">{row}</g>')
                delay += STAGGER
                y += LINE
            y += GAP
        bottom = max(bottom, y)
    height = bottom - GAP - LINE + PAD + 6

    style = ""
    if not STATIC:
        style = (
            "<style>.l{opacity:0;transform:translateY(6px);"
            f"animation:p {DUR}s ease-out forwards}}"
            "@keyframes p{to{opacity:1;transform:none}}</style>"
        )

    header = (
        f'<text x="{PAD}" y="{PAD + 12}" fill="{KEY}" font-weight="700" font-size="17">{TITLE}</text>'
        f'<line x1="{PAD}" x2="{W - PAD}" y1="{PAD + 26}" y2="{PAD + 26}" stroke="{BORDER}"/>'
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" '
        f'role="img" aria-label="Priyanshu Roy: role, projects, stack and highlights">{style}'
        f'<rect width="100%" height="100%" rx="12" fill="{BG}"/>'
        f'<g font-family="{FONT}" font-size="14">{header}{"".join(lines)}</g></svg>'
    )
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB, {W}x{height})")


if __name__ == "__main__":
    main()
