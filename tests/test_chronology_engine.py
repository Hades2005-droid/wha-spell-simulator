import unittest
from datetime import datetime

from tools.chronology_engine import analyze_date, analyze_timestamp, reduce_frequency


class ChronologyEngineTests(unittest.TestCase):
    def test_preserves_master_numbers(self):
        self.assertEqual(reduce_frequency(33), 33)
        self.assertEqual(reduce_frequency(22), 22)
        self.assertEqual(reduce_frequency(25), 7)

    def test_analyzes_micro_and_macro_values(self):
        result = analyze_date(datetime(2026, 6, 27).date())
        raw_values = result["raw_values"]
        self.assertEqual(raw_values["micro_number_sum"], 33)
        self.assertEqual(raw_values["macro_digit_sum"], 25)
        self.assertEqual(result["frequencies"]["micro_number_sum"]["reduced"], 33)
        self.assertEqual(result["frequencies"]["macro_digit_sum"]["reduced"], 7)
        self.assertTrue(result["symbolic_only"])

    def test_converts_local_timestamp_to_comparison_timezone(self):
        result = analyze_timestamp(datetime(2026, 6, 27, 20, 40), "America/New_York", "Asia/Singapore")
        self.assertEqual(result["clock_24_hour"], "20:40")
        self.assertIn("2026-06-28T08:40", result["comparison_timestamp"])
        self.assertEqual(result["clock_digit_sum"]["reduced"], 6)


if __name__ == "__main__":
    unittest.main()
