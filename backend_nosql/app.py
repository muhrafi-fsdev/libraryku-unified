"""API CRUD NoSQL (MongoDB) untuk LibraryKu Unified.

Kontrak JSON sengaja sama dengan API SQL agar frontend memakai komponen yang sama.
Perbedaan: id adalah string ObjectId (24 karakter heksadesimal), bukan angka.
"""
import logging
import os
from datetime import datetime, timezone

from bson import ObjectId
from flask import Flask, jsonify, request
from pymongo import DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError
from werkzeug.exceptions import HTTPException

from ids import is_valid_object_id
from validation import validate_book

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # badan permintaan maksimal 16 KiB

_DB_NAME = os.environ.get("MONGO_DB", "libraryku_nosql")
_client = MongoClient(
    host=os.environ.get("MONGO_HOST", "mongodb"),
    port=int(os.environ.get("MONGO_PORT", "27017")),
    username=os.environ["MONGO_APP_USER"],
    password=os.environ["MONGO_APP_PASSWORD"],
    authSource=_DB_NAME,
    serverSelectionTimeoutMS=3000,
    connectTimeoutMS=3000,
    socketTimeoutMS=5000,
    appname="libraryku-nosql-api",
)
books = _client[_DB_NAME]["books"]

LIST_LIMIT = 1000


def serialize_book(document):
    return {
        "id": str(document["_id"]),
        "title": document["title"],
        "author": document["author"],
        "category": document["category"],
        "year": document["year"],
        "stock": document["stock"],
    }


def not_found():
    return jsonify({"error": "Buku tidak ditemukan."}), 404


def bad_id():
    return jsonify({"error": "ID buku tidak valid. Gunakan 24 karakter heksadesimal."}), 400


@app.errorhandler(PyMongoError)
def handle_database_error(error):
    app.logger.exception("MongoDB tidak tersedia: %s", error)
    return jsonify({"error": "Database MongoDB tidak dapat diakses. Periksa container mongodb."}), 503


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


@app.get("/api/nosql/health")
def health():
    _client.admin.command("ping")
    return jsonify({"status": "ok", "service": "libraryku-nosql-api", "database": "connected", "engine": "mongodb"})


@app.get("/api/nosql/books")
def list_books():
    documents = books.find({}).sort("_id", DESCENDING).limit(LIST_LIMIT)
    data = [serialize_book(document) for document in documents]
    return jsonify({"data": data, "total": len(data)})


@app.get("/api/nosql/books/<book_id>")
def get_book(book_id):
    if not is_valid_object_id(book_id):
        return bad_id()
    document = books.find_one({"_id": ObjectId(book_id)})
    if document is None:
        return not_found()
    return jsonify({"data": serialize_book(document)})


@app.post("/api/nosql/books")
def create_book():
    cleaned, errors = validate_book(request.get_json(silent=True))
    if errors:
        return jsonify({"error": "Data buku tidak valid.", "details": errors}), 400
    # Dokumen disusun dari kolom yang sudah divalidasi saja: kunci dan nilai dari pengguna tidak dipakai mentah.
    document = {
        "title": cleaned["title"],
        "author": cleaned["author"],
        "category": cleaned["category"],
        "year": cleaned["year"],
        "stock": cleaned["stock"],
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = books.insert_one(document)
    except DuplicateKeyError:
        return jsonify({"error": "Terjadi konflik data. Coba lagi."}), 409
    document["_id"] = result.inserted_id
    return jsonify({"message": "Buku berhasil ditambahkan.", "data": serialize_book(document)}), 201


@app.put("/api/nosql/books/<book_id>")
def update_book(book_id):
    if not is_valid_object_id(book_id):
        return bad_id()
    cleaned, errors = validate_book(request.get_json(silent=True))
    if errors:
        return jsonify({"error": "Data buku tidak valid.", "details": errors}), 400
    changes = {key: cleaned[key] for key in ("title", "author", "category", "year", "stock")}
    document = books.find_one_and_update(
        {"_id": ObjectId(book_id)}, {"$set": changes}, return_document=ReturnDocument.AFTER
    )
    if document is None:
        return not_found()
    return jsonify({"message": "Buku berhasil diubah.", "data": serialize_book(document)})


@app.delete("/api/nosql/books/<book_id>")
def delete_book(book_id):
    if not is_valid_object_id(book_id):
        return bad_id()
    result = books.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        return not_found()
    return jsonify({"message": "Buku berhasil dihapus.", "id": book_id})
