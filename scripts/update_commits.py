"""Generate a monthly commit line chart, using GitHub commit-search counts."""
import argparse
import calendar
from datetime import date, datetime, timezone
from html import escape
import json
import math
import os
from pathlib import Path
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def month_ranges(today):
    current = today.year * 12 + today.month - 1
    for serial in range(current - 11, current + 1):
        year, month = divmod(serial, 12)
        month += 1
        start = date(year, month, 1)
        end = min(today, date(year, month, calendar.monthrange(year, month)[1]))
        yield start, end


def collect(username, today):
    token = os.environ.get("PROFILE_STATS_TOKEN") or os.environ.get("GH_TOKEN")
    include_private = bool(os.environ.get("PROFILE_STATS_TOKEN"))
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "custom-commit-graph"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    months = []
    for start, end in month_ranges(today):
        # total_count counts all matches, without downloading commit messages or
        # truncating totals at the search endpoint's 1,000 retrievable-item limit.
        visibility = "" if include_private else " is:public"
        query = f"author:{username}{visibility} author-date:{start}..{end}"
        url = "https://api.github.com/search/commits?" + urlencode({"q": query, "per_page": 1})
        with urlopen(Request(url, headers=headers), timeout=45) as response:
            result = json.load(response)
        count = result.get("total_count")
        if result.get("incomplete_results") is not False or type(count) is not int or count < 0:
            raise ValueError("Incomplete commit search; preserving previous graph")
        months.append({"start": str(start), "end": str(end), "commits": count})
        print(f"{start:%b %Y}: {count} commits", flush=True)
        # Stay below search rate limits, including unauthenticated local runs.
        if end != today:
            time.sleep(3 if token else 7)
    return {"username": username, "updated": str(today), "scope": "public_and_private" if include_private else "public", "months": months}


def render(data):
    months = data["months"]
    scope = "Public + accessible private" if data.get("scope") == "public_and_private" else "Public"
    values = [m["commits"] for m in months]
    if len(months) != 12 or any(type(v) is not int or v < 0 for v in values):
        raise ValueError("Expected twelve nonnegative monthly counts")
    peak = max(values)
    step = max(1, math.ceil(peak / 4 / 10) * 10) if peak > 20 else max(1, math.ceil(peak / 4))
    ceiling = step * 4
    left, right, top, bottom = 68, 858, 132, 306
    points = [(left + i * (right - left) / 11, bottom - v / ceiling * (bottom - top)) for i, v in enumerate(values)]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="402" viewBox="0 0 900 402" role="img" aria-labelledby="title desc">',
           f'<title id="title">{escape(data["username"])} — monthly commits</title>',
           f'<desc id="desc">{scope} authored commits, grouped by month. ' + escape('; '.join(f'{m["start"][:7]}: {m["commits"]}' for m in months)) + '. Current month is partial.</desc>',
           '<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#a6e22e" stop-opacity="0.28"/><stop offset="100%" stop-color="#a6e22e" stop-opacity="0.015"/></linearGradient></defs>',
           '<rect x="1" y="1" width="898" height="400" rx="18" fill="#272822" stroke="#46483e"/>',
           '<g font-family="DejaVu Sans,Arial,sans-serif">']

    def text(x, y, value, size=11, color="#a7aa9c", anchor="start", weight="400"):
        out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(value))}</text>')

    text(28, 32, "HUSNAIN / COMMIT ACTIVITY", 12, "#a6e22e", weight="600")
    text(28, 70, f"{sum(values):,} commits", 28, "#f8f8f2", weight="700")
    text(28, 94, "Monthly authored commits · Last 12 calendar months", 12)
    text(858, 55, f"{values[-1]:,}", 24, "#66d9ef", "end", "700")
    text(858, 77, "THIS MONTH SO FAR", 10, anchor="end")
    text(28, 119, "COMMITS", 9)
    for i in range(5):
        v = i * step
        y = bottom - i / 4 * (bottom - top)
        out.append(f'<path d="M {left} {y} H {right}" stroke="#42443a" stroke-dasharray="3 5"/>')
        text(left - 12, y + 4, v, 10, anchor="end")
    path = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in points)
    out.append(f'<path d="{path} L {right} {bottom} L {left} {bottom} Z" fill="url(#area)"/>')
    out.append(f'<path d="{path}" fill="none" stroke="#a6e22e" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
    for i, ((x, y), month) in enumerate(zip(points, months)):
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#272822" stroke="#a6e22e" stroke-width="2"><title>{month["start"][:7]}: {month["commits"]} commits</title></circle>')
        text(x, y - 11, month["commits"], 10, "#f8f8f2", "middle")
        label = date.fromisoformat(month["start"]).strftime("%b") + ("*" if i == 11 else "")
        text(x, 329, label, 11, anchor="middle")
        if i == 0 or month["start"][5:7] == "01":
            text(x, 345, month["start"][:4], 9, anchor="middle")
    text(28, 372, f"{scope} · Default branches · Includes merges · *Partial month", 10)
    text(28, 390, f'Updated {data["updated"]} UTC · Daily snapshot · Source: GitHub commit search', 10)
    out.append('</g></svg>')
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="Husnain192")
    parser.add_argument("--input", type=Path, help="Render an existing monthly JSON snapshot")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]+", args.username):
        raise ValueError("Invalid username")
    today = datetime.now(timezone.utc).date()
    data = json.loads(args.input.read_text()) if args.input else collect(args.username, today)
    svg = render(data)
    Path("assets").mkdir(exist_ok=True)
    for name, content in [("commits.svg", svg), ("commits.json", json.dumps(data, indent=2) + "\n")]:
        path = Path("assets") / name
        temporary = path.with_suffix(".tmp")
        temporary.write_text(content)
        temporary.replace(path)


if __name__ == "__main__":
    main()
