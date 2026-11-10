"""Uji kontrol akses untuk MODE TERBUKA (tanpa nama pengguna dan kata sandi).

Yang diuji: membaca dan menulis berjalan tanpa login; penulisan tetap dilindungi header aplikasi (CSRF),
pembatasan laju, batas ukuran badan, dan validasi; header keamanan; port. Semua galat API berformat JSON.
Pemakaian: python3 scripts/test_akses.py [BASE_URL]   (bawaan http://127.0.0.1:8081)
Buku uji dihapus di akhir. Tidak ada kredensial yang dipakai."""
import json, subprocess, sys, time, urllib.error, urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8081").rstrip("/")


class CIDict(dict):
    """Nama header tidak peka huruf besar/kecil (HTTP/2 mengirim huruf kecil)."""
    def get(self, k, d=None): return super().get(k.lower(), d)
    def __contains__(self, k): return super().__contains__(k.lower())
    def __getitem__(self, k): return super().__getitem__(k.lower())


def _ci(h): return CIDict({k.lower(): v for k, v in dict(h).items()})


R = []; CREATED = []


def call(m, p, body=None, xrw=True, raw=None, ctype="application/json", extra=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Content-Type": ctype} if data is not None else {}
    if xrw: h["X-Requested-With"] = "libraryku"
    h.update(extra or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + p, data=data, method=m, headers=h), timeout=15) as x:
            return x.status, x.read().decode(), _ci(x.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), _ci(e.headers)


def js(t):
    try: return json.loads(t)
    except ValueError: return None


def check(n, c, d=""):
    R.append(bool(c)); print(("PASS " if c else "FAIL ") + n + (f" | {d}" if d else ""))


def pause(): time.sleep(0.25)


