"""Dijalankan dengan: python -m unittest discover -s tests -v  (tanpa MongoDB)."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend_nosql"))
from ids import is_valid_object_id  # noqa: E402
from validation import validate_book  # noqa: E402

VALID = {"title": "Dasar Basis Data", "author": "Sari Dewi", "category": "Teknologi", "year": 2024, "stock": 3}


class ObjectIdTest(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(is_valid_object_id("507f1f77bcf86cd799439011"))
        self.assertTrue(is_valid_object_id("507F1F77BCF86CD799439011"))

    def test_invalid(self):
        for bad in ["", "abc", "1", "507f1f77bcf86cd79943901", "507f1f77bcf86cd7994390111",
                    "507f1f77bcf86cd79943901z", "$ne", "{'$ne': 1}", None, 5, ["507f1f77bcf86cd799439011"]]:
            self.assertFalse(is_valid_object_id(bad), bad)

    def test_newline_tidak_lolos(self):
        self.assertFalse(is_valid_object_id("507f1f77bcf86cd799439011\n"))


class NoSqlInjectionTest(unittest.TestCase):
    def test_operator_di_kolom_teks_ditolak(self):
        for field in ("title", "author", "category"):
            data, errors = validate_book({**VALID, field: {"$ne": ""}})
            self.assertIsNone(data)
            self.assertIn(field, errors)

    def test_operator_di_kolom_angka_ditolak(self):
        for field in ("year", "stock"):
            data, errors = validate_book({**VALID, field: {"$gt": 0}})
            self.assertIsNone(data)
            self.assertIn(field, errors)

    def test_kolom_asing_tidak_ikut(self):
        data, errors = validate_book({**VALID, "$where": "sleep(1000)", "role": "admin"})
        self.assertEqual(errors, {})
        self.assertEqual(set(data), {"title", "author", "category", "year", "stock"})


if __name__ == "__main__":
    unittest.main()
