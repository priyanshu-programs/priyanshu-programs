#!/usr/bin/env python3
"""Render data/contributions.json as stats.svg: six number tiles and a monthly bar chart.

Tiles fade in and count up, then the bars grow from the baseline. It plays once
and freezes. STATIC=1 emits the finished frame for previews.
"""
import datetime as dt
import json
import os
import pathlib
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(os.environ.get("OUT", ROOT / "stats.svg"))
STATIC = os.environ.get("STATIC") == "1"

BG, TILE, FRAME = "#0d1117", "#161b22", "#30363d"
INK, MUTED = "#e6edf3", "#8b949e"
BAR = "#26a641"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"

# Same square as portrait.svg, so the two README columns match in height.
W = H = 880
PAD, GAP = 24, 16
TITLEBAR = 48
TILE_W = (W - PAD * 2 - GAP) / 2
TILE_H = 124
TILES_TOP = TITLEBAR + 16
CHART_TOP = TILES_TOP + 3 * TILE_H + 2 * GAP + GAP
CHART_H = H - PAD - CHART_TOP

BAR_MAX_W, BAR_RADIUS, BAR_MIN_H = 44, 8, 8
TILE_STAGGER, TILE_DUR = 0.14, 0.45
COUNT_DUR, COUNT_FRAMES = 1.0, 14
BAR_STAGGER, BAR_DUR = 0.06, 0.55


def date_of(iso):
    return dt.date.fromisoformat(iso)


def short(iso):
    d = date_of(iso)
    return f"{d:%b} {d.day}"


def span_text(span):
    if not span:
        return "no active streak"
    start, end = span
    return short(start) if start == end else f"{short(start)} - {short(end)}"


def fmt(value, decimals):
    return f"{value:,.{decimals}f}"


def value_markup(x, y, value, suffix, decimals, begin):
    """The tile's big number. When animated, it's a stack of frames shown in turn."""
    suffix_tag = f'<tspan font-size="26" fill="{MUTED}">{escape(suffix)}</tspan>' if suffix else ""
    attrs = f'x="{x:.1f}" y="{y:.1f}" fill="{INK}" font-size="50" font-weight="700"'
    if STATIC:
        return f"<text {attrs}>{fmt(value, decimals)}{suffix_tag}</text>"

    frames = []
    for k in range(1, COUNT_FRAMES + 1):
        shown = fmt(value * k / COUNT_FRAMES, decimals)
        if not frames or frames[-1] != shown:
            frames.append(shown)

    step = COUNT_DUR / len(frames)
    parts = []
    for i, shown in enumerate(frames):
        on = begin + i * step
        anim = f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>'
        if i < len(frames) - 1:
            anim += f'<set attributeName="opacity" to="0" begin="{on + step:.3f}s"/>'
        parts.append(f'<text {attrs} opacity="0">{shown}{suffix_tag}{anim}</text>')
    return "".join(parts)


