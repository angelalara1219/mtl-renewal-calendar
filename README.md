# MTL Renewal Calendar

A licensing calendar for a money transmitter: license renewals, surety bonds, pending applications, amendments, MSB Call Reports, state annual filings and open exam items, all in one dated list.

Every Monday it builds a report sorted by urgency and a calendar file you can import into Outlook or Google Calendar, with a reminder 14 days before each deadline.

**All data in this repo is synthetic.** The states, license IDs, dates and amounts are made up for illustration.

## Why I built this

At Bitcoin Depot I built and ran deadline trackers for SAR/STR/SMR filings across the US, Canada and Australia, and a daily CTR tracker that followed FinCEN GTO ZIP codes as the orders changed. Licensing has the same problem at a bigger scale: dozens of state deadlines on different schedules, where one missed date can mean a lapsed license, a fine or an exam finding. One list, sorted by what's due next, is how I'd want to run it.

## What it tracks

| Input file | What's in it | What becomes a deadline |
|---|---|---|
| `data/licenses.csv` | Each state license, its expiration and surety bond | License renewal date; bond expiration |
| `data/applications.csv` | New license applications in progress | Next follow-up date and any open deficiency |
| `data/amendments.csv` | Change of control, address, officers, delegates | Filing or approval due date |
| `data/filings.csv` | State annual reports, audited financials, assessments | Due date |
| `data/exam_items.csv` | Open findings from state exams | Remediation due date |
| `data/call_reports_filed.csv` | Quarters already filed | Any unfiled quarter, due 45 days after quarter end |

Anything marked Approved, Closed, Filed, Surrendered or Withdrawn drops off. Anything overdue stays at the top until it's marked done.

## Output

- [`reports/latest.md`](reports/latest.md): the weekly report, grouped as Overdue, Due within 30 days, 31-60 days and 61-90 days
- [`reports/licensing-calendar.ics`](reports/licensing-calendar.ics): the same deadlines as calendar events

Sample (as of Nov 18, 2026):

| Due | Days | Type | State | Item |
|---|---|---|---|---|
| 2026-11-10 | -8 | Surety bond | WA | Renew $50,000 surety bond and file the rider |
| 2026-11-14 | -4 | MSB Call Report | ALL | NMLS MSB Call Report for Q3 2026 |
| 2026-11-25 | 7 | Application | MA | Respond to deficiency: updated business plan and projections |
| 2026-12-31 | 43 | License renewal | AZ | Money Transmitter renewal via NMLS (window opens Nov 1) |

## Run it

No packages to install. Python 3.10 or later.

```bash
python -m renewal_calendar.report                         # as of today
python -m renewal_calendar.report --as-of 2026-11-18      # as of a given date
python -m unittest discover -s tests                      # 9 tests
```

Settings such as the look-ahead window and the Call Report due date live in `data/settings.json`.

## What this is not

- **Not a system of record.** NMLS and each state regulator are the source of truth. This is the to-do list that sits on top.
- **Not legal advice.** Renewal windows, filing dates and bond rules vary by state and change. Confirm every date against the current state requirements.

## Related

- [State Money Transmitter Licensing Tracker](https://github.com/angelalara1219/state-mt-licensing-tracker): changes in state money transmitter law, NMLS agency alerts and MTMA adoption
- [CTR & GTO Monitor](https://github.com/angelalara1219/ctr-gto-monitor): daily CTR, GTO and structuring checks
- [FinCEN Advisory & Guidance Tracker](https://github.com/angelalara1219/fincen-advisory-guidance-tracker): FinCEN alerts, advisories and SAR key terms

## License

MIT
