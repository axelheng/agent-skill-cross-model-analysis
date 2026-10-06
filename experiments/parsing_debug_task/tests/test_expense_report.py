import unittest
from src.expense_report import parse_amount

class ParsingTests(unittest.TestCase):
    def test_currency(self):
        self.assertEqual(parse_amount("$12.50"), 1250)
    def test_rejects_invalid_text(self):
        with self.assertRaises(ValueError):
            parse_amount("12.5 cents")

