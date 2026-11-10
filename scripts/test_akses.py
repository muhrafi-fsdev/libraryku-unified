"""Uji kontrol akses untuk akses publik: operasi tulis wajib login, header CSRF, pembatasan laju.
Jalankan setelah ./scripts/ctl.sh apply-frontend. Hanya menyentuh localhost; buku uji dihapus di akhir.
Kredensial dibaca dari ~/.libraryku_dashboard_credentials (izin 600) dan tidak pernah dicetak."""
import base64, json, os, sys, time, subprocess, urllib.request, urllib.error
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8081").rstrip("/")
kv = dict(l.strip().split("=", 1) for l in open(os.path.expanduser("~/.libraryku_dashboard_credentials")) if "=" in l)
GOOD = "Basic " + base64.b64encode(f"{kv['username']}:{kv['password']}".encode()).decode()
BAD_PW = "Basic " + base64.b64encode(f"{kv['username']}:salah-sekali".encode()).decode()
BAD_USER = "Basic " + base64.b64encode(f"bukan-admin:{kv['password']}".encode()).decode()
class CIDict(dict):
    """Nama header tidak peka huruf besar/kecil (HTTP/2 mengirim huruf kecil)."""
    def get(self, k, d=None): return super().get(k.lower(), d)
    def __contains__(self, k): return super().__contains__(k.lower())
    def __getitem__(self, k): return super().__getitem__(k.lower())
