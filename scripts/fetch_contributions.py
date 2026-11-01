#!/usr/bin/env python3
"""Scrape the public contribution calendar into data/contributions.json.

Uses the same unauthenticated HTML fragment the profile page loads, so it needs
no token. Fails loudly if GitHub's markup changes, so a bad scrape can never
overwrite good data with an empty graph.
"""
import collections
import json
import os
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "priyanshu-programs")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tooltips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        date = cell.get("data-date")
        if not date:
            continue
        match = re.match(r"([\d,]+) contribution", tooltips.get(cell.get("id"), ""))
        days.append(
            {
                "date": date,
                "count": int(match.group(1).replace(",", "")) if match else 0,
                "level": int(cell.get("data-level") or 0),
            }
        )
    if not days:
        sys.exit("no calendar cells found: GitHub's markup may have changed")
    days.sort(key=lambda d: d["date"])

    heading = soup.find("h2", id="js-contribution-activity-description") or soup.find("h2")
    match = re.search(r"([\d,]+)\s+contributions?", heading.get_text(" ", strip=True)) if heading else None
    reported = int(match.group(1).replace(",", "")) if match else None
    return days, reported


def streaks(days):
    longest = run = 0
    for day in days:
        run = run + 1 if day["count"] else 0
        longest = max(longest, run)

    current = 0
    # Today isn't over yet, so an empty today doesn't break the streak.
    tail = days[:-1] if days[-1]["count"] == 0 else days
    for day in reversed(tail):
        if not day["count"]:
            break
        current += 1
    return current, longest


def main():
    days, reported = fetch()
    total = sum(d["count"] for d in days)
    if reported is not None and reported != total:
        sys.exit(f"scraped total {total} does not match GitHub's reported {reported}")

    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    monthly = collections.Counter()
    for day in days:
        monthly[day["date"][:7]] += day["count"]

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "username": USERNAME,
                "total": total,
                "current_streak": current,
                "longest_streak": longest,
                "best_day": {"date": best["date"], "count": best["count"]},
                "monthly": dict(sorted(monthly.items())),
                "days": days,
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"{len(days)} days, {total} contributions (GitHub reports {reported}), streak {current}, longest {longest}")


if __name__ == "__main__":
    main()
