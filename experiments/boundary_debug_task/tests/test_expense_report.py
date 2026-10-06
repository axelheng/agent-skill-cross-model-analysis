import unittest
from src.expense_report import clamp_score

class BoundaryTests(unittest.TestCase):
    def test_inclusive_bounds(self):
        self.assertEqual(clamp_score(0), 0)
        self.assertEqual(clamp_score(100), 100)
    def test_outside_bounds(self):
        self.assertEqual(clamp_score(-1), 0)
        self.assertEqual(clamp_score(101), 100)