def _ci(h): return CIDict({k.lower(): v for k, v in dict(h).items()})
R = []; CREATED = []
def call(m, p, body=None, auth=None, xrw=True, raw=None, ctype="application/json", extra=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Content-Type": ctype} if data is not None else {}
    if auth: h["Authorization"] = auth
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
def pause(): time.sleep(0.7)
BOOK = {"title": "[UJI-AKSES] Buku", "author": "Penguji", "category": "Umum", "year": 2024, "stock": 1}
SECH = ("X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy", "Strict-Transport-Security")
try:
    print("== Membaca tanpa login tetap boleh (mode publik read-only) ==")
    for p in ("/api/sql/health", "/api/nosql/health", "/api/sql/books", "/api/nosql/books", "/api/health", "/api/books"):
        s, t, h = call("GET", p, xrw=False); check(f"GET {p} tanpa login -> 200", s == 200, f"HTTP {s}")
    s, t, h = call("GET", "/", xrw=False); check("halaman utama tanpa login -> 200", s == 200)
    print("== Menulis tanpa login ditolak (semua endpoint tulis) ==")
    for base in ("/api/sql/books", "/api/nosql/books", "/api/books"):
        some = "1" if base != "/api/nosql/books" else "507f1f77bcf86cd799439011"
        for m, p, b in (("POST", base, BOOK), ("PUT", f"{base}/{some}", BOOK), ("DELETE", f"{base}/{some}", None)):
            pause(); s, t, h = call(m, p, b)
            check(f"{m} {p} tanpa login -> 401 JSON + WWW-Authenticate", s == 401 and js(t) and "error" in js(t) and "Basic" in h.get("WWW-Authenticate", ""), f"HTTP {s}")
    print("== Kredensial salah ditolak ==")
    for label, a in (("kata sandi salah", BAD_PW), ("nama pengguna salah", BAD_USER)):
        pause(); s, t, h = call("POST", "/api/sql/books", BOOK, auth=a); check(f"POST dengan {label} -> 401", s == 401, f"HTTP {s}")
    print("== Perlindungan CSRF (header X-Requested-With wajib untuk tulis) ==")
    pause(); s, t, h = call("POST", "/api/sql/books", BOOK, auth=GOOD, xrw=False); check("login benar tetapi tanpa header aplikasi -> 403", s == 403, f"HTTP {s}")
    pause(); s, t, h = call("DELETE", "/api/nosql/books/507f1f77bcf86cd799439011", auth=GOOD, xrw=False); check("DELETE tanpa header aplikasi -> 403", s == 403, f"HTTP {s}")
    pause(); s, t, h = call("POST", "/api/sql/books", raw=json.dumps(BOOK).encode(), auth=GOOD, ctype="text/plain"); check("POST ala form text/plain walau login benar -> 400", s == 400, f"HTTP {s}")
    s, t, h = call("OPTIONS", "/api/sql/books", xrw=False, extra={"Origin": "http://contoh-asing.test", "Access-Control-Request-Method": "DELETE", "Access-Control-Request-Headers": "x-requested-with"})
    check("preflight CORS lintas-origin tidak diberi izin", "Access-Control-Allow-Origin" not in h, f"HTTP {s}")
    print("== Dengan login yang benar, CRUD tetap berfungsi di kedua database ==")
    for mode in ("sql", "nosql"):
        base = f"/api/{mode}/books"
        pause(); s, t, h = call("POST", base, BOOK, auth=GOOD); d = js(t)
        ok = s == 201 and d; check(f"{mode} POST dengan login -> 201", ok, f"HTTP {s}")
        if not ok: continue
        i = d["data"]["id"]; CREATED.append((mode, i))
        pause(); s, t, h = call("PUT", f"{base}/{i}", {**BOOK, "stock": 5}, auth=GOOD); check(f"{mode} PUT dengan login -> 200", s == 200 and js(t)["data"]["stock"] == 5, f"HTTP {s}")
        pause(); s, t, h = call("DELETE", f"{base}/{i}", auth=GOOD); check(f"{mode} DELETE dengan login -> 200", s == 200, f"HTTP {s}")
        CREATED.remove((mode, i))
        s, t, h = call("GET", f"{base}/{i}", xrw=False); check(f"{mode} data benar-benar terhapus (GET 404)", s == 404, f"HTTP {s}")
    print("== Kredensial tidak diteruskan ke backend dan tidak bocor ==")
    pause(); s, t, h = call("POST", "/api/sql/books", {**BOOK, "title": 'x' * 200}, auth=GOOD)
    check("galat validasi tetap JSON tanpa data sensitif", s == 400 and kv["password"] not in t and "htpasswd" not in t.lower(), f"HTTP {s}")
    print("== Pembatasan laju untuk operasi tulis ==")
    time.sleep(3); codes = []
    for _ in range(25): codes.append(call("POST", "/api/sql/books", BOOK, auth=BAD_PW)[0])
    check("rentetan tulis (percobaan login salah) dibatasi: ada 429", 429 in codes and codes.count(401) >= 3, f"{codes.count(401)}x401, {codes.count(429)}x429")
    s, t, h = call("POST", "/api/sql/books", BOOK, auth=BAD_PW)
    check("balasan 429 berformat JSON + Retry-After", (s != 429) or (js(t) and "error" in js(t) and "Retry-After" in h), f"HTTP {s}")
    time.sleep(3)
    codes = [call("GET", "/api/sql/health", xrw=False)[0] for _ in range(30)]
    check("30 pembacaan cepat tetap normal (batas baca longgar)", codes.count(200) >= 28, f"{codes.count(200)}x200")
    print("== Header keamanan pada semua jenis respons ==")
    time.sleep(3)
    for label, (s, t, h) in {"GET 200": call("GET", "/api/sql/books", xrw=False), "401": call("POST", "/api/sql/books", BOOK), "403": call("POST", "/api/sql/books", BOOK, xrw=False)}.items():
        check(f"header keamanan lengkap pada respons {label}", all(k in h for k in SECH), ", ".join(k for k in SECH if k not in h) or "lengkap")
    s, t, h = call("GET", "/", xrw=False); check("Server tidak menampilkan versi", h.get("Server", "") == "nginx", h.get("Server", ""))
    s, t, h = call("POST", "/api/sql/books", raw=b"x" * 40000, auth=GOOD); check("badan 40 KB ditolak (413)", s == 413, f"HTTP {s}")
    print("== Port ==")
    out = subprocess.run(["ss", "-ltn"], capture_output=True, text=True).stdout
    lines = [l for l in out.splitlines() if ":8081 " in l]
    check("8081 hanya mendengarkan di 127.0.0.1 (tidak di 0.0.0.0/[::])", lines and all("127.0.0.1:8081" in l for l in lines), "; ".join(l.split()[3] for l in lines))
    check("tidak ada listener 27017/5432/5000 milik LibraryKu di antarmuka publik", all(not any(x in l for x in ("0.0.0.0:27017", "0.0.0.0:5000", "0.0.0.0:5432", "*:27017")) for l in out.splitlines()))
finally:
    time.sleep(2)
    for mode, i in CREATED:
        call("DELETE", f"/api/{mode}/books/{i}", auth=GOOD)
        print(f"[bersih-bersih] hapus {mode} {i}")
p = sum(R); print(f"\nRINGKASAN: {p} PASS, {len(R) - p} FAIL dari {len(R)}")
sys.exit(0 if p == len(R) else 1)
