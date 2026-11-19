"""Unclaimed property (escheatment) deadlines for dormant customer accounts.

For each account that hasn't been reported or reactivated:
  - the dormancy date (last owner activity + the state's dormancy period),
  - an owner outreach reminder before that date, since owner contact can restart the clock,
  - the due-diligence notice to the owner before the state report,
  - the state report.
A dormant account that suddenly reactivates is flagged for fraud review instead.

State rules live in data/escheat_rules.csv. A state with no confirmed dormancy period
uses the default in settings.json and is labeled "confirm" in the report.
"""

import csv
from datetime import date, timedelta
from pathlib import Path


def _date(value):
    value = (value or "").strip()
    return date.fromisoformat(value) if value else None


def _rows(data_dir, name):
    path = Path(data_dir) / name
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def add_years(d, years):
    try:
        return d.replace(year=d.year + years)
    except ValueError:              # Feb 29
        return d.replace(year=d.year + years, day=28)


def next_report_date(after, month_day):
    """The first report due date (MM-DD) on or after `after`."""
    month, day = (int(x) for x in month_day.split("-"))
    candidate = date(after.year, month, day)
    return candidate if candidate >= after else date(after.year + 1, month, day)


def load_rules(data_dir):
    return {r["state"].strip(): r for r in _rows(data_dir, "escheat_rules.csv")}


def account_schedule(acct, rules, settings):
    """Dormancy date, notice date and report date for one account, plus how sure we are."""
    rule = rules.get(acct["state"].strip())
    years = (rule or {}).get("dormancy_years", "").strip()
    confirmed = bool(years)
    years = int(years) if confirmed else int(settings.get("escheat_default_dormancy_years", 3))
    dormant = add_years(_date(acct["last_owner_activity"]), years)
    report = next_report_date(dormant, settings.get("escheat_report_due", "11-01"))
    # The notice can't go out before the account is actually dormant.
    notice = max(report - timedelta(days=int(settings.get("escheat_notice_days_before_report", 120))), dormant)
    handling = (rule or {}).get("crypto_remittance", "").strip() or "State rule not on file"
    return dormant, notice, report, years, confirmed, handling


def escheat_deadlines(data_dir, settings, as_of, deadline_cls):
    rules = load_rules(data_dir)
    review_years = int(settings.get("reactivation_review_after_years", 2))
    out = []
    for a in _rows(data_dir, "dormant_accounts.csv"):
        state, acct_id = a["state"].strip(), a["account_id"]
        holding = f"{a['balance']} {a['asset']}"
        last = _date(a["last_owner_activity"])
        reactivated = _date(a["reactivated_on"])

        if reactivated:
            idle_days = (reactivated - last).days
            if idle_days >= review_years * 365:
                out.append(deadline_cls(
                    reactivated + timedelta(days=7), "Reactivation review", state,
                    f"Account {acct_id} reactivated after {idle_days // 365} years dormant ({holding})",
                    "Compliance", "Review for account takeover or money mule activity"))
            continue
        if _date(a["reported_on"]):
            continue

        dormant, notice, report, years, confirmed, handling = account_schedule(a, rules, settings)
        rule_note = f"{years}-year dormancy" + ("" if confirmed else " (default; confirm state rule)")
        if a["asset"].strip().upper() != "USD":
            rule_note += f"; crypto: {handling}"

        if dormant > as_of:
            out.append(deadline_cls(
                dormant, "Unclaimed property", state,
                f"Account {acct_id} goes dormant ({holding}); reach out to the owner first",
                "Compliance", rule_note))
            continue
        if not _date(a["owner_contacted"]):
            out.append(deadline_cls(
                notice, "Unclaimed property", state,
                f"Send due-diligence notice for account {acct_id} ({holding})",
                "Compliance", rule_note))
        out.append(deadline_cls(
            report, "Unclaimed property", state,
            f"File unclaimed property report and remit account {acct_id} ({holding})",
            "Finance", rule_note))
    return out
