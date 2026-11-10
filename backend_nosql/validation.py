"""Validasi data buku, dipisahkan agar mudah diuji tanpa database."""
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
