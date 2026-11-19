"""Turn the licensing inventory into one dated list of deadlines."""

import csv
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .escheat import escheat_deadlines

DONE_STATUSES = {"approved", "closed", "filed", "surrendered", "withdrawn"}


@dataclass(frozen=True)
class Deadline:
    due: date
    category: str
    state: str
    item: str
    owner: str = ""
    note: str = ""


def _date(value):
    value = (value or "").strip()
    return date.fromisoformat(value) if value else None


def _rows(data_dir, name):
    path = Path(data_dir) / name
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _open(row):
    return row.get("status", "").strip().lower() not in DONE_STATUSES


def load_settings(data_dir):
    with open(Path(data_dir) / "settings.json", encoding="utf-8") as f:
        return json.load(f)


def quarter_ends(first, last):
    """Every calendar quarter end from `first` through `last`, inclusive."""
    out = []
    for year in range(first.year, last.year + 1):
        for month, day in ((3, 31), (6, 30), (9, 30), (12, 31)):
            q = date(year, month, day)
            if first <= q <= last:
                out.append(q)
    return out


def license_deadlines(data_dir, settings):
    window = settings.get("nmls_renewal_window_opens", "11-01")
    out = []
    for r in _rows(data_dir, "licenses.csv"):
        if not _open(r):
            continue
        exp = _date(r["expiration_date"])
        if exp:
            note = ""
            if r["renewal_via"].strip() == "NMLS":
                note = f"NMLS renewal window opens {exp.year}-{window}"
            out.append(Deadline(exp, "License renewal", r["state"],
                                f"{r['license_type']} renewal ({r['license_id']}, via {r['renewal_via']})",
                                r["owner"], note))
        bond = _date(r["bond_expiration"])
        if bond:
            amount = int(float(r["bond_amount"] or 0))
            out.append(Deadline(bond, "Surety bond", r["state"],
                                f"Renew ${amount:,} surety bond and file the rider",
                                r["owner"]))
    return out


def application_deadlines(data_dir):
    out = []
    for r in _rows(data_dir, "applications.csv"):
        follow_up = _date(r["next_follow_up"])
        if _open(r) and follow_up:
            out.append(Deadline(follow_up, "Application", r["state"],
                                f"{r['license_type']} application ({r['status']}, submitted {r['submitted']})",
                                r["owner"], r["open_deficiency"]))
    return out


def amendment_deadlines(data_dir):
    out = []
    for r in _rows(data_dir, "amendments.csv"):
        due = _date(r["due_date"])
        if _open(r) and due:
            note = f"Filed {r['filed_date']}" if r["filed_date"].strip() else "Not yet filed"
            out.append(Deadline(due, "Amendment", r["state"],
                                f"{r['change']} ({r['status']})", r["owner"], note))
    return out


def filing_deadlines(data_dir):
    out = []
    for r in _rows(data_dir, "filings.csv"):
        due = _date(r["due_date"])
        if _open(r) and due:
            out.append(Deadline(due, "Report / filing", r["state"],
                                f"{r['filing']} ({r['status']})", r["owner"]))
    return out


def exam_deadlines(data_dir):
    out = []
    for r in _rows(data_dir, "exam_items.csv"):
        due = _date(r["due_date"])
        if _open(r) and due:
            out.append(Deadline(due, "Exam item", r["state"],
                                f"{r['finding']} ({r['status']})", r["owner"], r["exam"]))
    return out


def call_report_deadlines(data_dir, settings, as_of, horizon_days):
    """Quarterly NMLS MSB Call Reports not yet logged as filed."""
    days = int(settings.get("call_report_days_after_quarter_end", 45))
    first = _date(settings["call_report_first_quarter_end"])
    filed = {_date(r["quarter_end"]) for r in _rows(data_dir, "call_reports_filed.csv")}
    last = as_of + timedelta(days=horizon_days)
    out = []
    for q in quarter_ends(first, last):
        due = q + timedelta(days=days)
        if q not in filed and due <= last:
            quarter = f"Q{(q.month - 1) // 3 + 1} {q.year}"
            out.append(Deadline(due, "MSB Call Report", "ALL",
                                f"NMLS MSB Call Report for {quarter}", "Licensing Lead",
                                f"Due {days} days after quarter end"))
    return out


def collect(data_dir, as_of, horizon_days=None):
    """All open deadlines that are overdue or fall within the horizon, soonest first."""
    settings = load_settings(data_dir)
    if horizon_days is None:
        horizon_days = int(settings.get("horizon_days", 90))
    items = (license_deadlines(data_dir, settings)
             + application_deadlines(data_dir)
             + amendment_deadlines(data_dir)
             + filing_deadlines(data_dir)
             + exam_deadlines(data_dir)
             + call_report_deadlines(data_dir, settings, as_of, horizon_days)
             + escheat_deadlines(data_dir, settings, as_of, Deadline))
    last = as_of + timedelta(days=horizon_days)
    return sorted((d for d in items if d.due <= last),
                  key=lambda d: (d.due, d.state, d.category))


def bucket(deadline, as_of):
    days = (deadline.due - as_of).days
    if days < 0:
        return "Overdue"
    if days <= 30:
        return "Due within 30 days"
    if days <= 60:
        return "Due in 31-60 days"
    return "Due in 61-90 days"
