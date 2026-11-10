"""API CRUD perpustakaan untuk tugas Project 1 Cloud Computing."""
import logging
import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from validation import validate_book

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
        cursor.execute("DELETE FROM books WHERE id = %s RETURNING id", (book_id,))
        record = cursor.fetchone()
    if record is None:
        return jsonify({"error": "Buku tidak ditemukan."}), 404
    return jsonify({"message": "Buku berhasil dihapus.", "id": book_id})
