import unittest
from src.expense_report import percentage

class HeldoutTests(unittest.TestCase):
    def test_zero_total(self):
        self.assertEqual(percentage(0, 0), 0)
    def test_regular_percentage(self):
        self.assertEqual(percentage(1, 4), 25)

