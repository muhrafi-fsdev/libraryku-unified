"""Uji API LibraryKu Unified (SQL dan NoSQL) terhadap aplikasi yang BERJALAN (Nginx -> Flask -> PostgreSQL/MongoDB).

Hanya memakai pustaka standar. Membuat buku uji berjudul "[UJI-UNIFIED] ..." dan menghapusnya di akhir;
buku lain tidak disentuh. Jalankan:  python3 scripts/test_api.py [http://localhost:8081]
"""
import base64, os, json, time
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8081").rstrip("/")
RESULTS = []
CREATED = {"sql": [], "nosql": []}


def _auth_header():
    """Kredensial dashboard dibaca dari file izin 600 (bukan argumen/log)."""
    path = os.environ.get("LIBRARYKU_CRED", os.path.expanduser("~/.libraryku_dashboard_credentials"))
    try:
        kv = dict(l.strip().split("=", 1) for l in open(path) if "=" in l)
        token = base64.b64encode(f"{kv['username']}:{kv['password']}".encode()).decode()
        return {"Authorization": "Basic " + token}
    except Exception:
        return {}
AUTH = _auth_header() if os.environ.get("LIBRARYKU_AUTH") == "1" else {}  # mode terbuka: tanpa login; LIBRARYKU_AUTH=1 bila login diaktifkan lagi


