"""Mengambil respons JSON nyata dari semua endpoint API untuk laporan (lewat alamat publik atau lokal).

Pemakaian: python3 scripts/ambil_json.py [BASE_URL]
Hasil: bukti/laporan/respons_json.txt dan bukti/laporan/respons_json.json
Membuat satu buku uji per database lalu menghapusnya lagi. Tanpa login (mode terbuka).
"""
import json, os, sys, time, urllib.error, urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://libraryku-kali.tail342a2f.ts.net").rstrip("/")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bukti", "laporan")
os.makedirs(OUT, exist_ok=True)
lines, rows = [], []


def call(label, method, path, body=None, xrw=True):
    h = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    if method != "GET" and xrw:
        h["X-Requested-With"] = "libraryku"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            code, txt = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        code, txt = e.code, e.read().decode()
    try:
        js = json.loads(txt)
    except ValueError:
        js = txt
    lines.append(f"### {label}\n{method} {path}" + (f"\nBody: {json.dumps(body, ensure_ascii=False)}" if body else "") +
                 (f"\n(tanpa header aplikasi)" if not xrw else "") + f"\nHTTP {code}\n{txt.strip()}\n")
    rows.append({"label": label, "method": method, "path": path, "xrw": xrw, "status": code, "body": js})
    print(f"{code} {method} {path}")
    if method != "GET":
        time.sleep(0.8)
    return code, js


buku = {"title": "Cloud Computing Praktis", "author": "Kelompok Cloud", "category": "Teknologi", "year": 2025, "stock": 12}
for db, nama in (("sql", "PostgreSQL"), ("nosql", "MongoDB")):
    call(f"{nama}: health", "GET", f"/api/{db}/health")
    call(f"{nama}: daftar buku", "GET", f"/api/{db}/books")
    c, js = call(f"{nama}: tambah buku (valid)", "POST", f"/api/{db}/books", buku)
    bid = js["data"]["id"]
    call(f"{nama}: ambil satu buku", "GET", f"/api/{db}/books/{bid}")
    call(f"{nama}: ubah buku", "PUT", f"/api/{db}/books/{bid}", {**buku, "stock": 30})
    call(f"{nama}: tambah buku (data tidak valid)", "POST", f"/api/{db}/books", {**buku, "title": "", "year": 1800})
    call(f"{nama}: tulis tanpa header aplikasi", "POST", f"/api/{db}/books", buku, xrw=False)
    call(f"{nama}: hapus buku", "DELETE", f"/api/{db}/books/{bid}")
    call(f"{nama}: ambil buku yang sudah dihapus", "GET", f"/api/{db}/books/{bid}")

open(os.path.join(OUT, "respons_json.txt"), "w").write(f"Alamat dasar: {BASE}\n\n" + "\n".join(lines))
json.dump(rows, open(os.path.join(OUT, "respons_json.json"), "w"), ensure_ascii=False, indent=1)
for db in ("sql", "nosql"):
    with urllib.request.urlopen(f"{BASE}/api/{db}/books", timeout=20) as r:
        print(db, "total akhir:", json.load(r)["total"])
