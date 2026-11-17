"""Uji fitur Peminjaman dan Pengembalian pada STACK SEMENTARA (jangan diarahkan ke database aktif).

Pemakaian: python3 scripts/test_peminjaman.py BASE_URL TAHAP
TAHAP: sebelum | akses | fungsional | failclosed
Kredensial uji fiktif dibaca dari variabel lingkungan UJI_USER dan UJI_PASS (dibuat oleh scripts/uji_peminjaman.sh).
Semua data di sini fiktif. Skrip ini tidak mencetak kata sandi."""
import base64, json, os, sys, threading, time, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone

BASE = sys.argv[1].rstrip("/")
TAHAP = sys.argv[2]
USER, PASS = os.environ["UJI_USER"], os.environ["UJI_PASS"]
GOOD = "Basic " + base64.b64encode(f"{USER}:{PASS}".encode()).decode()
BAD = "Basic " + base64.b64encode(f"{USER}:salah-sekali".encode()).decode()
R = []


def call(method, path, body=None, auth=GOOD, xrw=True, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if auth:
        headers["Authorization"] = auth
    if xrw and method != "GET":
        headers["X-Requested-With"] = "libraryku"
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path, data=data, method=method, headers=headers), timeout=20) as r:
            status, text, hdr = r.status, r.read().decode(), r.headers
    except urllib.error.HTTPError as e:
        status, text, hdr = e.code, e.read().decode(), e.headers
    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = text
    return status, parsed, {k.lower(): v for k, v in dict(hdr).items()}


def check(name, cond, detail=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + (f" | {detail}" if detail != "" else ""))


def pause():
    time.sleep(0.3)  # batas peminjaman 5 permintaan/detik


def today_wib():
    return datetime.now(timezone(timedelta(hours=7))).date()


def iso(delta=0):
    return (today_wib() + timedelta(days=delta)).isoformat()


def mkbook(title, stock):
    s, d, _ = call("POST", "/api/sql/books", {"title": title, "author": "Penulis Uji", "category": "Umum", "year": 2024, "stock": stock}, auth=None)
    assert s == 201, (s, d)
    return d["data"]["id"]


def stock_of(book_id):
    s, d, _ = call("GET", f"/api/sql/books/{book_id}", auth=None)
    return d["data"]["stock"] if s == 200 else None


def loan_body(book_id, **kw):
    return {"book_id": book_id, "borrower_name": "Budi Fiktif", "borrower_class": "S1TT-UJI-01", "borrower_nim": "0012345678",
            "loan_date": iso(0), "due_date": iso(7), "note": "data fiktif", **kw}


def all_loans():
    pause(); s, d, _ = call("GET", "/api/sql/loans"); return d["data"] if s == 200 else []


def parallel(n, fn):
    out, barrier = [None] * n, threading.Barrier(n)

    def run(i):
        barrier.wait(); out[i] = fn(i)
    threads = [threading.Thread(target=run, args=(i,)) for i in range(n)]
    [t.start() for t in threads]; [t.join() for t in threads]
    return out


# ---------------------------------------------------------------------------
if TAHAP == "sebelum":
    print("== Sebelum migrasi: katalog tetap normal, fitur peminjaman memberi pesan jelas ==")
    s, d, _ = call("GET", "/api/sql/loans")
    check("GET loans sebelum migrasi -> 503 JSON yang menyebut migrasi", s == 503 and isinstance(d, dict) and "migrasi" in d.get("error", "").lower(), f"HTTP {s}")
    bid = mkbook("[UJI-PINJAM] sebelum migrasi", 1)
    s, d, _ = call("DELETE", f"/api/sql/books/{bid}", auth=None)
    check("hapus buku (tanpa tabel loans) tetap 200", s == 200, f"HTTP {s}")
    s, d, _ = call("GET", "/api/sql/books", auth=None)
    check("daftar buku katalog tetap 200", s == 200 and d["total"] >= 1, f"{d['total']} buku")

