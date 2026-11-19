# MTL Renewal Calendar

A licensing calendar for a money transmitter: license renewals, surety bonds, pending applications, amendments, MSB Call Reports, state annual filings, open exam items and unclaimed property (escheatment) deadlines, all in one dated list.

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
| `data/dormant_accounts.csv` | Customer accounts with no recent owner activity | Dormancy date, owner notice and state report; reactivation reviews |
| `data/escheat_rules.csv` | Each state's dormancy period and how crypto is handled | Applied to the accounts above |

Anything marked Approved, Closed, Filed, Surrendered or Withdrawn drops off. Anything overdue stays at the top until it's marked done.

## Unclaimed property (escheatment)

A custodial crypto company holds customer bitcoin and cash, so dormant balances eventually have to be reported and turned over to the state. For each account, the calendar works out:

- **Dormancy date:** last owner activity plus the state's dormancy period. Before that date it adds an outreach reminder, since owner contact can restart the clock.
- **Due-diligence notice:** the letter to the owner before the state report.
- **State report and remittance**, with the state's rule on crypto: sold first, or turned over as is.

A dormant account that suddenly comes back to life gets a **reactivation review** instead. After years of no activity, a sudden login or withdrawal is a classic sign of account takeover or money mule use.

State rules on file, each with its source:

| State | Dormancy | Crypto handling | Source |
|---|---|---|---|
| DE | 5 years | Liquidate before reporting | [Sovos](https://dev.sovos.com/en-gb/blog/trr/crypto-to-nfts-unclaimed-property-laws) |
| IL | 5 years | Liquidate before reporting | [Bloomberg Law](https://news.bloomberglaw.com/tax-insights-and-commentary/looking-at-unclaimed-property-issues-in-cryptocurrency) |
| CA | Confirm | No forced liquidation (SB 822) | [Cointelegraph](https://cointelegraph.com/explained/california-just-drew-the-line-between-crypto-and-cash-here-s-why-it-matters) |
| VA | Confirm | In kind; state holds at least 1 year before sale | [The Block](https://www.theblock.co/news/regulation/2026-04-15-virginia-approves-bill-unclaimed-crypto-assets-397484) |
| AZ | Confirm | Digital assets covered since 2025 (HB 2749) | [Cointelegraph](https://cointelegraph.com/explained/california-just-drew-the-line-between-crypto-and-cash-here-s-why-it-matters) |

Where a state's dormancy period isn't confirmed, the calendar uses a 3-year default and says "confirm state rule" on the item. The report due date (Nov 1) and the 120-day notice window in `data/settings.json` are planning defaults, not any one state's rule. Set them per your states.

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
python -m unittest discover -s tests                      # 19 tests
```

Settings such as the look-ahead window and the Call Report due date live in `data/settings.json`.

## What this is not

- **Not a system of record.** NMLS and each state regulator are the source of truth. This is the to-do list that sits on top.
- **Not legal advice.** Renewal windows, filing dates, bond rules and unclaimed property laws vary by state and change often, especially for digital assets. Confirm every date against current state requirements.

## Related

- [State Money Transmitter Licensing Tracker](https://github.com/angelalara1219/state-mt-licensing-tracker): changes in state money transmitter law, NMLS agency alerts and MTMA adoption
- [CTR & GTO Monitor](https://github.com/angelalara1219/ctr-gto-monitor): daily CTR, GTO and structuring checks
- [FinCEN Advisory & Guidance Tracker](https://github.com/angelalara1219/fincen-advisory-guidance-tracker): FinCEN alerts, advisories and SAR key terms

## License

MIT
