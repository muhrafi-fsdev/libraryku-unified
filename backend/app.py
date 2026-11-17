"""API CRUD perpustakaan untuk tugas Project 1 Cloud Computing."""
import logging
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.errors
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from validation import validate_book, validate_loan

app = Flask(__name__)
app.logger.setLevel(logging.INFO)


@contextmanager
def db_cursor():
    connection = psycopg2.connect(
        host=os.environ.get("DB_HOST", "database"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "libraryku"),
        user=os.environ.get("DB_USER", "libraryku_user"),
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )
    try:
        with connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
    finally:
        connection.close()


def serialize_book(record):
    return {key: record[key] for key in ("id", "title", "author", "category", "year", "stock")}


@app.errorhandler(psycopg2.Error)
def handle_database_error(error):
    app.logger.exception("Database tidak tersedia: %s", error)
    return jsonify({"error": "Database tidak dapat diakses. Periksa container database."}), 503


@app.errorhandler(psycopg2.errors.UndefinedTable)
def handle_missing_table(error):
    app.logger.error("Tabel peminjaman belum ada: %s", error)
    return jsonify({"error": "Tabel peminjaman belum dibuat. Terapkan migrasi database/migrations/002_peminjaman.sql (./scripts/migrasi.sh)."}), 503


@app.errorhandler(HTTPException)
def handle_http_error(error):
    names = {
        400: "Permintaan tidak valid.",
        404: "Endpoint tidak ditemukan.",
        405: "Metode HTTP tidak didukung untuk endpoint ini.",
        413: "Badan permintaan terlalu besar.",
        415: "Gunakan Content-Type application/json.",
    }
    return jsonify({"error": names.get(error.code, error.name)}), error.code


@app.errorhandler(Exception)
def handle_unexpected(error):
    app.logger.exception("Galat tak terduga: %s", error)
    return jsonify({"error": "Terjadi kesalahan pada server."}), 500


@app.get("/api/health")
def health():
    with db_cursor() as cursor:
        cursor.execute("SELECT 1 AS ok")
        cursor.fetchone()
    return jsonify({"status": "ok", "service": "libraryku-api", "database": "connected"})


@app.get("/api/books")
def list_books():
    with db_cursor() as cursor:
        cursor.execute("SELECT id, title, author, category, year, stock FROM books ORDER BY id DESC")
        records = cursor.fetchall()
    books = [serialize_book(record) for record in records]
    return jsonify({"data": books, "total": len(books)})


@app.get("/api/books/<int:book_id>")
def get_book(book_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT id, title, author, category, year, stock FROM books WHERE id = %s", (book_id,))
        record = cursor.fetchone()
    if record is None:
        return jsonify({"error": "Buku tidak ditemukan."}), 404
    return jsonify({"data": serialize_book(record)})


@app.post("/api/books")
def create_book():
    cleaned, errors = validate_book(request.get_json(silent=True))
    if errors:
        return jsonify({"error": "Data buku tidak valid.", "details": errors}), 400
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO books (title, author, category, year, stock) "
            "VALUES (%s, %s, %s, %s, %s) "
            "RETURNING id, title, author, category, year, stock",
            (cleaned["title"], cleaned["author"], cleaned["category"], cleaned["year"], cleaned["stock"]),
        )
        record = cursor.fetchone()
    return jsonify({"message": "Buku berhasil ditambahkan.", "data": serialize_book(record)}), 201


@app.put("/api/books/<int:book_id>")
def update_book(book_id):
    cleaned, errors = validate_book(request.get_json(silent=True))
    if errors:
        return jsonify({"error": "Data buku tidak valid.", "details": errors}), 400
    with db_cursor() as cursor:
        cursor.execute(
            "UPDATE books SET title = %s, author = %s, category = %s, year = %s, stock = %s "
            "WHERE id = %s RETURNING id, title, author, category, year, stock",
            (cleaned["title"], cleaned["author"], cleaned["category"], cleaned["year"], cleaned["stock"], book_id),
        )
        record = cursor.fetchone()
    if record is None:
        return jsonify({"error": "Buku tidak ditemukan."}), 404
    return jsonify({"message": "Buku berhasil diubah.", "data": serialize_book(record)})


@app.delete("/api/books/<int:book_id>")
def delete_book(book_id):
    with db_cursor() as cursor:
        # Kunci baris buku: serial dengan peminjaman baru, sehingga buku tidak bisa dipinjam dan dihapus bersamaan.
        cursor.execute("SELECT id FROM books WHERE id = %s FOR UPDATE", (book_id,))
        if cursor.fetchone() is None:
            return jsonify({"error": "Buku tidak ditemukan."}), 404
        cursor.execute("SELECT to_regclass('public.loans') IS NOT NULL AS ada")
        if cursor.fetchone()["ada"]:
            cursor.execute("SELECT count(*) AS n FROM loans WHERE book_id = %s AND returned_date IS NULL", (book_id,))
            dipinjam = cursor.fetchone()["n"]
            if dipinjam:
                return jsonify({"error": f"Buku masih dipinjam ({dipinjam} eksemplar). Kembalikan dulu sebelum menghapus buku."}), 409
        cursor.execute("DELETE FROM books WHERE id = %s RETURNING id", (book_id,))
        cursor.fetchone()
    return jsonify({"message": "Buku berhasil dihapus.", "id": book_id})