def tiles_markup(data):
    days = data["days"]
    active = data["active_days"]
    best = data["best_day"]
    avg = data["total"] / active if active else 0
    tiles = [
        ("current streak", data["current_streak"], " days", 0, span_text(data["current_span"])),
        ("longest streak", data["longest_streak"], " days", 0, span_text(data["longest_span"])),
        ("contributions", data["total"], "", 0, "in the last year"),
        ("active days", active, f" / {len(days)}", 0, f"{active / len(days):.0%} of the year"),
        ("best day", best["count"], "", 0, short(best["date"])),
        ("avg / active day", avg, "", 1, "contributions"),
    ]
    parts = []
    for i, (label, value, suffix, decimals, caption) in enumerate(tiles):
        x = PAD + (i % 2) * (TILE_W + GAP)
        y = TILES_TOP + (i // 2) * (TILE_H + GAP)
        begin = i * TILE_STAGGER
        anim = "" if STATIC else f' class="f" style="animation-delay:{begin:.2f}s"'
        parts.append(
            f"<g{anim}>"
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" fill="{TILE}"/>'
            f'<text x="{x + 20:.1f}" y="{y + 31:.1f}" fill="{MUTED}" font-size="19">$ {escape(label)}</text>'
            f'<text x="{x + 20:.1f}" y="{y + 108:.1f}" fill="{MUTED}" font-size="18">{escape(caption)}</text>'
            "</g>"
            + value_markup(x + 20, y + 80, value, suffix, decimals, begin)
        )
    return "".join(parts)


def bar_path(x, width, bottom, height):
    """Rounded at the data end, square at the baseline."""
    r = min(BAR_RADIUS, height, width / 2)
    top = bottom - height
    return (
        f"M{x:.1f} {bottom:.1f}V{top + r:.1f}Q{x:.1f} {top:.1f} {x + r:.1f} {top:.1f}"
        f"H{x + width - r:.1f}Q{x + width:.1f} {top:.1f} {x + width:.1f} {top + r:.1f}V{bottom:.1f}Z"
    )


def chart_markup(data):
    monthly = list(data["monthly"].items())
    peak = max(count for _, count in monthly) or 1
    days = data["days"]
    x0, x1 = PAD + 20, W - PAD - 20
    top, bottom = CHART_TOP + 88, CHART_TOP + CHART_H - 46
    slot = (x1 - x0) / len(monthly)
    bar_w = min(BAR_MAX_W, slot - 2)
    start_at = 6 * TILE_STAGGER + 0.5

    parts = [
        f'<rect x="{PAD}" y="{CHART_TOP}" width="{W - PAD * 2}" height="{CHART_H}" rx="10" fill="{TILE}"/>',
        f'<text x="{x0}" y="{CHART_TOP + 33}" fill="{MUTED}" font-size="19">$ contributions / month</text>',
        f'<text x="{x1}" y="{CHART_TOP + 33}" fill="{MUTED}" font-size="17" text-anchor="end">'
        f'{date_of(days[0]["date"]):%b %Y} - {date_of(days[-1]["date"]):%b %Y}</text>',
        f'<line x1="{x0}" x2="{x1}" y1="{bottom + 0.5}" y2="{bottom + 0.5}" stroke="{FRAME}"/>',
    ]
    for i, (month, count) in enumerate(monthly):
        cx = x0 + slot * (i + 0.5)
        parts.append(
            f'<text x="{cx:.1f}" y="{bottom + 30}" fill="{MUTED}" font-size="18" text-anchor="middle">'
            f'{date_of(month + "-01"):%b}</text>'
        )
        if not count:
            continue  # a zero month draws nothing, so it can't be mistaken for a small one
        height = max(BAR_MIN_H, (bottom - top) * count / peak)
        delay = start_at + i * BAR_STAGGER
        anim = "" if STATIC else f' class="b" style="animation-delay:{delay:.2f}s"'
        parts.append(f'<path d="{bar_path(cx - bar_w / 2, bar_w, bottom, height)}" fill="{BAR}"{anim}/>')
        if count == peak:
            fade = "" if STATIC else f' class="f" style="animation-delay:{delay + BAR_DUR:.2f}s"'
            parts.append(
                f'<text x="{cx:.1f}" y="{bottom - height - 12:.1f}" fill="{INK}" font-size="20" font-weight="700" '
                f'text-anchor="middle"{fade}>{count:,}</text>'
            )
    return "".join(parts)


def main():
    data = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))

    style = "" if STATIC else (
        f"<style>.f{{opacity:0;animation:fi {TILE_DUR}s ease-out forwards}}"
        f".b{{transform:scaleY(0);transform-box:fill-box;transform-origin:50% 100%;"
        f"animation:gr {BAR_DUR}s ease-out forwards}}"
        "@keyframes fi{to{opacity:1}}@keyframes gr{to{transform:scaleY(1)}}</style>"
    )
    dots = "".join(
        f'<circle cx="{PAD + 8 + n * 22}" cy="{TITLEBAR / 2 + 2}" r="7" fill="{color}"/>'
        for n, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f"))
    )
    months = ", ".join(f"{date_of(m + '-01'):%b %Y} {c}" for m, c in data["monthly"].items())
    label = (
        f'{data["total"]} contributions in the last year. Current streak {data["current_streak"]} days, '
        f'longest {data["longest_streak"]} days, {data["active_days"]} active days. By month: {months}.'
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(label)}">{style}'
        f'<rect width="100%" height="100%" rx="12" fill="{BG}"/>'
        f'<g font-family="{FONT}">{dots}'
        f'<text x="{W / 2}" y="{TITLEBAR / 2 + 8}" fill="{MUTED}" font-size="19" text-anchor="middle">'
        f"priyanshu@github: ~$ ./stats.sh</text>"
        f"{tiles_markup(data)}{chart_markup(data)}</g></svg>"
    )
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
