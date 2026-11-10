"""Uji keamanan terarah pada aplikasi LOKAL LibraryKu Unified (hanya localhost, buku uji dihapus di akhir)."""
import base64, os, json, time, sys, urllib.request, urllib.error, subprocess
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8081").rstrip("/")
R = []; CREATED = []
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


def call(m, p, body=None, raw=None, headers=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Content-Type": "application/json"} if data is not None else {}
    if m not in ("GET", "HEAD", "OPTIONS"):
        h.update(AUTH); h["X-Requested-With"] = "libraryku"; time.sleep(0.6)  # jeda agar tidak kena batas laju tulis
    h.update(headers or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + p, data=data, method=m, headers=h), timeout=15) as x:
            return x.status, x.read().decode(), dict(x.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), dict(e.headers)
def js(t):
    try: return json.loads(t)
    except ValueError: return None
def check(n, c, d=""):
    R.append(bool(c)); print(("PASS " if c else "FAIL ") + n + (f" | {d}" if d else ""))
B = {"title": "x", "author": "a", "category": "Umum", "year": 2024, "stock": 1}
try:
    print("== SQL injection (PostgreSQL) ==")
    n0 = js(call("GET", "/api/sql/books")[1])["total"]
    for label, payload in {"akhiri query + DROP": "'); DROP TABLE books; --", "OR selalu benar": "' OR '1'='1", "UNION": "x' UNION SELECT 1,2,3,4,5 --"}.items():
        s, t, _ = call("POST", "/api/sql/books", {**B, "title": payload})
        d = js(t)
        ok = s == 201 and d["data"]["title"] == payload
        check(f"payload '{label}' tersimpan sebagai teks biasa (query berparameter)", ok, f"HTTP {s}")
        if s == 201: CREATED.append(("sql", d["data"]["id"]))
    check("tabel books masih utuh dan jumlah bertambah tepat 3", js(call("GET", "/api/sql/books")[1])["total"] == n0 + 3)
    for bad in ["1%20OR%201=1", "1;DROP%20TABLE%20books", "-1", "1.5", "abc", "99999999999999999999"]:
        s, t, _ = call("GET", f"/api/sql/books/{bad}")
        check(f"SQL id '{bad}' tidak mengembalikan data dan tidak galat 500", s in (404, 400), f"HTTP {s}")
    print("== NoSQL injection (MongoDB) ==")
    n1 = js(call("GET", "/api/nosql/books")[1])["total"]
    s, t, _ = call("GET", "/api/nosql/books?title[$ne]=x&$where=1&author[$regex]=.*")
    check("parameter query berisi operator diabaikan (tidak ada filter dari pengguna, tidak galat)", s == 200 and js(t)["total"] == n1, f"HTTP {s}")
    for label, payload in {"JS di string": "'; return true; var x='", "operator sebagai teks": "{\"$ne\": null}", "$where sebagai teks": "$where: sleep(5000)"}.items():
        s, t, _ = call("POST", "/api/nosql/books", {**B, "title": payload})
        d = js(t); ok = s == 201 and d["data"]["title"] == payload
        check(f"nilai '{label}' hanya tersimpan sebagai string biasa", ok, f"HTTP {s}")
        if s == 201: CREATED.append(("nosql", d["data"]["id"]))
    print("== XSS tersimpan: API mengirim teks, bukan HTML ==")
    xss = '<img src=x onerror=alert(document.domain)>'
    for mode in ("sql", "nosql"):
        s, t, h = call("POST", f"/api/{mode}/books", {**B, "title": xss}); d = js(t)
        if s == 201: CREATED.append((mode, d["data"]["id"]))
        s, t, h = call("GET", f"/api/{mode}/books")
        check(f"{mode}: Content-Type application/json + nosniff", h.get("Content-Type", "").startswith("application/json") and h.get("X-Content-Type-Options") == "nosniff", h.get("Content-Type", ""))
    print("== CSRF dan CORS ==")
    for mode in ("sql", "nosql"):
        s, t, _ = call("POST", f"/api/{mode}/books", raw=json.dumps(B).encode(), headers={"Content-Type": "text/plain"})
        check(f"{mode}: POST lintas-situs ala form (text/plain) ditolak", s == 400, f"HTTP {s}")
        s, t, h = call("OPTIONS", f"/api/{mode}/books", headers={"Origin": "http://contoh-asing.test", "Access-Control-Request-Method": "DELETE"})
        check(f"{mode}: preflight CORS tidak memberi izin", "Access-Control-Allow-Origin" not in h, str(h.get("Access-Control-Allow-Origin")))
    print("== Metode dan header ==")
    for m in ("TRACE", "CONNECT"):
        try:
            s, t, h = call(m, "/api/nosql/books")
        except Exception as e:
            s = 0
        check(f"metode {m} tidak diterima", s in (0, 400, 405, 501), f"HTTP {s}")
    print("== Port di host (LibraryKu) ==")
    out = subprocess.run(["ss", "-ltn"], capture_output=True, text=True).stdout
    check("tidak ada listener 27017 (MongoDB) di host", ":27017 " not in out)
    check("tidak ada listener 5000 (Flask) di host", ":5000 " not in out)
    check("8081 hanya mendengarkan di 127.0.0.1 (Nginx LibraryKu, tidak terbuka ke jaringan)", ":8081 " in out and "0.0.0.0:8081" not in out and "[::]:8081" not in out)
finally:
    for mode, i in CREATED:
        call("DELETE", f"/api/{mode}/books/{i}")
    print(f"[bersih-bersih] {len(CREATED)} buku uji dihapus")
p = sum(R); print(f"\nRINGKASAN: {p} PASS, {len(R) - p} FAIL dari {len(R)}")
sys.exit(0 if p == len(R) else 1)
