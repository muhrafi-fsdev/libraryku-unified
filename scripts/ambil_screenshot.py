"""Mengambil screenshot web LibraryKu untuk laporan dari aplikasi yang sedang berjalan.

Pemakaian: python3 scripts/ambil_screenshot.py [BASE_URL]
BASE_URL bawaan: https://libraryku-kali.tail342a2f.ts.net (alamat publik Tailscale Funnel).
Hasil: bukti/laporan/*.png dan bukti/laporan/ringkasan.txt

Aksi tulis (tambah, ubah, hapus) memakai buku uji yang dihapus lagi di akhir. Tanpa login (mode terbuka).
"""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from ffclient import FF

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://libraryku-kali.tail342a2f.ts.net").rstrip("/")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "bukti", "laporan")
os.makedirs(OUT, exist_ok=True)
log = []


def total(db):
    with urllib.request.urlopen(f"{BASE}/api/{db}/books", timeout=20) as r:
        return json.load(r)["total"]


def note(msg):
    print(msg); log.append(msg)


SET = """const cb=arguments[arguments.length-1]; const [id,v]=arguments; const el=document.getElementById(id);
el.value=v; el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); cb(1);"""
CLICK = "const cb=arguments[arguments.length-1]; const el=document.querySelector(arguments[0]); if(!el) throw new Error('tidak ada: '+arguments[0]); el.click(); cb(1);"
FIRSTID = "const cb=arguments[arguments.length-1]; const r=document.querySelector('#bookTable tr[data-id]'); cb(r?r.dataset.id:null);"


def shot(ff, name, full=False, wait=1.2):
    time.sleep(wait)
    ff.shot(os.path.join(OUT, name), full=full)
    note("ok  " + name)


def fresh(ff, route, mode="sql"):
    ff.go(f"{BASE}/?v={int(time.time())}#{route}")
    ff.js(f"sessionStorage.setItem('libraryku-mode','{mode}'); arguments[arguments.length-1](1)")
    ff.go(f"{BASE}/?v={int(time.time())}#{route}")
    time.sleep(2.5)


sql0, no0 = total("sql"), total("nosql")
note(f"alamat: {BASE}  | awal: SQL={sql0} NoSQL={no0}")
ff = FF()
try:
    ff.rect(1366, 900)
    # 1-3 halaman baca
    fresh(ff, "beranda"); shot(ff, "01-beranda.png")
    fresh(ff, "katalog"); shot(ff, "02-katalog-sql.png")
    # 4-9 CRUD PostgreSQL lewat UI
    fresh(ff, "dashboard"); shot(ff, "03-dashboard-sql.png")
    ff.js(CLICK, ["#newBtn"]); time.sleep(0.5)
    for i, v in [("title", "Cloud Computing Praktis"), ("author", "Kelompok Cloud"), ("category", "Teknologi"), ("year", "2025"), ("stock", "12")]:
        ff.js(SET, [i, v])
    shot(ff, "04-sql-dialog-tambah.png", wait=0.6)
    ff.js(CLICK, ["#submitBtn"]); time.sleep(2.2)
    shot(ff, "05-sql-sesudah-create.png")
    bid = ff.js(FIRSTID)
    ff.js(CLICK, [f'[data-edit-id="{bid}"]']); time.sleep(0.5)
    ff.js(SET, ["stock", "30"]); ff.js(SET, ["title", "Cloud Computing Praktis (Edisi Revisi)"])
    shot(ff, "06-sql-dialog-ubah.png", wait=0.6)
    ff.js(CLICK, ["#submitBtn"]); time.sleep(2.2)
    shot(ff, "07-sql-sesudah-update.png")
    ff.js(CLICK, [f'[data-delete-id="{bid}"]']); time.sleep(0.5)
    shot(ff, "08-sql-konfirmasi-hapus.png", wait=0.6)
    ff.js(CLICK, ["#confirmDelete"]); time.sleep(2.2)
    shot(ff, "09-sql-sesudah-delete.png")
    # 10-14 MongoDB: ganti mode lewat radio, buat dokumen, tampilkan JSON-nya, lalu hapus
    fresh(ff, "dashboard")
    ff.js(CLICK, ['input[name="dbmode-dash"][value="nosql"]']); time.sleep(2)
    shot(ff, "10-dashboard-nosql.png", wait=0.6)
    ff.js(CLICK, ["#newBtn"]); time.sleep(0.5)
    for i, v in [("title", "Sistem Terdistribusi dengan MongoDB"), ("author", "Kelompok Cloud"), ("category", "Teknologi"), ("year", "2025"), ("stock", "8")]:
        ff.js(SET, [i, v])
    shot(ff, "11-nosql-dialog-tambah.png", wait=0.6)
    ff.js(CLICK, ["#submitBtn"]); time.sleep(2.2)
    shot(ff, "12-nosql-sesudah-create.png")
    nid = ff.js(FIRSTID)
    note(f"id dokumen MongoDB: {nid}")
    ff.rect(1100, 520)
    ff.go(BASE + "/api/nosql/books"); shot(ff, "21-api-nosql-books.png", wait=1.0)
    ff.go(f"{BASE}/api/nosql/books/{nid}"); shot(ff, "25-api-nosql-book-by-id.png", wait=1.0)
    ff.rect(1366, 900)
    fresh(ff, "dashboard")
    ff.js(CLICK, ['input[name="dbmode-dash"][value="nosql"]']); time.sleep(2)
    ff.js(CLICK, [f'[data-delete-id="{nid}"]']); time.sleep(0.5)
    ff.js(CLICK, ["#confirmDelete"]); time.sleep(2.2)
    shot(ff, "13-nosql-sesudah-delete.png")
    # perbandingan dan tentang
    fresh(ff, "perbandingan"); time.sleep(2); ff.js(CLICK, ["#cmpMeasure"]); time.sleep(5)
    shot(ff, "15-perbandingan.png", full=True)
    fresh(ff, "tentang"); shot(ff, "16-tentang.png", full=True)
    # respons JSON di browser
    ff.rect(1100, 520)
    for name, path in [("20-api-sql-books.png", "/api/sql/books"),
                       ("22-api-sql-health.png", "/api/sql/health"), ("23-api-nosql-health.png", "/api/nosql/health")]:
        ff.go(BASE + path); shot(ff, name, wait=1.0)
    with urllib.request.urlopen(f"{BASE}/api/sql/books", timeout=20) as r:
        first = json.load(r)["data"][0]["id"]
    ff.go(f"{BASE}/api/sql/books/{first}"); shot(ff, "24-api-sql-book-by-id.png", wait=1.0)
    ff.rect(1366, 900)
    # tampilan ponsel
    ff.rect(450, 900)
    fresh(ff, "beranda"); shot(ff, "30-mobile-beranda.png")
    fresh(ff, "dashboard"); shot(ff, "31-mobile-dashboard.png")
finally:
    ff.close()

sql1, no1 = total("sql"), total("nosql")
note(f"akhir: SQL={sql1} NoSQL={no1}  | data kembali seperti awal: {sql0 == sql1 and no0 == no1}")
open(os.path.join(OUT, "ringkasan.txt"), "w").write("\n".join(log) + "\n")