elif TAHAP == "akses":
    print("== Akses petugas: semua endpoint peminjaman terkunci tanpa login ==")
    for m, p, b in (("GET", "/api/sql/loans", None), ("GET", "/api/loans", None), ("POST", "/api/sql/loans", loan_body(1)),
                    ("POST", "/api/loans", loan_body(1)), ("POST", "/api/sql/loans/1/return", {}), ("POST", "/api/loans/1/return", {})):
        pause(); s, d, h = call(m, p, b, auth=None)
        check(f"{m} {p} tanpa login -> 401 JSON + WWW-Authenticate", s == 401 and isinstance(d, dict) and "error" in d and "basic" in h.get("www-authenticate", "").lower(), f"HTTP {s}")
    pause(); s, d, _ = call("GET", "/api/sql/loans", auth=BAD); check("kata sandi salah -> 401", s == 401, f"HTTP {s}")
    pause(); s, d, _ = call("POST", "/api/sql/loans", loan_body(1), auth=None, xrw=False); check("tulis tanpa login dan tanpa header aplikasi -> 403 (tidak membocorkan apa pun)", s == 403, f"HTTP {s}")
    pause(); s, d, _ = call("GET", "/api/sql/loans"); check("GET dengan login petugas -> 200", s == 200 and "data" in d, f"HTTP {s}")
    pause(); s, d, _ = call("GET", "/api/loans"); check("jalur langsung /api/loans dengan login -> 200", s == 200, f"HTTP {s}")
    pause(); s, d, _ = call("POST", "/api/sql/loans", loan_body(1), xrw=False); check("login benar tetapi tanpa header aplikasi -> 403", s == 403, f"HTTP {s}")
    pause(); s, d, _ = call("GET", "/api/nosql/loans"); check("mode NoSQL tidak punya fitur peminjaman -> 404 JSON", s == 404 and isinstance(d, dict), f"HTTP {s}")
    print("== Dashboard dan katalog publik tetap terbuka ==")
    for p in ("/", "/api/sql/books", "/api/nosql/books", "/api/sql/health"):
        s, d, _ = call("GET", p, auth=None); check(f"GET {p} tanpa login -> 200", s == 200, f"HTTP {s}")
    bid = mkbook("[UJI-PINJAM] publik", 1)
    s, d, _ = call("PUT", f"/api/sql/books/{bid}", {"title": "[UJI-PINJAM] publik 2", "author": "Penulis Uji", "category": "Umum", "year": 2024, "stock": 1}, auth=None)
    check("ubah buku katalog tanpa login tetap 200 (perilaku lama)", s == 200, f"HTTP {s}")
    s, d, _ = call("DELETE", f"/api/sql/books/{bid}", auth=None); check("hapus buku katalog tanpa login tetap 200 (perilaku lama)", s == 200, f"HTTP {s}")

