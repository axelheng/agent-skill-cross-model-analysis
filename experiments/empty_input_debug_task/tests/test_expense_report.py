import unittest
from src.expense_report import average

class EmptyInputTests(unittest.TestCase):
    def test_empty_returns_none(self):
        self.assertIsNone(average([]))
    def test_values_average(self):
        self.assertEqual(average([2, 4]), 3)

