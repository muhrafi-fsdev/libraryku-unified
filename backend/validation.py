"""Validasi data buku, dipisahkan agar mudah diuji tanpa database."""
import re
from datetime import date


def validate_book(payload):
    if not isinstance(payload, dict):
        return None, {"body": "Kirim objek JSON yang valid."}

    cleaned = {}
    errors = {}
    fields = {"title": 150, "author": 100, "category": 60}
    for key, max_len in fields.items():
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors[key] = "Wajib diisi dengan teks."
        elif len(value.strip()) > max_len:
            errors[key] = f"Maksimal {max_len} karakter."
        else:
            cleaned[key] = value.strip()

    year = payload.get("year")
    if isinstance(year, bool) or not isinstance(year, int) or not (1900 <= year <= date.today().year + 1):
        errors["year"] = f"Tahun harus angka bulat antara 1900 dan {date.today().year + 1}."
    else:
        cleaned["year"] = year

    stock = payload.get("stock")
    if isinstance(stock, bool) or not isinstance(stock, int) or not (0 <= stock <= 1_000_000):
        errors["stock"] = "Stok harus angka bulat antara 0 dan 1.000.000."
    else:
        cleaned["stock"] = stock

    return (cleaned, {}) if not errors else (None, errors)


NIM_PATTERN = re.compile(r"^[0-9]{5,20}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_iso_date(value):
    """Tanggal ISO 'YYYY-MM-DD' yang valid pada tahun 2000 sampai 2100, selain itu None."""
    if not isinstance(value, str) or not DATE_PATTERN.match(value):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if 2000 <= parsed.year <= 2100 else None


def validate_loan(payload):
    """Validasi data peminjaman. Mengembalikan (data_bersih, {}) atau (None, galat_per_kolom)."""
    if not isinstance(payload, dict):
        return None, {"body": "Kirim objek JSON yang valid."}

    cleaned = {}
    errors = {}

    book_id = payload.get("book_id")
    if isinstance(book_id, bool) or not isinstance(book_id, int) or not (1 <= book_id <= 2_147_483_647):
        errors["book_id"] = "Pilih buku yang valid."
    else:
        cleaned["book_id"] = book_id

    for key, label, max_len in (("borrower_name", "Nama lengkap", 100), ("borrower_class", "Kelas", 30)):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors[key] = f"{label} wajib diisi."
        elif len(value.strip()) > max_len:
            errors[key] = f"{label} maksimal {max_len} karakter."
        else:
            cleaned[key] = value.strip()

    nim = payload.get("borrower_nim")
    if not isinstance(nim, str) or not NIM_PATTERN.match(nim.strip()):
        errors["borrower_nim"] = "NIM harus berupa teks angka, 5 sampai 20 digit."
    else:
        cleaned["borrower_nim"] = nim.strip()

    loan_date = parse_iso_date(payload.get("loan_date"))
    due_date = parse_iso_date(payload.get("due_date"))
    if loan_date is None:
        errors["loan_date"] = "Tanggal pinjam harus tanggal yang valid (YYYY-MM-DD)."
    else:
        cleaned["loan_date"] = loan_date
    if due_date is None:
        errors["due_date"] = "Batas pengembalian wajib diisi dengan tanggal yang valid (YYYY-MM-DD)."
    elif loan_date is not None and due_date < loan_date:
        errors["due_date"] = "Batas pengembalian tidak boleh sebelum tanggal pinjam."
    else:
        cleaned["due_date"] = due_date

    note = payload.get("note")
    if note is None or (isinstance(note, str) and not note.strip()):
        cleaned["note"] = None
    elif not isinstance(note, str):
        errors["note"] = "Catatan harus berupa teks."
    elif len(note.strip()) > 300:
        errors["note"] = "Catatan maksimal 300 karakter."
    else:
        cleaned["note"] = note.strip()

    return (cleaned, {}) if not errors else (None, errors)