# ---------------------------------------------------------------------------
# Peminjaman dan pengembalian (khusus SQL). Nginx menerjemahkan /api/sql/loans menjadi /api/loans dan
# mewajibkan login petugas untuk SEMUA metode, karena datanya berisi nama, kelas, dan NIM.
# ---------------------------------------------------------------------------
WIB = timezone(timedelta(hours=7))  # Indonesia Barat tidak memakai waktu musim panas
LOAN_COLUMNS = "id, book_id, book_title, borrower_name, borrower_class, borrower_nim, loan_date, due_date, returned_date, note"


def today_wib():
    return datetime.now(WIB).date()


def serialize_loan(record):
    loan = {key: record[key] for key in ("id", "book_id", "book_title", "borrower_name", "borrower_class", "borrower_nim", "note")}
    for key in ("loan_date", "due_date", "returned_date"):
        loan[key] = record[key].isoformat() if record[key] else None
    loan["status"] = "Dikembalikan" if record["returned_date"] else "Dipinjam"
    return loan


@app.get("/api/loans")
def list_loans():
    with db_cursor() as cursor:
        cursor.execute(f"SELECT {LOAN_COLUMNS} FROM loans ORDER BY id DESC")
        records = cursor.fetchall()
    loans = [serialize_loan(record) for record in records]
    return jsonify({"data": loans, "total": len(loans)})


@app.post("/api/loans")
def create_loan():
    cleaned, errors = validate_loan(request.get_json(silent=True))
    if errors:
        return jsonify({"error": "Data peminjaman tidak valid.", "details": errors}), 400
    with db_cursor() as cursor:
        # Kunci baris buku sampai transaksi selesai: dua permintaan bersamaan tidak bisa sama-sama mengambil eksemplar terakhir.
        cursor.execute("SELECT id, title, stock FROM books WHERE id = %s FOR UPDATE", (cleaned["book_id"],))
        book = cursor.fetchone()
        if book is None:
            return jsonify({"error": "Buku tidak ditemukan."}), 404
        if book["stock"] <= 0:
            return jsonify({"error": "Stok buku ini habis, tidak bisa dipinjam."}), 409
        cursor.execute("UPDATE books SET stock = stock - 1 WHERE id = %s", (book["id"],))
        cursor.execute(
            "INSERT INTO loans (book_id, book_title, borrower_name, borrower_class, borrower_nim, loan_date, due_date, note) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING {LOAN_COLUMNS}",
            (book["id"], book["title"], cleaned["borrower_name"], cleaned["borrower_class"], cleaned["borrower_nim"],
             cleaned["loan_date"], cleaned["due_date"], cleaned["note"]),
        )
        record = cursor.fetchone()
    return jsonify({"message": "Peminjaman dicatat.", "data": serialize_loan(record)}), 201


@app.post("/api/loans/<int:loan_id>/return")
def return_loan(loan_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT book_id FROM loans WHERE id = %s", (loan_id,))
        found = cursor.fetchone()
        if found is None:
            return jsonify({"error": "Data peminjaman tidak ditemukan."}), 404
        # Urutan kunci selalu buku lalu pinjaman (sama dengan peminjaman baru) agar tidak saling tunggu.
        if found["book_id"] is not None:
            cursor.execute("SELECT id FROM books WHERE id = %s FOR UPDATE", (found["book_id"],))
        cursor.execute(f"SELECT {LOAN_COLUMNS} FROM loans WHERE id = %s FOR UPDATE", (loan_id,))
        loan = cursor.fetchone()
        if loan["returned_date"] is not None:
            return jsonify({"error": "Buku ini sudah dikembalikan sebelumnya."}), 409
        returned = max(today_wib(), loan["loan_date"])  # tanggal pinjam bisa diisi lebih maju dari hari ini
        cursor.execute(f"UPDATE loans SET returned_date = %s WHERE id = %s RETURNING {LOAN_COLUMNS}", (returned, loan_id))
        record = cursor.fetchone()
        if loan["book_id"] is not None:
            cursor.execute("UPDATE books SET stock = LEAST(stock + 1, 1000000) WHERE id = %s", (loan["book_id"],))
    return jsonify({"message": "Buku dikembalikan.", "data": serialize_loan(record)})
