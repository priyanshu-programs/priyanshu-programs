#!/usr/bin/env python3
"""Write info-card.svg, a neofetch-style panel whose lines print in one by one.

Edit SECTIONS to change the content. STATIC=1 emits a frozen frame for previews.
"""
import os
import pathlib
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(os.environ.get("OUT", ROOT / "info-card.svg"))
STATIC = os.environ.get("STATIC") == "1"

TITLE = "priyanshu@github"
SECTIONS = [
    ("Role", ["Website Designer & Web Developer"]),
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
        "Stack",
        [
            "TypeScript, Next.js, React",
            "Python, FastAPI, LangChain",
            "PostgreSQL",
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
    ("Web", ["priyanshuroy.com", "kinetiq.runs-on.dev"]),
]

# Rendered at width 490 beside the 370-wide square portrait, so 680 x 514 makes
# both columns the same height in the README.
W, H = 680, 514
PAD = 30
LINE, GAP = 26, 8
KEY_X, VAL_X = PAD, PAD + 150
BG, BORDER, KEY, VAL = "#0d1117", "#30363d", "#39d353", "#d7dde4"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
STAGGER, DUR = 0.16, 0.45


def main():
    y = PAD + 62
    delay = 0.0
    lines = []
    for key, values in SECTIONS:
        for i, value in enumerate(values):
            k = f'<text x="{KEY_X}" y="{y}" fill="{KEY}" font-weight="700">{escape(key)}</text>' if i == 0 else ""
            row = f'{k}<text x="{VAL_X}" y="{y}" fill="{VAL}">{escape(value)}</text>'
            lines.append(f"<g>{row}</g>" if STATIC else f'<g class="l" style="animation-delay:{delay:.2f}s">{row}</g>')
            delay += STAGGER
            y += LINE
        y += GAP

    if y > H:
        raise SystemExit(f"content overflows the card: needs {y}px, has {H}px")

    style = ""
    if not STATIC:
        style = (
            "<style>.l{opacity:0;transform:translateY(6px);"
            f"animation:p {DUR}s ease-out forwards}}"
            "@keyframes p{to{opacity:1;transform:none}}</style>"
        )

    header = (
        f'<text x="{PAD}" y="{PAD + 12}" fill="{KEY}" font-weight="700" font-size="22">{TITLE}</text>'
        f'<line x1="{PAD}" x2="{W - PAD}" y1="{PAD + 28}" y2="{PAD + 28}" stroke="{BORDER}" stroke-width="2"/>'
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Priyanshu Roy: role, projects, stack and highlights">{style}'
        f'<rect width="100%" height="100%" rx="12" fill="{BG}"/>'
        f'<g font-family="{FONT}" font-size="18">{header}{"".join(lines)}</g></svg>'
    )
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
