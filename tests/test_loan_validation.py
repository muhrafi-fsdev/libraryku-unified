"""Dijalankan dengan: python -m unittest discover -s tests -v  (tanpa database)."""
import pathlib
import sys
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))
from validation import parse_iso_date, validate_loan  # noqa: E402

VALID = {
    "book_id": 1, "borrower_name": "Budi Santoso", "borrower_class": "S1TT-KJ-23-04", "borrower_nim": "0123456789",
    "loan_date": "2026-11-17", "due_date": "2026-11-24", "note": "",
}


def with_(**kw):
    return {**VALID, **kw}


class ValidateLoanTests(unittest.TestCase):
    def test_data_valid(self):
        cleaned, errors = validate_loan(VALID)
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["loan_date"], date(2026, 11, 17))
        self.assertIsNone(cleaned["note"])

    def test_nim_nol_di_depan_tetap_teks(self):
        cleaned, _ = validate_loan(with_(borrower_nim="0012345"))
        self.assertEqual(cleaned["borrower_nim"], "0012345")

    def test_nim_angka_json_ditolak(self):
        _, errors = validate_loan(with_(borrower_nim=12345678))
        self.assertIn("borrower_nim", errors)

    def test_nim_bukan_angka_atau_terlalu_pendek(self):
        for nim in ("12AB567", "1234", "1" * 21, ""):
            self.assertIn("borrower_nim", validate_loan(with_(borrower_nim=nim))[1], nim)

    def test_batas_sebelum_tanggal_pinjam_ditolak(self):
        _, errors = validate_loan(with_(loan_date="2026-11-17", due_date="2026-11-16"))
        self.assertIn("due_date", errors)

    def test_batas_sama_dengan_tanggal_pinjam_boleh(self):
        self.assertEqual(validate_loan(with_(due_date="2026-11-17"))[1], {})

    def test_tanggal_tidak_valid(self):
        for bad in ("2026-02-30", "17-11-2026", "2026/11/17", "", None, 20261117, "1999-01-01", "2101-01-01"):
            self.assertIn("loan_date", validate_loan(with_(loan_date=bad))[1], str(bad))

    def test_batas_wajib(self):
        self.assertIn("due_date", validate_loan({k: v for k, v in VALID.items() if k != "due_date"})[1])

    def test_book_id(self):
        for bad in (0, -1, True, "1", None, 1.5, 2**31):
            self.assertIn("book_id", validate_loan(with_(book_id=bad))[1], str(bad))

    def test_nama_dan_kelas_wajib_dan_dibatasi(self):
        self.assertIn("borrower_name", validate_loan(with_(borrower_name="   "))[1])
        self.assertIn("borrower_name", validate_loan(with_(borrower_name="a" * 101))[1])
        self.assertIn("borrower_class", validate_loan(with_(borrower_class=""))[1])
        self.assertIn("borrower_class", validate_loan(with_(borrower_class="k" * 31))[1])

    def test_catatan_opsional_dan_dibatasi(self):
        self.assertEqual(validate_loan(with_(note="Buku titipan"))[0]["note"], "Buku titipan")
        self.assertIn("note", validate_loan(with_(note="x" * 301))[1])
        self.assertIn("note", validate_loan(with_(note=5))[1])

    def test_bukan_objek(self):
        self.assertIn("body", validate_loan([1, 2])[1])
        self.assertIn("body", validate_loan(None)[1])

    def test_parse_iso_date(self):
        self.assertEqual(parse_iso_date("2024-02-29"), date(2024, 2, 29))
        self.assertIsNone(parse_iso_date("2025-02-29"))


if __name__ == "__main__":
    unittest.main()