def call(method, path, body=None, raw=None, headers=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    hdrs = {"Content-Type": "application/json"} if (body is not None or raw is not None) else {}
    if method not in ("GET", "HEAD"):
        hdrs.update(AUTH)
        hdrs["X-Requested-With"] = "libraryku"
        time.sleep(0.6)  # jeda agar tidak kena batas laju tulis
    hdrs.update(headers or {})
    request = urllib.request.Request(BASE + path, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            text = response.read().decode()
            return response.status, text, dict(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(), dict(error.headers)


def js(text):
    try:
        return json.loads(text)
    except ValueError:
        return None


def check(name, condition, detail=""):
    RESULTS.append(bool(condition))
    print(("PASS " if condition else "FAIL ") + name + (f" | {detail}" if detail else ""))


BOOK = {"title": "[UJI-UNIFIED] Buku Uji", "author": "Penguji", "category": "Umum", "year": 2024, "stock": 5}


def suite(mode, other):
    base = f"/api/{mode}/books"
    print(f"\n===== {mode.upper()} ({'PostgreSQL' if mode == 'sql' else 'MongoDB'}) =====")
    s, t, h = call("GET", f"/api/{mode}/health")
    check(f"{mode} health 200 dan connected", s == 200 and js(t) and js(t)["database"] == "connected", t.strip()[:120])
    s, t, _ = call("GET", base)
    before = js(t)
    check(f"{mode} list 200 berformat {{data,total}}", s == 200 and before and "data" in before and before["total"] == len(before["data"]), f"total={before and before['total']}")
    s, t, _ = call("GET", f"/api/{other}/books")
    other_before = js(t)

    # CREATE
    s, t, _ = call("POST", base, BOOK)
    created = js(t)
    ok = s == 201 and created and created["data"]["title"] == BOOK["title"]
    check(f"{mode} CREATE 201", ok, f"HTTP {s} {t.strip()[:150]}")
    if not ok:
        return
    book_id = created["data"]["id"]
    CREATED[mode].append(book_id)
    if mode == "sql":
        check("sql id bertipe integer", isinstance(book_id, int), repr(book_id))
    else:
        check("nosql id string 24 heksadesimal", isinstance(book_id, str) and len(book_id) == 24 and all(c in "0123456789abcdef" for c in book_id.lower()), repr(book_id))
    expected = {"id", "title", "author", "category", "year", "stock"}
    check(f"{mode} bentuk JSON data konsisten (field)", set(created["data"]) == expected, str(sorted(created["data"])))

    # READ
    s, t, _ = call("GET", f"{base}/{book_id}")
    check(f"{mode} READ satu buku 200", s == 200 and js(t)["data"]["id"] == book_id, f"HTTP {s}")
    s, t, _ = call("GET", base)
    listed = js(t)
    check(f"{mode} READ daftar memuat buku uji di urutan teratas", s == 200 and listed["data"][0]["id"] == book_id and listed["total"] == before["total"] + 1, f"total {before['total']} -> {listed['total']}")

    # ISOLASI
    s, t, _ = call("GET", f"/api/{other}/books")
    after_other = js(t)
    check(f"{mode} tidak mengubah database {other} (jumlah sama, buku uji tidak muncul)", after_other["total"] == other_before["total"] and not any(b["title"] == BOOK["title"] for b in after_other["data"]), f"{other}: {other_before['total']} -> {after_other['total']}")

    # UPDATE
    updated = {**BOOK, "title": "[UJI-UNIFIED] Buku Uji Diubah", "year": 2023, "stock": 42}
    s, t, _ = call("PUT", f"{base}/{book_id}", updated)
    check(f"{mode} UPDATE 200", s == 200 and js(t)["data"]["stock"] == 42, f"HTTP {s} {t.strip()[:120]}")
    s, t, _ = call("GET", f"{base}/{book_id}")
    d = js(t)["data"]
    check(f"{mode} UPDATE tersimpan (GET ulang)", d["title"].endswith("Diubah") and d["year"] == 2023 and d["stock"] == 42, json.dumps(d, ensure_ascii=False))

    # VALIDASI
    bad_payloads = {
        "judul kosong": {**BOOK, "title": " "},
        "stok negatif": {**BOOK, "stock": -1},
        "tahun di luar batas": {**BOOK, "year": 1800},
        "tipe salah (year string, stock boolean)": {**BOOK, "year": "2024", "stock": True},
        "judul terlalu panjang": {**BOOK, "title": "x" * 151},
    }
    for label, payload in bad_payloads.items():
        s, t, _ = call("POST", base, payload)
        check(f"{mode} POST {label} -> 400", s == 400 and js(t) and "error" in js(t), f"HTTP {s}")
    s, t, _ = call("POST", base, raw=b"bukan json")
    check(f"{mode} POST bukan JSON -> 400", s == 400, f"HTTP {s}")
    s, t, _ = call("POST", base)
    check(f"{mode} POST tanpa badan -> 400", s == 400, f"HTTP {s}")
    s, t, _ = call("PUT", f"{base}/{book_id}", {**BOOK, "stock": -5})
    check(f"{mode} PUT data tidak valid -> 400 dan data lama utuh", s == 400 and js(call("GET", f"{base}/{book_id}")[1])["data"]["stock"] == 42, f"HTTP {s}")

    # DELETE
    s, t, _ = call("DELETE", f"{base}/{book_id}")
    check(f"{mode} DELETE 200", s == 200, f"HTTP {s} {t.strip()[:100]}")
    CREATED[mode].remove(book_id)
    s, t, _ = call("GET", f"{base}/{book_id}")
    check(f"{mode} GET setelah DELETE -> 404", s == 404, f"HTTP {s}")
    s, t, _ = call("DELETE", f"{base}/{book_id}")
    check(f"{mode} DELETE ulang -> 404", s == 404, f"HTTP {s}")
    s, t, _ = call("GET", base)
    final = js(t)
    check(f"{mode} data kembali seperti semula", final["total"] == before["total"] and [b["id"] for b in final["data"]] == [b["id"] for b in before["data"]], f"total {final['total']}")


def nosql_extra():
    print("\n===== NOSQL: ID, injeksi, galat =====")
    base = "/api/nosql/books"
    for bad in ["abc", "123", "507f1f77bcf86cd79943901z", "507f1f77bcf86cd7994390111", "%24ne", "%7B%22%24ne%22%3A1%7D", "507f1f77bcf86cd799439011%0A"]:
        for method in ("GET", "PUT", "DELETE"):
            body = BOOK if method == "PUT" else None
            s, t, _ = call(method, f"{base}/{bad}", body)
            check(f"nosql {method} id tidak valid '{bad}' -> 400 JSON (tanpa query ke DB)", s == 400 and js(t) and "error" in js(t), f"HTTP {s}")
    missing = "507f1f77bcf86cd799439011"
    for method in ("GET", "PUT", "DELETE"):
        s, t, _ = call(method, f"{base}/{missing}", BOOK if method == "PUT" else None)
        check(f"nosql {method} ObjectId valid tetapi tidak ada -> 404", s == 404 and js(t) and "error" in js(t), f"HTTP {s}")
    # injeksi operator
    for label, payload in {
        "$ne pada title": {**BOOK, "title": {"$ne": ""}},
        "$gt pada stock": {**BOOK, "stock": {"$gt": 0}},
        "$where di kolom teks": {**BOOK, "author": {"$where": "sleep(2000)"}},
        "array pada category": {**BOOK, "category": ["Umum", {"$ne": 1}]},
    }.items():
        s, t, _ = call("POST", base, payload)
        check(f"nosql injeksi {label} -> 400", s == 400, f"HTTP {s}")
    # kolom asing tidak tersimpan
    s, t, _ = call("POST", base, {**BOOK, "$where": "1", "role": "admin", "_id": "000000000000000000000000"})
    created = js(t)
    if s == 201:
        CREATED["nosql"].append(created["data"]["id"])
        check("nosql kolom asing diabaikan (_id dari klien tidak dipakai, field asing tidak tersimpan)", set(created["data"]) == {"id", "title", "author", "category", "year", "stock"} and created["data"]["id"] != "000000000000000000000000", json.dumps(created["data"]))
        call("DELETE", f"{base}/{created['data']['id']}")
        CREATED["nosql"].remove(created["data"]["id"])
    else:
        check("nosql kolom asing diabaikan", False, f"HTTP {s}")
    # galat umum berformat JSON
    s, t, h = call("PATCH", base)
    check("nosql metode tidak didukung -> 405 JSON", s == 405 and js(t) and "error" in js(t), f"HTTP {s} {t.strip()[:80]}")
    s, t, h = call("GET", "/api/nosql/tidakada")
    check("nosql rute tidak ada -> 404 JSON", s == 404 and js(t) and "error" in js(t), f"HTTP {s}")
    s, t, _ = call("POST", base, raw=b"x" * 40000)
    check("nosql badan terlalu besar (40 KB) -> ditolak (413)", s == 413, f"HTTP {s}")
    s, t, _ = call("POST", base, raw=json.dumps(BOOK).encode(), headers={"Content-Type": "text/plain"})
    check("nosql Content-Type bukan JSON -> 400", s == 400, f"HTTP {s}")


def leakage():
    print("\n===== Kebocoran informasi =====")
    probes = [("GET", "/api/sql/books"), ("GET", "/api/nosql/books"), ("GET", "/api/nosql/books/abc"), ("GET", "/api/nosql/tidakada"),
              ("POST", "/api/nosql/books"), ("GET", "/api/sql/health"), ("GET", "/api/nosql/health")]
    words = ["mongodb://", "password", "passwd", "traceback", "libraryku_app", "mongo_admin", "libraryku_user", "/app/", "File \""]
    leaked = []
    for method, path in probes:
        s, t, h = call(method, path)
        for w in words:
            if w.lower() in t.lower():
                leaked.append((path, w))
    check("badan respons tidak memuat kredensial, URI, nama pengguna DB, atau jejak tumpukan", not leaked, str(leaked))
    s, t, h = call("GET", "/api/nosql/health")
    check("header Server tidak membuka versi Nginx", h.get("Server", "") == "nginx", h.get("Server", ""))
    for name in ("X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy", "Referrer-Policy"):
        check(f"header {name} ada", name in h, h.get(name, "(tidak ada)")[:80])
    check("tidak ada header CORS terbuka (Access-Control-Allow-Origin)", "Access-Control-Allow-Origin" not in h, str(h.get("Access-Control-Allow-Origin")))
    s, t, h = call("GET", "/api/nosql/books", headers={"Origin": "http://contoh-asing.test"})
    check("permintaan lintas-origin tidak mendapat izin CORS", "Access-Control-Allow-Origin" not in h, str(h.get("Access-Control-Allow-Origin")))


def legacy():
    print("\n===== Kompatibilitas alamat lama =====")
    s, t, _ = call("GET", "/api/health")
    check("/api/health lama tetap 200", s == 200, f"HTTP {s}")
    s1, t1, _ = call("GET", "/api/books")
    s2, t2, _ = call("GET", "/api/sql/books")
    check("/api/books lama = isi /api/sql/books (PostgreSQL)", s1 == 200 and js(t1) == js(t2), f"total lama={js(t1)['total']} baru={js(t2)['total']}")


try:
    legacy()
    suite("sql", "nosql")
    suite("nosql", "sql")
    nosql_extra()
    leakage()
finally:
    for mode, ids in CREATED.items():
        for book_id in list(ids):
            call("DELETE", f"/api/{mode}/books/{book_id}")
            print(f"[bersih-bersih] hapus buku uji {mode} {book_id}")

passed, total = sum(RESULTS), len(RESULTS)
print(f"\nRINGKASAN: {passed} PASS, {total - passed} FAIL dari {total} pemeriksaan")
sys.exit(0 if passed == total else 1)
