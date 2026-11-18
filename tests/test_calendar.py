import unittest
from datetime import date
from pathlib import Path

from renewal_calendar.build import Deadline, bucket, collect, quarter_ends
from renewal_calendar.report import ics, markdown

DATA = Path(__file__).resolve().parent.parent / "data"
AS_OF = date(2026, 11, 18)


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.items = collect(DATA, AS_OF, 90)

    def find(self, category, state):
        return [d for d in self.items if d.category == category and d.state == state]

    def test_buckets_and_boundaries(self):
        d = lambda days: Deadline(date.fromordinal(AS_OF.toordinal() + days), "x", "x", "x")
        self.assertEqual(bucket(d(-1), AS_OF), "Overdue")
        self.assertEqual(bucket(d(0), AS_OF), "Due within 30 days")
        self.assertEqual(bucket(d(30), AS_OF), "Due within 30 days")
        self.assertEqual(bucket(d(31), AS_OF), "Due in 31-60 days")
        self.assertEqual(bucket(d(90), AS_OF), "Due in 61-90 days")

    def test_nothing_past_horizon(self):
        self.assertTrue(all(d.due <= date(2027, 2, 16) for d in self.items))
        self.assertFalse(self.find("License renewal", "FL"))  # expires April 2027

    def test_overdue_items_stay_on_the_list(self):
        self.assertEqual(self.find("Surety bond", "WA")[0].due, date(2026, 11, 10))
        self.assertTrue(self.find("Report / filing", "IL"))
        self.assertEqual(bucket(self.find("Application", "NJ")[0], AS_OF), "Overdue")

    def test_closed_filed_approved_and_surrendered_are_excluded(self):
        self.assertFalse([d for d in self.items if d.state == "OR"])
        self.assertFalse(self.find("Amendment", "GA"))
        self.assertFalse(self.find("Application", "CT"))
        self.assertFalse(self.find("Report / filing", "AZ"))
        self.assertFalse(self.find("Exam item", "AZ"))

    def test_nmls_renewals_note_the_window(self):
        az = self.find("License renewal", "AZ")[0]
        self.assertEqual(az.due, date(2026, 12, 31))
        self.assertIn("2026-11-01", az.note)

    def test_call_reports_due_45_days_after_quarter_end_until_filed(self):
        calls = {d.item: d.due for d in self.items if d.category == "MSB Call Report"}
        self.assertEqual(calls, {
            "NMLS MSB Call Report for Q3 2026": date(2026, 11, 14),   # unfiled, overdue
            "NMLS MSB Call Report for Q4 2026": date(2027, 2, 14),
        })

    def test_quarter_ends(self):
        self.assertEqual(quarter_ends(date(2026, 6, 30), date(2027, 1, 1)),
                         [date(2026, 6, 30), date(2026, 9, 30), date(2026, 12, 31)])

    def test_sorted_soonest_first(self):
        dues = [d.due for d in self.items]
        self.assertEqual(dues, sorted(dues))

    def test_outputs(self):
        md = markdown(self.items, AS_OF, "Sample", 90)
        self.assertIn("## Overdue", md)
        cal = ics(self.items, "Sample")
        self.assertEqual(cal.count("BEGIN:VEVENT"), len(self.items))
        self.assertTrue(cal.endswith("END:VCALENDAR\r\n"))
        self.assertIn("\\,", cal)  # commas escaped (e.g. $100,000 bond)


if __name__ == "__main__":
    unittest.main()
