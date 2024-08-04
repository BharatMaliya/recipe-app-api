"""
sample test file
"""

from django.test import SimpleTestCase

from app import calc


class CalcTests(SimpleTestCase):
    """test class for calc.py"""

    def test_add(self):
        """test case for add method"""
        self.assertEqual(calc.add(1, 2), 3)
        self.assertEqual(calc.add(-1, 1), 0)
        self.assertEqual(calc.add(-1, -1), -2)

    def test_subtract(self):
        """test case for subtract method"""
        self.assertEqual(calc.subtract(1, 2), -1)
        self.assertEqual(calc.subtract(-1, 1), -2)
        self.assertEqual(calc.subtract(-1, -1), 0)

    def test_multiply(self):
        """test case for multiply method"""
        self.assertEqual(calc.multiply(1, 2), 2)
        self.assertEqual(calc.multiply(-1, 1), -1)
        self.assertEqual(calc.multiply(-1, -1), 1)

    def test_divide(self):
        """test case for divide method"""
        self.assertEqual(calc.divide(1, 2), 0.5)
        self.assertEqual(calc.divide(-1, 1), -1)
        self.assertEqual(calc.divide(-1, -1), 1)
        self.assertEqual(calc.divide(5, 2), 2.5)

        with self.assertRaises(ValueError):
            calc.divide(10, 0)
