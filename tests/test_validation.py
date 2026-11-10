"""Dijalankan dengan: python -m unittest discover -s tests -v"""
import pathlib
import sys
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))
from validation import validate_book


class ValidationTest(unittest.TestCase):
    valid = {"title": "Dasar Jaringan Komputer", "author": "Budi Santoso", "category": "Teknologi", "year": 2023, "stock": 5}

    def test_valid_book(self):
        data, errors = validate_book(self.valid)
        self.assertEqual(errors, {})
        self.assertEqual(data["stock"], 5)

    def test_trim_text(self):
        data, _ = validate_book({**self.valid, "title": "  Buku Bagus  "})
        self.assertEqual(data["title"], "Buku Bagus")

    def test_empty_title_rejected(self):
        _, errors = validate_book({**self.valid, "title": " "})
        self.assertIn("title", errors)

    def test_negative_stock_rejected(self):
        _, errors = validate_book({**self.valid, "stock": -1})
        self.assertIn("stock", errors)

    def test_boolean_stock_rejected(self):
        _, errors = validate_book({**self.valid, "stock": True})
        self.assertIn("stock", errors)

    def test_invalid_year_rejected(self):
        _, errors = validate_book({**self.valid, "year": date.today().year + 2})
        self.assertIn("year", errors)

    def test_invalid_json_type_rejected(self):
        _, errors = validate_book([self.valid])
        self.assertIn("body", errors)

    def test_too_long_author_rejected(self):
        _, errors = validate_book({**self.valid, "author": "X" * 101})
        self.assertIn("author", errors)


if __name__ == "__main__":
    unittest.main()
