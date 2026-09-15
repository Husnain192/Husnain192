"""Render the public GitHub contribution calendar with Python's standard library.

One public HTML request per refresh; no API token or third-party card service.
Fail before replacing the SVG if GitHub changes its markup or returns bad data.
"""
import argparse
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.request import Request, urlopen


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tips = {}
        self.tip = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs:
            self.cells[attrs["id"]] = (date.fromisoformat(attrs["data-date"]), int(attrs["data-level"]))
        if tag == "tool-tip":
            self.tip = attrs.get("for")
            if self.tip:
                self.tips[self.tip] = ""

    def handle_data(self, data):
        if self.tip:
            self.tips[self.tip] += data

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.tip = None


def parse_calendar(source):
    parser = CalendarParser()
    parser.feed(source)
    days = []
    for key, (day, level) in parser.cells.items():
        match = re.match(r"\s*(No|[\d,]+) contributions? on ", parser.tips.get(key, ""))
        if not match or level not in range(5):
            raise ValueError("Unrecognized contribution cell; preserving previous graph")
        count = 0 if match[1] == "No" else int(match[1].replace(",", ""))
        days.append((day, count, level))
    days.sort()
    if not 365 <= len(days) <= 371:
        raise ValueError("Expected a full year of contribution data")
    if any(b[0] - a[0] != timedelta(days=1) for a, b in zip(days, days[1:])):
        raise ValueError("Contribution dates are not consecutive")
    if not 0 <= (date.today() - days[-1][0]).days <= 2:
        raise ValueError("Contribution data is stale or in the future")
    return days


def render(days, username):
    colors = ["#33352f", "#465c30", "#648a36", "#8aba3d", "#a6e22e"]
    total = sum(count for _, count, _ in days)
    active = sum(count > 0 for _, count, _ in days)
    best = max(count for _, count, _ in days)
    longest = run = 0
    for _, count, _ in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="320" viewBox="0 0 900 320" role="img" aria-labelledby="title desc">',
           f'<title id="title">{escape(username)} — contribution activity</title>',
           f'<desc id="desc">{total:,} contributions across {active} active days. Longest streak: {longest} days. {days[0][0]} to {days[-1][0]}.</desc>',
           '<rect x="1" y="1" width="898" height="318" rx="18" fill="#272822" stroke="#46483e"/>',
           '<g font-family="Segoe UI,Arial,sans-serif">']

    def text(x, y, value, size=12, color="#a7aa9c", weight="400"):
        out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(str(value))}</text>')

    text(28, 32, "HUSNAIN / CONTRIBUTION ACTIVITY", 12, "#a6e22e", "600")
    text(28, 66, f"{total:,} contributions", 27, "#f8f8f2", "700")
    text(28, 89, f"{days[0][0]:%d %b %Y} — {days[-1][0]:%d %b %Y} · Public profile activity")
    start = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
    month = None
    for day, count, level in days:
        delta = (day - start).days
        col, row = divmod(delta, 7)
        x, y = 60 + col * 15, 128 + row * 15
        if day.month != month and (day.day <= 7 or month is None):
            if col < 51:
                text(x, 117, day.strftime("%b"), 10)
            month = day.month
        out.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{colors[level]}"><title>{day}: {count} contributions</title></rect>')
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        text(28, 137 + row * 15, label, 10)
    text(690, 250, "Less", 10)
    for i, color in enumerate(colors):
        out.append(f'<rect x="{720 + i * 16}" y="240" width="11" height="11" rx="2" fill="{color}"/>')
    text(806, 250, "More", 10)
    text(28, 282, f"{active} active days", 14, "#f8f8f2", "600")
    text(235, 282, f"{longest}-day best streak", 14, "#f8f8f2", "600")
    text(475, 282, f"{best} best day", 14, "#f8f8f2", "600")
    text(28, 305, f"Updated {date.today().isoformat()} UTC · Refreshed daily · Generated in this repository", 10)
    out.append('</g></svg>')
    return "\n".join(out) + "\n"


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--username", default="Husnain192")
    cli.add_argument("--input", type=Path, help="Use a saved public contribution HTML page")
    cli.add_argument("--output", type=Path, default=Path("assets/contributions.svg"))
    args = cli.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]+", args.username):
        raise ValueError("Invalid GitHub username")
    if args.input:
        source = args.input.read_text()
    else:
        request = Request(f"https://github.com/users/{args.username}/contributions", headers={"User-Agent": "profile-contribution-graph", "Accept-Language": "en-US"})
        with urlopen(request, timeout=30) as response:
            source = response.read().decode("utf-8")
    days = parse_calendar(source)
    svg = render(days, args.username)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(svg)
    temporary.replace(args.output)
    print(f"Generated {len(days)} days, {sum(d[1] for d in days)} contributions")


if __name__ == "__main__":
    main()
