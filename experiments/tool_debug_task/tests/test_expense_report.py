import unittest

from src.expense_report import summarize_by_category


ROWS = [
    {"category": "Food", "cents": 1200},
    {"category": " food ", "cents": 300},
    {"category": "Travel", "cents": 2500},
]


class ExpenseReportTests(unittest.TestCase):
    def test_groups_categories_case_insensitively(self):
        self.assertEqual(
            summarize_by_category(ROWS), {"food": 1500, "travel": 2500}
        )

    def test_category_filter_is_case_insensitive(self):
        self.assertEqual(summarize_by_category(ROWS, "FOOD"), {"food": 1500})

    def test_unknown_category_returns_empty_result(self):
        self.assertEqual(summarize_by_category(ROWS, "health"), {})


if __name__ == "__main__":
    unittest.main()
