"""Tambah 3 buku contoh via API. Aman dijalankan ulang (tidak menduplikasi judul contoh)."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = os.environ.get("LIBRARYKU_URL", "http://localhost:8081").rstrip("/")
SAMPLES = [
    {"title": "Pengantar Cloud Computing", "author": "Andi Prasetyo", "category": "Teknologi", "year": 2024, "stock": 8},
    {"title": "Dasar Jaringan Komputer", "author": "Dina Lestari", "category": "Pendidikan", "year": 2022, "stock": 5},
    {"title": "Cerita di Balik Hujan", "author": "Raka Ananta", "category": "Fiksi", "year": 2021, "stock": 3},
]


def fetch_json(path, data=None):
    request = Request(
        ROOT + path,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="POST" if data is not None else "GET",
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def main():
    try:
        existing = {row["title"] for row in fetch_json("/api/books")["data"]}
        for book in SAMPLES:
            if book["title"] in existing:
                print(f"Dilewati (sudah ada): {book['title']}")
                continue
            result = fetch_json("/api/books", book)
            print(f"Ditambah ID {result['data']['id']}: {book['title']}")
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"Gagal mengakses {ROOT}. Pastikan 'docker compose up -d --build' sukses. {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