BOOK = {"title": "[UJI-AKSES] Buku", "author": "Penguji", "category": "Umum", "year": 2024, "stock": 1}
SECH = ("X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy", "Strict-Transport-Security")
try:
    print("== Membaca tanpa login ==")
    for p in ("/api/sql/health", "/api/nosql/health", "/api/sql/books", "/api/nosql/books", "/api/health", "/api/books"):
        s, t, h = call("GET", p, xrw=False); check(f"GET {p} -> 200", s == 200, f"HTTP {s}")
    s, t, h = call("GET", "/", xrw=False); check("halaman utama -> 200", s == 200)
    s, t, h = call("GET", "/api/auth-check", xrw=False); check("tidak ada lagi pemeriksa login (/api/auth-check -> 404 JSON)", s == 404 and js(t) and "error" in js(t), f"HTTP {s}")

    print("== Menulis tanpa login berhasil di kedua database (dengan header aplikasi) ==")
    for mode in ("sql", "nosql"):
        base = f"/api/{mode}/books"
        pause(); s, t, h = call("POST", base, BOOK); d = js(t)
        ok = s == 201 and d and "data" in d; check(f"{mode} POST tanpa login -> 201", ok, f"HTTP {s}")
        if not ok: continue
        i = d["data"]["id"]; CREATED.append((mode, i))
        pause(); s, t, h = call("GET", f"{base}/{i}", xrw=False); check(f"{mode} GET id baru -> 200", s == 200 and js(t)["data"]["title"] == BOOK["title"], f"HTTP {s}")
        pause(); s, t, h = call("PUT", f"{base}/{i}", {**BOOK, "stock": 9}); check(f"{mode} PUT tanpa login -> 200", s == 200 and js(t)["data"]["stock"] == 9, f"HTTP {s}")
        pause(); s, t, h = call("DELETE", f"{base}/{i}"); check(f"{mode} DELETE tanpa login -> 200", s == 200, f"HTTP {s}")
        CREATED.remove((mode, i))
        pause(); s, t, h = call("GET", f"{base}/{i}", xrw=False); check(f"{mode} data benar-benar terhapus (GET 404)", s == 404 and js(t) and "error" in js(t), f"HTTP {s}")

    print("== Perlindungan CSRF (header X-Requested-With wajib untuk tulis) ==")
    for m, p, b in (("POST", "/api/sql/books", BOOK), ("PUT", "/api/sql/books/1", BOOK), ("DELETE", "/api/nosql/books/507f1f77bcf86cd799439011", None), ("POST", "/api/nosql/books", BOOK), ("POST", "/api/books", BOOK)):
        pause(); s, t, h = call(m, p, b, xrw=False); check(f"{m} {p} tanpa header aplikasi -> 403 JSON", s == 403 and js(t) and "error" in js(t), f"HTTP {s}")
    pause(); s, t, h = call("POST", "/api/sql/books", raw=json.dumps(BOOK).encode(), ctype="text/plain"); check("POST ala form (text/plain) -> 400, tidak membuat data", s == 400, f"HTTP {s}")
    s, t, h = call("OPTIONS", "/api/sql/books", xrw=False, extra={"Origin": "http://contoh-asing.test", "Access-Control-Request-Method": "DELETE", "Access-Control-Request-Headers": "x-requested-with"})
    check("preflight CORS lintas-origin tidak diberi izin", "Access-Control-Allow-Origin" not in h, f"HTTP {s}")

    print("== Galat API selalu JSON (bukan halaman HTML) ==")
    for m, p in (("GET", "/api/sql/tidak-ada"), ("GET", "/api/nosql/tidak-ada"), ("GET", "/api/sql/books/abc"), ("PUT", "/api/sql/books"), ("DELETE", "/api/nosql/books"), ("PATCH", "/api/sql/books/1")):
        pause(); s, t, h = call(m, p, xrw=True); check(f"{m} {p} -> {s} JSON", js(t) is not None and "error" in js(t) and "json" in h.get("Content-Type", ""), f"HTTP {s}")
    pause(); s, t, h = call("POST", "/api/sql/books", raw=b"{rusak", ctype="application/json"); check("POST JSON rusak -> 400 JSON", s == 400 and js(t) is not None, f"HTTP {s}")
    for payload, nama in (({**BOOK, "year": True}, "year boolean"), ({**BOOK, "stock": -1}, "stok negatif"), ({**BOOK, "title": "   "}, "judul spasi"), ({**BOOK, "year": "2020"}, "year string"), ({**BOOK, "stock": 1.5}, "stok desimal")):
        pause(); s, t, h = call("POST", "/api/sql/books", payload); check(f"validasi menolak {nama} -> 400", s == 400 and js(t) and "details" in js(t), f"HTTP {s}")

    print("== Pembatasan laju untuk operasi tulis (data tidak dibuat: badan kosong) ==")
    time.sleep(3); codes = []
    for _ in range(60): codes.append(call("POST", "/api/sql/books", {})[0])
    check("rentetan tulis dibatasi: ada 429", 429 in codes and codes.count(400) >= 5, f"{codes.count(400)}x400, {codes.count(429)}x429")
    time.sleep(0.2); s, t, h = call("POST", "/api/sql/books", {})
    check("balasan 429 berformat JSON + Retry-After", (s != 429) or (js(t) and "error" in js(t) and "Retry-After" in h), f"HTTP {s}")
    time.sleep(4)
    codes = [call("GET", "/api/sql/health", xrw=False)[0] for _ in range(30)]
    check("30 pembacaan cepat tetap normal (batas baca longgar)", codes.count(200) >= 28, f"{codes.count(200)}x200")
    check("tulis normal pulih setelah jeda", call("POST", "/api/sql/books", {})[0] == 400)

    print("== Header keamanan pada semua jenis respons ==")
    time.sleep(2)
    for label, (s, t, h) in {"GET 200": call("GET", "/api/sql/books", xrw=False), "400": call("POST", "/api/sql/books", {}), "403": call("POST", "/api/sql/books", BOOK, xrw=False), "404": call("GET", "/api/sql/tidak-ada", xrw=False)}.items():
        check(f"header keamanan lengkap pada respons {label}", all(k in h for k in SECH), ", ".join(k for k in SECH if k not in h) or "lengkap")
    s, t, h = call("GET", "/", xrw=False); check("Server tidak menampilkan versi", h.get("Server", "") == "nginx", h.get("Server", ""))
    pause(); s, t, h = call("POST", "/api/sql/books", raw=b"x" * 40000); check("badan 40 KB ditolak (413)", s == 413, f"HTTP {s}")

    print("== Port ==")
    out = subprocess.run(["ss", "-ltn"], capture_output=True, text=True).stdout
    lines = [l for l in out.splitlines() if ":8081 " in l]
    check("8081 hanya mendengarkan di 127.0.0.1 (tidak di 0.0.0.0/[::])", lines and all("127.0.0.1:8081" in l for l in lines), "; ".join(l.split()[3] for l in lines))
    check("tidak ada listener 27017/5432/5000 milik LibraryKu di antarmuka publik", all(not any(x in l for x in ("0.0.0.0:27017", "0.0.0.0:5000", "0.0.0.0:5432", "*:27017")) for l in out.splitlines()))
finally:
    time.sleep(2)
    for mode, i in CREATED:
        call("DELETE", f"/api/{mode}/books/{i}")
        print(f"[bersih-bersih] hapus {mode} {i}")
p = sum(R); print(f"\nRINGKASAN: {p} PASS, {len(R) - p} FAIL dari {len(R)}")
sys.exit(0 if p == len(R) else 1)
