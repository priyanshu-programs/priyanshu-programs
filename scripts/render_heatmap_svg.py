#!/usr/bin/env python3
"""Render data/contributions.json as contrib-heatmap.svg.

Boxes slide in along a diagonal on load, then freeze. STATIC=1 emits a frozen
frame for previews.
"""
import datetime as dt
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(os.environ.get("OUT", ROOT / "contrib-heatmap.svg"))
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG, TEXT, DIM = "#0d1117", "#d7dde4", "#8b949e"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
CELL, STEP = 12, 15
LEFT, TOP = 44, 44
DIAGONAL_DELAY, DUR = 0.022, 0.4


def levels(days):
    """GitHub's 0-4 levels, plus a neon level 5 for the busiest ~2% of active days."""
    counts = sorted(d["count"] for d in days if d["count"])
    cutoff = counts[int(len(counts) * 0.98)] if len(counts) >= 10 else None
    return [5 if cutoff and d["count"] >= cutoff and d["level"] == 4 else d["level"] for d in days]


def main():
    data = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))
    days = data["days"]
    first = dt.date.fromisoformat(days[0]["date"])
    start_offset = (first.weekday() + 1) % 7  # calendar columns start on Sunday

    cells, months = [], []
    last_month, last_label_week = None, -9
    weeks = 0
    for i, (day, level) in enumerate(zip(days, levels(days))):
        date = dt.date.fromisoformat(day["date"])
        pos = i + start_offset
        week, weekday = pos // 7, pos % 7
        weeks = max(weeks, week + 1)
        x, y = LEFT + week * STEP, TOP + weekday * STEP
        anim = "" if STATIC else f' class="c" style="animation-delay:{(week + weekday) * DIAGONAL_DELAY:.2f}s"'
        cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{PALETTE[level]}"{anim}/>')
        if date.month != last_month and weekday == 0 or (i == 0 and date.day < 15):
            if week - last_label_week >= 3:
                months.append(f'<text x="{x}" y="{TOP - 12}" fill="{DIM}">{date:%b}</text>')
                last_label_week = week
            last_month = date.month

    w = LEFT + weeks * STEP + 18
    grid_bottom = TOP + 7 * STEP
    h = grid_bottom + 62

    day_labels = "".join(
        f'<text x="12" y="{TOP + row * STEP + 10}" fill="{DIM}">{name}</text>'
        for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    legend_x = w - 18 - STEP * len(PALETTE) - 42
    legend_y = grid_bottom + 28
    legend = (
        f'<text x="{legend_x - 38}" y="{legend_y + 10}" fill="{DIM}">Less</text>'
        + "".join(
            f'<rect x="{legend_x + n * STEP}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="3" fill="{color}"/>'
            for n, color in enumerate(PALETTE)
        )
        + f'<text x="{legend_x + len(PALETTE) * STEP + 6}" y="{legend_y + 10}" fill="{DIM}">More</text>'
    )
    best = data["best_day"]
    best_label = f"{dt.date.fromisoformat(best['date']):%b} {int(best['date'][8:])}"
    footer = (
        f'<text x="{LEFT}" y="{legend_y + 10}" fill="{TEXT}">{data["total"]:,} contributions in the last year</text>'
        f'<text x="{LEFT + 330}" y="{legend_y + 10}" fill="{DIM}">'
        f'streak {data["current_streak"]}d | longest {data["longest_streak"]}d | best {best["count"]} on {best_label}</text>'
    )

    style = "" if STATIC else (
        "<style>.c{opacity:0;transform:translateY(-8px);"
        f"animation:d {DUR}s ease-out forwards}}"
        "@keyframes d{to{opacity:1;transform:none}}</style>"
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
        f'aria-label="{data["total"]:,} GitHub contributions in the last year">{style}'
        f'<rect width="100%" height="100%" rx="12" fill="{BG}"/>'
        f'<g font-family="{FONT}" font-size="11">{"".join(months)}{day_labels}{"".join(cells)}{legend}{footer}</g></svg>'
    )
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB, {weeks} weeks)")


if __name__ == "__main__":
    main()
