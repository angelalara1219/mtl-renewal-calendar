"""Write the weekly licensing report (Markdown) and a calendar file (.ics).

Usage:
    python -m renewal_calendar.report                    # as of today
    python -m renewal_calendar.report --as-of 2026-11-18 --horizon 90
"""

import argparse
import hashlib
from collections import Counter
from datetime import date
from pathlib import Path

from .build import bucket, collect, load_settings

BUCKETS = ["Overdue", "Due within 30 days", "Due in 31-60 days", "Due in 61-90 days"]


def _cell(text):
    return (text or "").replace("|", "/")


def markdown(deadlines, as_of, company, horizon):
    counts = Counter(bucket(d, as_of) for d in deadlines)
    lines = [
        f"# Licensing calendar: {company}",
        "",
        f"As of {as_of.isoformat()}, looking {horizon} days ahead. All data is synthetic.",
        "",
        "| Status | Count |",
        "|---|---|",
    ]
    lines += [f"| {b} | {counts.get(b, 0)} |" for b in BUCKETS]
    for b in BUCKETS:
        group = [d for d in deadlines if bucket(d, as_of) == b]
        if not group:
            continue
        lines += ["", f"## {b}", "",
                  "| Due | Days | Type | State | Item | Owner | Note |",
                  "|---|---|---|---|---|---|---|"]
        for d in group:
            lines.append(
                f"| {d.due.isoformat()} | {(d.due - as_of).days} | {d.category} | {d.state} "
                f"| {_cell(d.item)} | {_cell(d.owner)} | {_cell(d.note)} |"
            )
    return "\n".join(lines) + "\n"


def _ics_text(text):
    return (text or "").replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def ics(deadlines, company):
    """All-day calendar events, each with a reminder 14 days before."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//mtl-renewal-calendar//EN", f"X-WR-CALNAME:{_ics_text(company)} licensing"]
    for d in deadlines:
        uid = hashlib.sha1(f"{d.due}{d.category}{d.state}{d.item}".encode()).hexdigest()[:16]
        summary = f"[{d.state}] {d.category}: {d.item}"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}@mtl-renewal-calendar",
            f"DTSTAMP:{d.due.strftime('%Y%m%d')}T000000Z",
            f"DTSTART;VALUE=DATE:{d.due.strftime('%Y%m%d')}",
            f"SUMMARY:{_ics_text(summary)}",
            f"DESCRIPTION:{_ics_text(' | '.join(x for x in (d.owner, d.note) if x))}",
            "BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:-P14D",
            f"DESCRIPTION:{_ics_text(summary)}", "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--horizon", type=int, default=None, help="days ahead (default from settings)")
    parser.add_argument("--data", default="data")
    parser.add_argument("--out", default="reports")
    args = parser.parse_args(argv)

    settings = load_settings(args.data)
    horizon = args.horizon or int(settings.get("horizon_days", 90))
    deadlines = collect(args.data, args.as_of, horizon)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest.md").write_text(markdown(deadlines, args.as_of, settings["company"], horizon), encoding="utf-8")
    (out / "licensing-calendar.ics").write_text(ics(deadlines, settings["company"]), encoding="utf-8", newline="")
    counts = Counter(bucket(d, args.as_of) for d in deadlines)
    print(f"{len(deadlines)} deadlines: " + ", ".join(f"{b}: {counts.get(b, 0)}" for b in BUCKETS))


if __name__ == "__main__":
    main()