elif TAHAP == "fungsional":
    print("== Pinjam, stok, dan riwayat ==")
    a = mkbook("[UJI-PINJAM] Buku A", 2)
    pause(); s, d, _ = call("POST", "/api/sql/loans", loan_body(a))
    loan = d["data"] if s == 201 else {}
    check("pinjam buku -> 201", s == 201, f"HTTP {s}")
    check("status Dipinjam, tanggal aktual kosong", loan.get("status") == "Dipinjam" and loan.get("returned_date") is None)
    check("NIM tersimpan sebagai teks dengan nol di depan", loan.get("borrower_nim") == "0012345678", loan.get("borrower_nim"))
    check("judul buku dicatat di riwayat", loan.get("book_title") == "[UJI-PINJAM] Buku A")
    check("stok berkurang satu (2 -> 1)", stock_of(a) == 1, f"stok {stock_of(a)}")
    rows = all_loans()
    check("riwayat memuat pinjaman itu", any(r["id"] == loan.get("id") and r["borrower_nim"] == "0012345678" for r in rows))

    print("== Validasi dan penolakan ==")
    kasus = [("batas sebelum tanggal pinjam", loan_body(a, due_date=iso(-1)), "due_date"),
             ("tanggal 2026-02-30", loan_body(a, loan_date="2026-02-30", due_date="2026-03-05"), "loan_date"),
             ("NIM bukan teks (angka JSON)", loan_body(a, borrower_nim=12345678), "borrower_nim"),
             ("NIM berisi huruf", loan_body(a, borrower_nim="12AB5678"), "borrower_nim"),
             ("nama kosong", loan_body(a, borrower_name="  "), "borrower_name"),
             ("book_id berupa teks", loan_body("1"), "book_id"),
             ("batas pengembalian kosong", {k: v for k, v in loan_body(a).items() if k != "due_date"}, "due_date")]
    for nama, body, kolom in kasus:
        pause(); s, d, _ = call("POST", "/api/sql/loans", body)
        check(f"{nama} -> 400 dengan galat pada {kolom}", s == 400 and kolom in d.get("details", {}), f"HTTP {s}")
    pause(); s, d, _ = call("POST", "/api/sql/loans", loan_body(2147483000)); check("buku tidak ditemukan -> 404", s == 404, f"HTTP {s}")
    pause(); s, d, _ = call("POST", "/api/sql/loans", raw=b"{rusak"); check("JSON rusak -> 400", s == 400, f"HTTP {s}")
    check("validasi yang ditolak tidak mengubah stok (tetap 1)", stock_of(a) == 1, f"stok {stock_of(a)}")
    b = mkbook("[UJI-PINJAM] Buku B (stok 0)", 0)
    n_before = len(all_loans())
    pause(); s, d, _ = call("POST", "/api/sql/loans", loan_body(b)); check("stok habis -> 409", s == 409 and "habis" in d.get("error", ""), f"HTTP {s}")
    check("pinjaman ditolak tidak tercatat", len(all_loans()) == n_before)

    print("== Hapus buku yang masih dipinjam ==")
    s, d, _ = call("DELETE", f"/api/sql/books/{a}", auth=None)
    check("hapus buku yang masih dipinjam -> 409", s == 409 and "dipinjam" in d.get("error", ""), f"HTTP {s}")
    check("buku masih ada dan stok tidak berubah", stock_of(a) == 1)

    print("== Pengembalian ==")
    pause(); s, d, _ = call("POST", f"/api/sql/loans/{loan['id']}/return")
    ret = d.get("data", {}) if s == 200 else {}
    check("kembalikan -> 200", s == 200, f"HTTP {s}")
    check("tanggal aktual terisi otomatis dengan hari ini (WIB), status Dikembalikan", ret.get("returned_date") == iso(0) and ret.get("status") == "Dikembalikan", ret.get("returned_date"))
    check("stok bertambah satu (1 -> 2)", stock_of(a) == 2, f"stok {stock_of(a)}")
    pause(); s, d, _ = call("POST", f"/api/sql/loans/{loan['id']}/return")
    check("pengembalian kedua -> 409", s == 409, f"HTTP {s}")
    check("pengembalian kedua tidak menambah stok (tetap 2)", stock_of(a) == 2, f"stok {stock_of(a)}")
    pause(); s, d, _ = call("POST", "/api/sql/loans/2147483000/return"); check("kembalikan id yang tidak ada -> 404", s == 404, f"HTTP {s}")
    s, d, _ = call("DELETE", f"/api/sql/books/{a}", auth=None)
    check("setelah dikembalikan, buku bisa dihapus -> 200", s == 200, f"HTTP {s}")
    row = next((r for r in all_loans() if r["id"] == loan["id"]), None)
    check("riwayat tetap ada dengan judul, book_id menjadi null", row is not None and row["book_title"] == "[UJI-PINJAM] Buku A" and row["book_id"] is None and row["status"] == "Dikembalikan")

    print("== Tanggal pinjam di masa depan ==")
    f = mkbook("[UJI-PINJAM] Buku F", 1)
    pause(); s, d, _ = call("POST", "/api/sql/loans", loan_body(f, loan_date=iso(3), due_date=iso(10)))
    fid = d["data"]["id"] if s == 201 else None
    pause(); s, d, _ = call("POST", f"/api/sql/loans/{fid}/return")
    check("kembalikan sebelum tanggal pinjam: tanggal aktual tidak lebih awal dari tanggal pinjam", s == 200 and d["data"]["returned_date"] == iso(3), d.get("data", {}).get("returned_date") if isinstance(d, dict) else d)

    print("== Balapan: eksemplar terakhir ==")
    time.sleep(2)
    c = mkbook("[UJI-PINJAM] Buku C (1 eksemplar)", 1)
    hasil = parallel(8, lambda i: call("POST", "/api/sql/loans", loan_body(c, borrower_name=f"Peminjam {i}"))[0])
    check("8 permintaan bersamaan untuk 1 eksemplar: tepat satu berhasil (201)", hasil.count(201) == 1, str(sorted(hasil)))
    check("sisanya ditolak 409 (bukan galat server)", hasil.count(409) == 7, str(sorted(hasil)))
    check("stok akhir 0, tidak negatif", stock_of(c) == 0, f"stok {stock_of(c)}")
    aktif = [r for r in all_loans() if r["book_id"] == c and r["status"] == "Dipinjam"]
    check("hanya satu pinjaman aktif untuk buku itu", len(aktif) == 1, f"{len(aktif)} aktif")

    print("== Balapan: pengembalian ganda ==")
    time.sleep(2)
    hasil = parallel(6, lambda i: call("POST", f"/api/sql/loans/{aktif[0]['id']}/return")[0])
    check("6 pengembalian bersamaan: tepat satu 200, sisanya 409", hasil.count(200) == 1 and hasil.count(409) == 5, str(sorted(hasil)))
    check("stok hanya bertambah satu kali (0 -> 1)", stock_of(c) == 1, f"stok {stock_of(c)}")

    print("== Balapan: pinjam saat buku dihapus ==")
    kontradiksi = 0
    for putaran in range(5):
        time.sleep(1.5)
        d_id = mkbook(f"[UJI-PINJAM] Buku D{putaran}", 3)
        hasil = parallel(2, lambda i: call("POST", "/api/sql/loans", loan_body(d_id))[0] if i == 0 else call("DELETE", f"/api/sql/books/{d_id}", auth=None)[0])
        pinjam, hapus = hasil
        if not ((pinjam == 201 and hapus == 409) or (pinjam == 404 and hapus == 200)):
            kontradiksi += 1
            print(f"    putaran {putaran}: pinjam={pinjam} hapus={hapus}")
    check("pinjam dan hapus bersamaan selalu konsisten (201+409 atau 404+200)", kontradiksi == 0, f"{kontradiksi} kontradiksi dari 5")
    yatim = [r for r in all_loans() if r["status"] == "Dipinjam" and r["book_id"] is None]
    check("tidak ada pinjaman aktif yang bukunya sudah terhapus", not yatim, f"{len(yatim)} yatim")

