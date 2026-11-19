import unittest
from datetime import date
from pathlib import Path

from renewal_calendar.build import Deadline, collect, load_settings
from renewal_calendar.escheat import account_schedule, add_years, load_rules, next_report_date

DATA = Path(__file__).resolve().parent.parent / "data"
AS_OF = date(2026, 11, 18)


def acct(**kw):
    base = dict(account_id="X", customer_id="C", state="DE", asset="BTC", balance="0.1",
                last_owner_activity="2021-09-15", owner_contacted="", reactivated_on="", reported_on="")
    base.update(kw)
    return base


class EscheatTests(unittest.TestCase):
    def setUp(self):
        self.settings = load_settings(DATA)
        self.rules = load_rules(DATA)
        self.items = [d for d in collect(DATA, AS_OF, 90)
                      if d.category in ("Unclaimed property", "Reactivation review")]

    def mine(self, acct_id):
        return [d for d in self.items if f"account {acct_id}".lower() in d.item.lower()]

    def test_date_helpers(self):
        self.assertEqual(add_years(date(2024, 2, 29), 1), date(2025, 2, 28))
        self.assertEqual(next_report_date(date(2026, 9, 15), "11-01"), date(2026, 11, 1))
        self.assertEqual(next_report_date(date(2026, 11, 2), "11-01"), date(2027, 11, 1))
        self.assertEqual(next_report_date(date(2026, 11, 1), "11-01"), date(2026, 11, 1))

    def test_confirmed_state_rule(self):
        dormant, notice, report, years, confirmed, handling = account_schedule(acct(), self.rules, self.settings)
        self.assertEqual((dormant, report, years, confirmed), (date(2026, 9, 15), date(2026, 11, 1), 5, True))
        self.assertEqual(notice, date(2026, 9, 15))  # 120 days before the report is Jul 4, before dormancy
        self.assertIn("Liquidate", handling)

    def test_unconfirmed_state_uses_default_and_says_so(self):
        _, _, _, years, confirmed, handling = account_schedule(acct(state="TX"), self.rules, self.settings)
        self.assertEqual((years, confirmed, handling), (3, False, "State rule not on file"))

    def test_overdue_notice_and_report_for_unreported_dormant_account(self):
        items = self.mine("A-1001")
        self.assertEqual(sorted(d.due for d in items), [date(2026, 9, 15), date(2026, 11, 1)])

    def test_upcoming_dormancy_prompts_outreach(self):
        il = self.mine("A-1002")[0]
        self.assertEqual(il.due, date(2026, 12, 20))
        self.assertIn("reach out", il.item)
        ca = self.mine("A-1004")[0]
        self.assertIn("No forced liquidation", ca.note)
        self.assertIn("confirm", ca.note)

    def test_notice_is_120_days_before_report_when_dormant_long_enough(self):
        _, notice, report, *_ = account_schedule(acct(last_owner_activity="2021-03-01"), self.rules, self.settings)
        self.assertEqual((notice, report), (date(2026, 7, 4), date(2026, 11, 1)))

    def test_contacted_owner_skips_notice(self):
        self.assertFalse(self.mine("A-1005"))   # report is Nov 2027, past the horizon

    def test_reported_accounts_drop_off(self):
        self.assertFalse(self.mine("A-1003"))

    def test_reactivation_after_long_dormancy_is_flagged(self):
        r = self.mine("A-1007")
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0].category, "Reactivation review")
        self.assertIn("account takeover", r[0].note)

    def test_usd_accounts_have_no_crypto_note(self):
        self.assertNotIn("crypto", self.mine("A-1008")[0].note)


if __name__ == "__main__":
    unittest.main()