elif TAHAP == "failclosed":
    print("== Gagal tertutup: berkas login petugas tidak ada ==")
    for m, p, b in (("GET", "/api/sql/loans", None), ("POST", "/api/sql/loans", loan_body(1)), ("GET", "/api/loans", None)):
        pause(); s, d, _ = call(m, p, b, auth=GOOD)
        check(f"{m} {p} (dengan login) -> 503 pesan jelas, bukan data", s == 503 and isinstance(d, dict) and "belum dikonfigurasi" in d.get("error", "") and "data" not in d, f"HTTP {s}")
        pause(); s, d, _ = call(m, p, b, auth=None)
        check(f"{m} {p} (tanpa login) -> 401, bukan data", s == 401 and isinstance(d, dict) and "data" not in d, f"HTTP {s}")
    s, d, _ = call("GET", "/api/sql/books", auth=None); check("katalog publik tetap 200", s == 200, f"HTTP {s}")
    s, d, _ = call("GET", "/", auth=None); check("halaman utama tetap 200", s == 200, f"HTTP {s}")
else:
    sys.exit("TAHAP tidak dikenal")

p = sum(R)
print(f"\nRINGKASAN {TAHAP}: {p} PASS, {len(R) - p} FAIL dari {len(R)}")
sys.exit(0 if p == len(R) else 1)
