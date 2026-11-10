"""Membuat laporan/laporan.docx mengikuti urutan Laporan dan Dokumentasi pada PDF penugasan Project 1.

Pemakaian (butuh python-docx): ~/.venvs/libraryku-docs/bin/python scripts/buat_laporan.py
Gaya (font, judul, header, footer) diambil dari laporan/laporan.docx yang sudah ada; isi dibuat ulang.
Screenshot dibaca dari bukti/laporan/ (hasil scripts/ambil_screenshot.py) dan respons JSON dari
bukti/laporan/respons_json.json (hasil scripts/ambil_json.py). Tidak ada gambar atau JSON buatan tangan.
"""
import copy, json, os, shutil
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
B = lambda *p: os.path.join(ROOT, *p)
SHOT = B("bukti", "laporan")
OUT = B("laporan", "laporan.docx")
URL = "https://libraryku-kali.tail342a2f.ts.net"
REPO = "https://github.com/muhrafi-fsdev/libraryku-unified"

shutil.copy(OUT, B("laporan", "laporan.docx.bak")) if os.path.exists(OUT) else None
doc = Document(OUT)
body = doc.element.body
for el in list(body):
    if el.tag != qn("w:sectPr"):
        body.remove(el)

# ---------- pembantu ----------
def run_fmt(r, size=None, bold=None, italic=None, color=None, font=None):
    if size: r.font.size = Pt(size)
    if bold is not None: r.bold = bold
    if italic is not None: r.italic = italic
    if color: r.font.color.rgb = RGBColor.from_string(color)
    if font:
        r.font.name = font
        r._element.rPr.rFonts.set(qn("w:eastAsia"), font)

def para(text="", style=None, align=None, size=None, bold=None, italic=None, color=None, after=None, before=None, keep=False):
    p = doc.add_paragraph(style=style)
    if text:
        add_runs(p, text, size, bold, italic, color)
    if align: p.alignment = align
    if after is not None: p.paragraph_format.space_after = Pt(after)
    if before is not None: p.paragraph_format.space_before = Pt(before)
    if keep: p.paragraph_format.keep_with_next = True
    return p

def add_runs(p, text, size=None, bold=None, italic=None, color=None):
    """Teks dengan **tebal** dan `kode` sederhana."""
    import re
    for tok in re.split(r"(\*\*.+?\*\*|`[^`]+`)", text):
        if not tok: continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            r = p.add_run(tok[2:-2]); run_fmt(r, size, True, italic, color)
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
            r = p.add_run(tok[1:-1]); run_fmt(r, (size or 10) - 0.5, bold, italic, "1B3B38", font="Consolas")
        else:
            r = p.add_run(tok); run_fmt(r, size, bold, italic, color)

def h1(t): return doc.add_heading(t, level=1)
def h2(t): return doc.add_heading(t, level=2)
def bullet(t):
    p = doc.add_paragraph(style="List Bullet"); add_runs(p, t); return p
def numbered(items):
    for i, t in enumerate(items, 1):
        p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.7); p.paragraph_format.first_line_indent = Cm(-0.7)
        p.paragraph_format.space_after = Pt(3)
        add_runs(p, f"{i}.  " + t)

def code(text, size=8):
    lines = text.rstrip("\n").split("\n")
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    shade(c, "F1F5F4"); borders(t, "B9C8C5")
    c.paragraphs[0].text = ""
    for i, ln in enumerate(lines):
        p = c.paragraphs[0] if i == 0 else c.add_paragraph()
        p.paragraph_format.space_after = Pt(0); p.paragraph_format.space_before = Pt(0)
        r = p.add_run(ln if ln else " "); run_fmt(r, size, font="Consolas", color="1B3B38")
    para("", after=2)

def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:shd")): tcPr.remove(old)
    s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), hexcolor); tcPr.append(s)

def borders(table, color="9FB1AE"):
    tblPr = table._tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")): tblPr.remove(old)
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color); b.append(e)
    tblPr.append(b)

def cell_margins(table, cm=0.12):
    tblPr = table._tbl.tblPr
    m = OxmlElement("w:tblCellMar")
    for edge in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:w"), str(int(cm * 567))); e.set(qn("w:type"), "dxa"); m.append(e)
    tblPr.append(m)

def table(header, rows, widths, size=9, mono_cols=(), head_fill="D8E8E5"):
    t = doc.add_table(rows=1, cols=len(header)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False; borders(t); cell_margins(t)
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; shade(c, head_fill); c.text = ""
        r = c.paragraphs[0].add_run(h); run_fmt(r, size, True)
    tr = t.rows[0]._tr; trPr = tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            if i in mono_cols:
                r = p.add_run(str(v)); run_fmt(r, size - 0.5, font="Consolas")
            else:
                add_runs(p, str(v), size)
        trPr = t.rows[-1]._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); trPr.append(cs)
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    para("", after=4)
    return t

def caption(text):
    p = para(text, size=9, italic=True, color="4A5F68", after=8, align=WD_ALIGN_PARAGRAPH.CENTER)
    return p

def figure(fname, cap, width=15.5):
    path = os.path.join(SHOT, fname) if not os.path.isabs(fname) else fname
    if not os.path.exists(path): raise SystemExit("gambar tidak ada: " + path)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(path, width=Cm(width))
    caption(cap)

def figure_pair(f1, f2, cap, width=6.2):
    t = doc.add_table(rows=1, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, f in enumerate((f1, f2)):
        c = t.rows[0].cells[i]; c.text = ""
        pp = c.paragraphs[0]; pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pp.add_run().add_picture(os.path.join(SHOT, f), width=Cm(width))
    caption(cap)

def pagebreak():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ---------- data JSON nyata ----------
J = {(r["label"]): r for r in json.load(open(os.path.join(SHOT, "respons_json.json")))}
def js(label, compact=True):
    r = J[label]
    return json.dumps(r["body"], ensure_ascii=False, separators=(",", ":"), sort_keys=True) if compact else json.dumps(r["body"], ensure_ascii=False, indent=2, sort_keys=True)
def st(label): return str(J[label]["status"])

# ======================= SAMPUL =======================
para("LAPORAN PROJECT 1", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, color="0B6465", before=60, after=4)
para("LibraryKu", align=WD_ALIGN_PARAGRAPH.CENTER, size=34, bold=True, color="192D3A", after=2)
para("Sistem Pengelolaan Buku Perpustakaan", align=WD_ALIGN_PARAGRAPH.CENTER, size=15, after=2)
para("Flask, PostgreSQL, MongoDB, dan Docker Compose", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, color="4A5F68", after=24)
table(["Komponen", "Pilihan kasus"], [
    ["Nomor kasus", "15 (baris No. 15 pada tabel pembagian kasus di PDF penugasan)"],
    ["Domain", "Perpustakaan"], ["Platform", "Microservices (Docker)"], ["Jenis database", "SQL (PostgreSQL); mode NoSQL (MongoDB) sebagai pengembangan tambahan"],
    ["Mata kuliah", "Cloud Computing"]], [4.5, 11.5], size=10)
para("Disusun oleh", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, color="4A5F68", before=20, after=2)
para("Muhammad Rafi Priyo Sembodo", align=WD_ALIGN_PARAGRAPH.CENTER, size=15, bold=True, after=0)
para("NIM 101072300038  |  Kelas S1TT-KJ-23-04", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, after=8)
para("Anggota kelompok: Atilla Pramudya Nugroho (101072300039), Muhammad Aprilio Rizal Arifin (101072300040), Aji Eka Saputra (101072300071)", align=WD_ALIGN_PARAGRAPH.CENTER, size=10, after=14)
para(f"Kode sumber: {REPO}", align=WD_ALIGN_PARAGRAPH.CENTER, size=10, after=2)
para(f"Website (HTTPS publik): {URL}/", align=WD_ALIGN_PARAGRAPH.CENTER, size=10, after=18)
para("TELKOM UNIVERSITY  |  2026", align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, color="4A5F68")
pagebreak()

para("Urutan bab mengikuti bagian Laporan dan Dokumentasi pada PDF penugasan: (1) Identitas, (2) Deskripsi proyek, (3) Langkah deployment, (4) Endpoint API dan contoh respons JSON, (5) Analisis teknis, (6) Masalah dan solusi. Bab 7 memuat verifikasi dan testing (bagian D PDF) dan bab 8 demonstrasi (bagian E PDF). Semua screenshot diambil dari website yang sedang berjalan lewat alamat HTTPS publik; JSON adalah respons nyata dari alamat yang sama.", italic=True, size=10, color="4A5F68", after=6)

table(["Kebutuhan pada PDF penugasan", "Bab di laporan ini"], [
    ["Laporan 1. Identitas: nama, NIM, kelas, kategori", "Bab 1"],
    ["Laporan 2. Deskripsi proyek: ringkasan aplikasi dan framework", "Bab 2"],
    ["Laporan 3. Langkah deployment: perintah CLI atau screenshot konfigurasi", "Bab 3"],
    ["Laporan 4. Endpoint API: URL dan contoh respons JSON", "Bab 4"],
    ["Laporan 5. Analisis teknis: VM/container, network, storage, API", "Bab 5"],
    ["Laporan 6. Masalah dan solusi", "Bab 6"],
    ["D.1 Aplikasi dapat diakses lewat alamat public", "Bab 7.1"],
    ["D.2 Uji API lewat browser atau Postman; D.3 tampilkan respons JSON", "Bab 4 dan 7.2"],
    ["E. Demonstrasi: website berjalan, endpoint API, arsitektur dan deployment flow", "Bab 8"]], [11, 5], size=9)

# ======================= 1. IDENTITAS =======================
h1("1. Identitas")
table(["Komponen", "Isi"], [
    ["Nama", "Muhammad Rafi Priyo Sembodo"], ["NIM", "101072300038"], ["Kelas", "S1TT-KJ-23-04"],
    ["Mata kuliah", "Cloud Computing (Project 1)"],
    ["Kategori yang didapat", "Domain **Perpustakaan**, platform **Microservices (Docker)**, database **SQL (PostgreSQL)**"],
    ["Nomor kasus", "**15** pada tabel pembagian kasus di PDF (Perpustakaan, Microservices (Docker), SQL). Nomor kelompok resmi perlu dikonfirmasi ke dosen. Mode NoSQL (MongoDB, setara No. 16) adalah pengembangan tambahan dalam aplikasi yang sama dan tidak dihitung sebagai tugas kedua."],
    ["Repositori kode", REPO]], [4.2, 11.8], size=10)
table(["Anggota kelompok", "NIM"], [
    ["Muhammad Rafi Priyo Sembodo (penyusun)", "101072300038"], ["Atilla Pramudya Nugroho", "101072300039"],
    ["Muhammad Aprilio Rizal Arifin", "101072300040"], ["Aji Eka Saputra", "101072300071"]], [11, 5], size=10)

# ======================= 2. DESKRIPSI =======================
h1("2. Deskripsi Proyek")
para("LibraryKu adalah website katalog perpustakaan kampus. Pengunjung melihat ringkasan koleksi, mencari buku berdasarkan judul atau penulis, dan menyaring berdasarkan kategori. Pengelolaan data buku (tambah, ubah, hapus) dipusatkan di halaman Dashboard. Data disimpan di database dan dilayani lewat REST API Flask. Aplikasi berjalan sebagai beberapa container Docker yang dihubungkan Docker Compose, di VM Kali Linux (VirtualBox), dan dapat dibuka dari internet lewat alamat HTTPS publik.")
para("Data dapat disimpan di dua database terpisah yang dipilih pengguna lewat tombol **SQL / NoSQL** di Katalog dan Dashboard: **PostgreSQL** (kasus No. 15) dan **MongoDB** (tambahan). Keduanya memakai kontrak JSON yang sama, sehingga satu antarmuka melayani dua database.")
h2("2.1 Framework dan teknologi")
table(["Lapisan", "Teknologi", "Peran"], [
    ["Frontend", "HTML, CSS, dan JavaScript biasa, disajikan Nginx 1.28", "Antarmuka web; memanggil API dengan fetch; juga menjadi gerbang (reverse proxy) ke backend"],
    ["Backend SQL", "Flask (Python 3.12) + gunicorn + psycopg2", "REST API /api/sql/*, validasi, perintah SQL terparameter"],
    ["Database SQL", "PostgreSQL 16", "Tabel books dengan constraint CHECK; volume postgres_data"],
    ["Backend NoSQL", "Flask + gunicorn + PyMongo", "REST API /api/nosql/*, validasi, ID ObjectId"],
    ["Database NoSQL", "MongoDB 7.0", "Koleksi dokumen buku; volume mongo_data; pengguna aplikasi hak terbatas"],
    ["Orkestrasi", "Docker Compose", "Lima service, dua network bridge, dua volume"],
    ["Akses publik", "Tailscale Funnel", "Alamat HTTPS publik tanpa port forwarding dan tanpa domain"]], [3, 6.2, 6.8], size=9)
h2("2.2 Fitur CRUD")
table(["Operasi", "Aktivitas di website", "Permintaan API (contoh SQL)", "Status HTTP"], [
    ["Create", "Dashboard: Tambah buku, isi formulir, Simpan", "POST /api/sql/books", "201; 400 bila tidak valid"],
    ["Read", "Beranda, Katalog (cari dan filter), tabel Dashboard", "GET /api/sql/books, GET /api/sql/books/{id}", "200; 404 bila id tidak ada"],
    ["Update", "Dashboard: Edit, ubah, Simpan perubahan", "PUT /api/sql/books/{id}", "200; 400; 404"],
    ["Delete", "Dashboard: Hapus, konfirmasi di dialog", "DELETE /api/sql/books/{id}", "200; 404"]], [2, 5.2, 5.6, 3.2], size=9)
para("Website tidak memakai nama pengguna dan kata sandi: pengunjung langsung dapat membaca dan mengelola data. Penulisan tetap dilindungi header `X-Requested-With` (perlindungan CSRF), pembatasan laju, batas ukuran badan 16 KB, dan validasi di backend. Karena alamat publik dapat dibuka siapa saja, siapa pun yang tahu alamatnya dapat mengubah data; karena itu halaman Dashboard menampilkan peringatan dan data yang dimasukkan sebaiknya hanya data contoh (bab 3.6).")
h2("2.3 Tampilan website")
para(f"Gambar berikut diambil dari website yang berjalan, lewat alamat {URL}.", size=10, color="4A5F68")
figure("01-beranda.png", "Gambar 2.1  Beranda: rak buku dibuat dari tiga buku terbaru di database; status 'PostgreSQL terhubung' di pojok kanan atas.")
figure("02-katalog-sql.png", "Gambar 2.2  Katalog (mode SQL): pencarian, filter kategori, dan pemilih database SQL/NoSQL. Halaman ini hanya untuk melihat data.")
figure("03-dashboard-sql.png", "Gambar 2.3  Dashboard (mode SQL): tabel buku dengan tombol Edit dan Hapus, tombol Tambah buku, dan ringkasan jumlah judul, eksemplar, kategori.")
figure("15-perbandingan.png", "Gambar 2.4  Halaman Perbandingan: data nyata dari PostgreSQL dan MongoDB, tabel perbedaan, dan hasil ukur waktu respons dari browser.", width=10.5)
figure("16-tentang.png", "Gambar 2.5  Halaman Tentang: tujuan, teknologi, arsitektur, peran Docker Compose, dan tautan untuk mencoba API.", width=10.5)
figure_pair("30-mobile-beranda.png", "31-mobile-dashboard.png", "Gambar 2.6  Tampilan di layar sempit (lebar 450 piksel): Beranda dan Dashboard menyesuaikan lebar layar.")

# ======================= 3. DEPLOYMENT =======================
h1("3. Langkah Deployment")
para("Aplikasi dijalankan secara lokal di VM Kali Linux (VirtualBox) dengan Docker Compose, sesuai ketentuan bagian C.2 PDF (platform Docker: konfigurasi network Docker atau Docker Compose agar antar service saling berkomunikasi). Tidak ada deployment ke layanan cloud; alamat publik dibuat dengan Tailscale Funnel yang meneruskan ke aplikasi lokal (3.5).")
h2("3.1 Persiapan")
bullet("VM Kali Linux dengan Docker Engine dan Docker Compose v2 (periksa: `sudo docker --version` dan `sudo docker compose version`).")
bullet("Kode proyek di VM, misalnya `~/LibraryKu_UIUX/LibraryKu_Project1`, diperoleh dengan `git clone` dari repositori GitHub.")
bullet("Python 3 hanya untuk skrip uji; aplikasi sendiri berjalan di dalam container.")
h2("3.2 Struktur proyek")
code("""LibraryKu_Project1/
  compose.yaml            definisi lima service, dua network, dua volume
  .env.example            contoh variabel (kata sandi database); salin menjadi .env
  backend/                Flask SQL: app.py, validation.py, Dockerfile, requirements.txt
  backend_nosql/          Flask NoSQL: app.py, validation.py, ids.py, Dockerfile
  database/init.sql       skema PostgreSQL (dijalankan sekali saat volume baru)
  mongodb/init-app-user.js  membuat pengguna aplikasi MongoDB (hak terbatas)
  nginx/default.conf      router, reverse proxy, CSRF, rate limit
  frontend/               index.html, app.js, style.css
  scripts/                ctl.sh, funnel.sh, uji.sh, test_*.py, ambil_screenshot.py
  tests/  docs/  bukti/  laporan/""", size=8.5)
h2("3.3 Konfigurasi (cuplikan dari berkas asli)")
para("**compose.yaml** menghubungkan service lewat network dan menyimpan data di volume. Hanya `frontend` yang memiliki `ports`.", after=3)
code("""services:
  database:                      # PostgreSQL 16
    image: postgres:16-alpine
    volumes: [postgres_data:/var/lib/postgresql/data, ./database/init.sql:/docker-entrypoint-initdb.d/01-init.sql:ro]
    networks: [app_network]
  backend:                       # Flask SQL, dibangun dari backend/Dockerfile
    build: ./backend
    environment: {DB_HOST: database, DB_PORT: "5432", DB_NAME: libraryku}
    depends_on: {database: {condition: service_healthy}}
    expose: ["5000"]
    networks: [app_network]
  frontend:                      # Nginx: satu-satunya port ke host
    image: nginx:1.28-alpine
    ports: ["${FRONTEND_BIND:-127.0.0.1}:8081:80"]
    volumes: [./frontend:/usr/share/nginx/html:ro, ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro]
    networks: [app_network]
  mongodb:                       # MongoDB 7.0, hanya di network internal
    image: mongo:7.0.45
    volumes: [mongo_data:/data/db]
    networks: [nosql_network]
  backend-nosql:                 # Flask NoSQL, terhubung ke kedua network
    build: ./backend_nosql
    environment: {MONGO_HOST: mongodb, MONGO_PORT: "27017"}
    networks: [app_network, nosql_network]
networks:
  app_network:   {driver: bridge}
  nosql_network: {driver: bridge, internal: true}
volumes: {postgres_data: {}, mongo_data: {}}""", size=7.5)
para("**backend/Dockerfile** (backend NoSQL serupa):", after=3)
code("""FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]""", size=8)
para("**nginx/default.conf** meneruskan alamat API ke backend yang sesuai (cuplikan):", after=3)
code("""location /api/sql/   { rewrite ^/api/sql/(.*)$ /api/$1 break; proxy_pass $sql_upstream; }     # -> Flask SQL -> PostgreSQL
location /api/nosql/ { proxy_pass $nosql_upstream; }                                            # -> Flask NoSQL -> MongoDB
location /api/       { proxy_pass $legacy_upstream; }                                           # alamat lama -> Flask SQL
location /           { try_files $uri /index.html; }                                            # file statis frontend""", size=8)
h2("3.4 Langkah menjalankan (perintah CLI)")
numbered([
    "Masuk ke folder proyek lalu buat berkas rahasia dari contoh. Isi kata sandi dengan nilai acak; berkas ini tidak masuk repositori.",
    "Bangun image dan jalankan semua container, lalu periksa status.",
    "Buka website di browser VM: http://127.0.0.1:8081.",
    "Verifikasi dengan skrip yang disertakan (hasil tersimpan di folder bukti/)."])
code("""# 1
cd ~/LibraryKu_UIUX/LibraryKu_Project1
cp .env.example .env && nano .env
# 2
sudo docker compose up -d --build
sudo docker compose ps
# 4
./scripts/ctl.sh verify       # baca isi PostgreSQL dan MongoDB langsung
./scripts/ctl.sh security     # periksa port dan pengaturan container
python3 scripts/test_api.py   # pemeriksaan CRUD SQL dan NoSQL""", size=8.5)
table(["Perintah", "Fungsi dan alasan"], [
    ["cp .env.example .env", "Membuat berkas variabel berisi kata sandi database. Dipisah dari kode supaya rahasia tidak masuk repositori."],
    ["docker compose up -d --build", "Membangun image backend dari Dockerfile, mengunduh image Nginx/PostgreSQL/MongoDB, membuat network dan volume, lalu menjalankan semua service sesuai urutan `depends_on` (database sehat dulu, baru backend, baru Nginx)."],
    ["docker compose ps", "Memeriksa status container dan health check; hanya frontend yang menampilkan pemetaan port ke host."],
    ["./scripts/ctl.sh verify", "Membaca isi tabel PostgreSQL dan koleksi MongoDB langsung dari container, membuktikan data benar-benar tersimpan di database."],
    ["./scripts/ctl.sh security", "Memeriksa port yang dibuka, pengguna container, batas resource, dan pengaturan keamanan."],
    ["python3 scripts/test_api.py", "Menjalankan operasi CRUD lewat API pada kedua database dan memeriksa status HTTP serta bentuk JSON."]], [5.5, 10.5], size=8.5)
para("Hasil `docker compose ps` pada VM Kali (lima container; database dan backend berstatus healthy; hanya frontend yang memetakan port ke host). Kolom dipersingkat. Teks asli: `bukti/unified/ctl_restart-all_20261110_181951.txt`.", size=9.5, after=3)
code("""SERVICE         IMAGE                              STATUS                    PORTS
backend         libraryku-project1-backend         Up 9 seconds (healthy)    5000/tcp
backend-nosql   libraryku-project1-backend-nosql   Up 9 seconds (healthy)    5000/tcp
database        postgres:16-alpine                 Up 15 seconds (healthy)   5432/tcp
frontend        nginx:1.28-alpine                  Up 4 seconds              0.0.0.0:8081->80/tcp
mongodb         mongo:7.0.45                       Up 15 seconds (healthy)""", size=8)
para("Pada pengambilan teks tersebut port frontend masih `0.0.0.0:8081`. Sesudah pengamanan akses publik, port diikat ke `127.0.0.1:8081` (variabel `FRONTEND_BIND`), terbukti pada `bukti/unified/ctl_apply-frontend_20261110_190122.txt`: `frontend ... 127.0.0.1:8081->80/tcp`. Port 5000 (Flask), 5432 (PostgreSQL), dan 27017 (MongoDB) tidak dipublikasikan ke host.", size=9.5)
para("Peringatan: jangan menjalankan `docker compose down -v`; opsi `-v` menghapus volume dan seluruh data buku.", bold=True, size=10)
h2("3.5 Akses lewat alamat publik (Tailscale Funnel)")
para("PDF bagian D.1 meminta aplikasi dapat diakses melalui alamat public. Karena belum ada domain untuk Cloudflare Tunnel, alamat publik dibuat dengan Tailscale Funnel: Tailscale di VM Kali membuat sambungan keluar ke relay Tailscale, sehingga tidak perlu port forwarding VirtualBox, tidak perlu membuka port router, dan tidak mengubah Windows Firewall. Sertifikat HTTPS diterbitkan otomatis (Let's Encrypt).")
code("""./scripts/funnel.sh install    # pasang Tailscale (skrip instalasi resmi, diunduh dulu ke berkas)
./scripts/funnel.sh login      # masuk akun Tailscale (buka URL persetujuan perangkat)
./scripts/funnel.sh enable     # aktifkan Funnel ke 127.0.0.1:8081
                               # (menolak bila perlindungan CSRF belum aktif)
./scripts/funnel.sh status
./scripts/funnel.sh off        # mematikan akses publik; website lokal tetap jalan""", size=8.5)
para("Hasil perintah enable (`bukti/publik/funnel_enable_20261110_191513.txt`):", size=9.5, after=3)
code(f"""Available on the internet:
{URL}/
|-- proxy http://127.0.0.1:8081
Funnel started and running in the background.""", size=8.5)
h2("3.6 Catatan konfigurasi network dan keamanan")
bullet("**NAT VirtualBox** dan port forwarding (bagian C.1 PDF) berlaku untuk platform VM Monolithic. Karena kasus ini memakai Docker, konfigurasi yang relevan adalah network Docker Compose (3.3) dan, untuk akses dari luar, Funnel (3.5).")
bullet("**Mode terbuka (tanpa login).** Atas keputusan pemilik proyek, penulisan data tidak memakai nama pengguna dan kata sandi. Perlindungan yang tetap aktif: header `X-Requested-With` wajib untuk POST, PUT, DELETE (perlindungan CSRF); pembatasan laju 10 permintaan per detik (burst 20); batas badan 16 KB; validasi di backend; header keamanan (HSTS, CSP, nosniff, X-Frame-Options). Risiko yang diterima: siapa pun yang tahu alamat publik dapat menambah atau menghapus buku. Login dapat diaktifkan lagi dengan mengubah satu baris di `nginx/default.conf` (lihat `docs/publik/arsitektur.md`).")
bullet("Funnel berjalan di VM; website hanya online selama komputer dan VM menyala dan Funnel aktif. Setelah reboot, Docker menaikkan container sendiri (`restart: unless-stopped`); status Funnel diperiksa dengan `./scripts/funnel.sh status`.")

# ======================= 4. ENDPOINT API =======================
h1("4. Endpoint API dan Contoh Respons JSON")
para(f"Alamat dasar publik: {URL} (lokal: http://127.0.0.1:8081). Semua endpoint melayani dan menerima JSON. Pilihan database ada di awalan alamat: `/api/sql/...` untuk PostgreSQL dan `/api/nosql/...` untuk MongoDB. Alamat lama `/api/books` tetap diarahkan ke PostgreSQL.")
table(["Metode", "Alamat", "Fungsi", "Status HTTP"], [
    ["GET", "/api/{sql|nosql}/health", "Cek API dan koneksi database", "200; 503 bila database tidak terjangkau"],
    ["GET", "/api/{sql|nosql}/books", "Daftar buku (terbaru di atas)", "200"],
    ["GET", "/api/{sql|nosql}/books/{id}", "Satu buku", "200; 404"],
    ["POST", "/api/{sql|nosql}/books", "Tambah buku (Create)", "201; 400 data tidak valid; 403 tanpa header aplikasi; 413; 429"],
    ["PUT", "/api/{sql|nosql}/books/{id}", "Ubah buku (Update)", "200; 400; 403; 404; 429"],
    ["DELETE", "/api/{sql|nosql}/books/{id}", "Hapus buku (Delete)", "200; 403; 404; 429"]], [1.8, 5.2, 4.4, 4.6], size=8.5, mono_cols=(1,))
para("Badan POST dan PUT memuat `title` (maks. 150 karakter), `author` (maks. 100), `category` (maks. 60), `year` (1900 sampai tahun berjalan + 1), dan `stock` (0 sampai 1.000.000). Perbedaan kedua database hanya pada `id`: bilangan bulat di SQL, ObjectId (string 24 karakter heksadesimal) di NoSQL. Status 403 berarti header `X-Requested-With: libraryku` tidak ada pada permintaan tulis (website mengirimnya otomatis; pada curl atau Postman tambahkan sendiri), 413 berarti badan lebih dari 16 KB, dan 429 berarti terlalu banyak permintaan. Semua galat, termasuk alamat yang tidak ada (404) dan metode yang salah (405), dibalas dalam format JSON dengan kunci `error`.", size=10)
para(f"**Contoh respons JSON aktual.** Respons berikut diambil dengan `python3 scripts/ambil_json.py` dari {URL} (lewat internet). Tanpa login. Buku uji 'Cloud Computing Praktis' dibuat lalu dihapus; jumlah buku kembali seperti sebelum pengambilan. Respons daftar buku dipersingkat menjadi dua buku pertama agar tabel terbaca (tanda `...` menandai bagian yang dibuang). Berkas: `bukti/laporan/respons_json.txt`.", size=10)

def json_table(nama, db):
    rows = [
        (f"GET /api/{db}/health", f"{nama}: health"),
        (f"GET /api/{db}/books", f"{nama}: daftar buku"),
        (f"POST /api/{db}/books (data valid)", f"{nama}: tambah buku (valid)"),
        (f"GET /api/{db}/books/{{id}}", f"{nama}: ambil satu buku"),
        (f"PUT /api/{db}/books/{{id}}", f"{nama}: ubah buku"),
        (f"POST /api/{db}/books (data tidak valid)", f"{nama}: tambah buku (data tidak valid)"),
        (f"POST /api/{db}/books (tanpa header aplikasi)", f"{nama}: tulis tanpa header aplikasi"),
        (f"DELETE /api/{db}/books/{{id}}", f"{nama}: hapus buku"),
        (f"GET /api/{db}/books/{{id}} (sudah dihapus)", f"{nama}: ambil buku yang sudah dihapus")]
    def tampil(k):
        r = J[k]["body"]
        if isinstance(r, dict) and isinstance(r.get("data"), list) and len(r["data"]) > 2:
            n = r.get("total", len(r["data"]))
            return json.dumps({"data": r["data"][:2], "total": n}, ensure_ascii=False, separators=(",", ":"), sort_keys=True).replace("}],", "},...],", 1)
        return js(k)
    table(["Permintaan", "Status", "Respons JSON"], [[a, st(k), tampil(k)] for a, k in rows], [4.6, 1.3, 10.1], size=8, mono_cols=(2,))

h2("4.1 PostgreSQL (SQL)")
json_table("PostgreSQL", "sql")
h2("4.2 MongoDB (NoSQL)")
json_table("MongoDB", "nosql")
h2("4.3 Respons JSON di browser")
para("PDF bagian D.2 meminta uji API lewat browser atau Postman. GET dibuka langsung di Firefox pada alamat publik; penampil JSON bawaan Firefox menampilkan strukturnya.", size=10)
figure("20-api-sql-books.png", f"Gambar 4.1  {URL}/api/sql/books: daftar buku PostgreSQL; id berupa angka; `total` sama dengan jumlah buku.", width=14)
figure("24-api-sql-book-by-id.png", f"Gambar 4.2  /api/sql/books/{{id}}: satu buku.", width=14)
figure("22-api-sql-health.png", f"Gambar 4.3  /api/sql/health: API dan PostgreSQL terhubung.", width=14)
figure("23-api-nosql-health.png", f"Gambar 4.4  /api/nosql/health: API dan MongoDB terhubung.", width=14)
figure("21-api-nosql-books.png", f"Gambar 4.5  /api/nosql/books: dokumen MongoDB; id berupa ObjectId (string 24 karakter).", width=14)
figure("25-api-nosql-book-by-id.png", f"Gambar 4.6  /api/nosql/books/{{id}}: satu dokumen MongoDB.", width=14)

# ======================= 5. ANALISIS =======================
h1("5. Analisis Teknis")
para("Bab ini menjelaskan hubungan antara konsep VM/container, network, storage, dan API pada LibraryKu (bagian Laporan 5 PDF).")
figure(B("laporan", "diagram.png"), "Gambar 5.1  Arsitektur LibraryKu di VM Kali Linux. Diagram dibuat dari compose.yaml dan nginx/default.conf (bukan tangkapan layar).", width=16)
h2("5.1 VM dan container")
para("VirtualBox (hypervisor) menjalankan VM Kali Linux yang memiliki kernel dan sistem operasi sendiri, terpisah dari Windows. Di dalam VM, Docker Engine menjalankan lima container yang berbagi kernel VM. Setiap container hanya membawa proses dan pustaka yang dibutuhkan, sehingga lebih ringan dan lebih cepat dinyalakan daripada lima VM terpisah. Container bersifat sementara: data penting tidak disimpan di dalam container, melainkan di volume.")
h2("5.2 Network")
bullet("**Lapis 1, NAT VirtualBox.** VM dapat keluar ke internet, tetapi host tidak dapat masuk ke VM tanpa port forwarding. Tidak ada aturan forwarding; akses dari luar memakai Tailscale Funnel yang membuat sambungan keluar.")
bullet("**Lapis 2, `app_network` (bridge).** Frontend, backend SQL, PostgreSQL, dan backend NoSQL berada di satu network dan saling menemukan lewat nama service (DNS Docker): Flask menghubungi `database:5432`; Nginx meneruskan `/api/sql/*` ke `backend:5000` dan `/api/nosql/*` ke `backend-nosql:5000`.")
bullet("**`nosql_network` (bridge, internal).** Hanya MongoDB dan backend NoSQL; karena `internal: true`, MongoDB tidak punya jalur masuk maupun keluar ke host.")
bullet("**Port.** Hanya Nginx yang dipublikasikan ke host (`127.0.0.1:8081` ke port 80 container). Port 5000, 5432, dan 27017 tidak dapat dijangkau dari luar network Docker.")
h2("5.3 Storage")
bullet("Data PostgreSQL berada di volume `postgres_data`; data MongoDB di volume `mongo_data`. `database/init.sql` dijalankan hanya saat volume PostgreSQL baru dibuat.")
bullet("`docker compose down` tanpa `-v` menghapus container dan network, tetapi kedua volume tetap ada. Terbukti pada uji restart: data sebelum dan sesudah sama (`bukti/unified/ctl_restart-all_20261110_181951.txt`).")
bullet("Folder `frontend`, dan `nginx/default.conf` dipasang sebagai bind mount read-only; perubahan tampilan tidak memerlukan build ulang image.")
h2("5.4 API")
bullet("REST: metode HTTP dan URL menentukan operasi; badan dan respons berupa JSON; status HTTP menyatakan hasil (200, 201, 400, 401, 403, 404, 429, 503).")
bullet("Data divalidasi di backend (`validation.py`) dan di browser. SQL memakai parameter (`%s`) sehingga tidak rentan injeksi SQL; di MongoDB ID divalidasi 24 heksadesimal dan nilai pengguna tidak dipakai sebagai operator query. Frontend menulis ke halaman dengan `textContent`, sehingga teks buku tidak ditafsirkan sebagai HTML.")
bullet("Nginx berperan sebagai API gateway: satu alamat untuk semua, memilih backend berdasarkan awalan, menegakkan header CSRF dan pembatasan laju untuk operasi tulis, dan membalas 503 JSON bila backend mati tanpa ikut mati.")
h2("5.5 Alur satu permintaan (Create)")
numbered([
    "Pengguna menekan Simpan buku; JavaScript mengirim `POST /api/sql/books` (dengan header `X-Requested-With`) lewat HTTPS ke alamat publik.",
    "Relay Tailscale meneruskan lewat tunel terenkripsi ke tailscaled di Kali, yang mengakhiri TLS dan meneruskan HTTP ke `127.0.0.1:8081`.",
    "Docker memetakan port 8081 VM ke port 80 container Nginx. Nginx memeriksa header CSRF dan membatasi laju, lalu mengubah alamat menjadi `/api/books` dan meneruskan ke `backend:5000`.",
    "Flask memvalidasi data, lalu menjalankan `INSERT ... RETURNING` ke `database:5432`.",
    "PostgreSQL menyimpan baris di volume `postgres_data`.",
    "Flask membalas HTTP 201 dan JSON; website menampilkan buku baru dan memperbarui ringkasan koleksi."])
h2("5.6 SQL dan NoSQL pada aplikasi ini")
table(["Aspek", "SQL: PostgreSQL 16", "NoSQL: MongoDB 7.0"], [
    ["Model data", "Tabel, baris, kolom", "Dokumen JSON (BSON) dalam koleksi"],
    ["Skema", "Tetap; tipe kolom dan CHECK di init.sql", "Fleksibel; aplikasi memvalidasi bentuk dokumen"],
    ["Identitas", "id integer otomatis", "_id ObjectId (string 24 karakter di API)"],
    ["Tambah", "INSERT INTO books (...) VALUES (...)", "insert_one({...})"],
    ["Ubah", "UPDATE books SET ... WHERE id = %s", "find_one_and_update({\"_id\": ...}, {\"$set\": {...}})"],
    ["Hapus", "DELETE FROM books WHERE id = %s", "delete_one({\"_id\": ObjectId(id)})"],
    ["Penyimpanan", "Volume postgres_data", "Volume mongo_data"]], [3, 6.5, 6.5], size=9)
para("Desain ini adalah sistem berlapis dengan beberapa container (gateway, dua backend, dua database). Dua backend API tidak otomatis berarti ada banyak microservice bisnis yang independen, tetapi implementasi sesuai fokus praktikum: pemisahan service di Docker, networking, storage, dan API.", size=10)

h2("5.7 Hubungan antara VM/container, network, storage, dan API")
para("PDF meminta analisis hubungan keempat konsep. Pada LibraryKu keempatnya saling bergantung: container menjalankan program, network menghubungkan program itu, storage menyimpan hasilnya, dan API adalah bahasa yang dipakai browser untuk meminta semuanya.", size=10)
table(["Konsep", "Peran di LibraryKu", "Terhubung ke", "Akibat bila dilepas"], [
    ["VM dan container", "VM Kali menjalankan Docker; lima container (Nginx, 2 Flask, PostgreSQL, MongoDB) berbagi kernel VM", "Network: tiap container diberi alamat dan nama service. Storage: container memasang volume ke dalam dirinya", "Container dihapus lalu dibuat ulang tanpa kehilangan data karena data ada di volume"],
    ["Network", "`app_network` menyambungkan Nginx, Flask, dan PostgreSQL; `nosql_network` (internal) hanya MongoDB dan Flask NoSQL", "API: Nginx meneruskan `/api/...` ke `backend:5000` lewat nama service. Container: tiap container hanya mencapai tetangganya", "Tanpa network yang sama, Flask tidak menemukan `database:5432`; tanpa `internal`, MongoDB bisa dijangkau dari luar"],
    ["Storage", "Volume `postgres_data` dan `mongo_data` dipasang ke direktori data masing-masing database", "Container: volume menempel ke container database. API: setiap Create, Update, Delete berakhir di volume ini", "Tanpa volume, data hilang saat container dibuat ulang; `down -v` sengaja dihindari"],
    ["API", "REST JSON lewat Nginx: `/api/sql/*` ke PostgreSQL, `/api/nosql/*` ke MongoDB", "Network: jalur permintaan antar container. Storage: operasi INSERT/UPDATE/DELETE atau insert_one/delete_one", "Tanpa API, browser tidak punya jalan resmi ke database; tanpa validasi API, data tidak konsisten"]], [2.4, 4.9, 4.7, 4.0], size=8)
para("Bukti hubungan ini: setelah `restart-all` (container dihentikan dan dinyalakan lagi) jumlah dan id buku sebelum dan sesudah sama (`bukti/unified/ctl_restart-all_20261110_181951.txt`), dan permintaan Create dari website muncul di PostgreSQL ketika dibaca langsung dengan `./scripts/ctl.sh verify`.", size=10)

# ======================= 6. MASALAH =======================
h1("6. Masalah dan Solusi")
para("Tabel hanya memuat kendala yang benar-benar terjadi selama pengerjaan, dengan penyebab dan cara mengatasinya.", size=10, color="4A5F68")
table(["Masalah", "Penyebab dan cara mengatasi"], [
    ["Port 8080 bentrok", "Port 8080 di VM sudah dipakai container proyek lain. Diperiksa dengan `sudo docker ps` dan `sudo ss -ltnp`. **Solusi:** pemetaan frontend diubah menjadi 8081:80; container proyek lain tidak dihentikan."],
    ["Belum punya domain untuk Cloudflare Tunnel", "Cloudflare Tunnel dan Access yang permanen memerlukan domain. **Solusi:** memakai Tailscale Funnel (alamat HTTPS tetap tanpa domain). Karena Funnel tidak punya gerbang identitas, pengamanan ada di aplikasi (header CSRF, pembatasan laju, validasi) dan, sebelum login dicabut, login untuk tulis. Skrip Cloudflare (`scripts/tunnel.sh`) disiapkan bila domain tersedia."],
    ["Akses publik membuka API tulis ke internet", "Awalnya penulisan dilindungi login Basic Auth di Nginx (baca terbuka, tulis wajib login). Login menyulitkan penggunaan: kotak nama pengguna dan kata sandi muncul di tengah pengisian, salah ketik membuat permintaan berulang, dan memicu pesan 429. **Solusi:** atas keputusan pemilik proyek login dicabut (mode terbuka). Perlindungan yang tersisa: header CSRF, pembatasan laju 10/detik (burst 20), batas badan 16 KB, validasi. Risiko yang diterima dan dicatat: siapa pun dengan alamat publik dapat mengubah data. Login bisa diaktifkan lagi dengan satu baris konfigurasi."],
    ["Pesan 'Terlalu banyak permintaan' saat menyimpan buku", "Dari log Nginx: batas laju tulis awalnya 2 per detik dan dipakai bersama karena semua pengunjung Funnel tampak satu alamat; permintaan login yang berulang ikut menghabiskannya. **Solusi:** batas dinaikkan menjadi 10 per detik (burst 20) dan sumber permintaan berulang (login) dihapus."],
    ["API SQL membalas halaman HTML saat alamat tidak ada", "Flask backend SQL memakai penanganan galat bawaan: alamat tidak dikenal (404), metode salah (405), atau badan terlalu besar membalas HTML, berbeda dengan API NoSQL yang sudah JSON. Ditemukan saat audit endpoint (`GET /api/sql/books/abc`). **Solusi:** handler `HTTPException` dan `Exception` di `backend/app.py` sehingga semua galat berformat JSON; diuji di `test_akses.py`."],
    ["Nginx gagal start bila backend NoSQL belum ada", "Nginx menerjemahkan nama upstream saat start. **Solusi:** resolver Docker dan variabel upstream; bila backend mati, Nginx tetap hidup dan membalas 503 JSON."],
    ["`limit_except` membuat tulis gagal 500", "Pada tahap login, direktif itu melewati pengecekan CSRF dan handler proxy. **Solusi:** diganti `auth_basic` berbasis variabel; setelah login dicabut variabel yang sama dipakai untuk mematikannya."],
    ["Header keamanan hilang pada respons tertentu", "`add_header` di dalam `location` menghapus header tingkat server. **Solusi:** header diulang pada location galat; lokasi API memakai `expires -1` tanpa `add_header`."],
    ["Berkas `.env` tertimpa", "Saat README ditulis lewat heredoc tanpa tanda kutip, perintah `cp .env.example .env` di dalam teks ikut dijalankan. **Solusi:** `.env` dipulihkan dari variabel container yang sedang berjalan (`scripts/restore_env.sh`), contoh perintah diperbaiki, cadangan dibuat. Volume database tidak tersentuh."],
    ["Id berbeda tipe (integer vs ObjectId) memecah UI", "**Solusi:** frontend memperlakukan id sebagai string dan memakai urutan dari API."],
    ["Respons mode lama menimpa tampilan mode baru", "Saat pengguna berganti SQL/NoSQL, respons yang terlambat masih tiba. **Solusi:** request dibatalkan (AbortController) dan respons dicocokkan dengan mode aktif; diuji dengan request yang sengaja ditunda."],
    ["Dropdown kategori tidak memuat kategori lain", "Buku berkategori di luar lima pilihan tidak dapat disimpan saat diedit. **Solusi:** pilihan dibuat dinamis dari data."],
    ["Halaman melebar di layar HP", "Navigasi pindah baris tetapi kontainer tidak `flex-wrap`. **Solusi:** `flex-wrap: wrap`, lebar diukur ulang di 360 sampai 1024 piksel."],
    ["Uji otomatis melaporkan 9 kegagalan lewat alamat publik", "Skrip mencari nama header huruf besar, padahal HTTP/2 mengirim huruf kecil. **Solusi:** pencarian header tidak peka huruf besar-kecil; aplikasi tidak berubah."],
    ["Token GitHub tempelan terkontaminasi karakter kontrol", "Push pertama gagal. **Solusi:** skrip `push_github.sh` membersihkan dan memvalidasi token sebelum dipakai."]], [4.6, 11.4], size=8.5)

# ======================= 7. VERIFIKASI =======================
h1("7. Verifikasi dan Testing")
para("Bab ini menjawab bagian D PDF: (1) aplikasi dapat diakses lewat alamat public, (2) API diuji lewat browser atau Postman, (3) hasil response JSON ditampilkan.")
h2("7.1 Akses lewat alamat public (D.1)")
para(f"Alamat: **{URL}/** (HTTPS, sertifikat Let's Encrypt, HTTP/2). Semua screenshot di laporan ini diambil dari alamat tersebut. Hasil `scripts/test_akses.py` lewat alamat publik: **49 PASS, 0 FAIL**, yaitu baca 200, CRUD tanpa login berhasil di kedua database (POST 201, PUT 200, DELETE 200, lalu GET 404), tulis tanpa header aplikasi 403, galat API selalu JSON, validasi menolak data buruk dengan 400, batas laju memberi 429 pada rentetan permintaan, header keamanan lengkap, dan port 8081 hanya di 127.0.0.1. Log Nginx juga mencatat permintaan dari browser Chrome di Windows lewat alamat publik yang sama.")
para("Pembatasan yang perlu disebut: pengujian otomatis tersebut dijalankan dari dalam VM Kali lewat alamat publik, sehingga tidak membuktikan akses dari jaringan lain. Akses dari perangkat Android lewat data seluler (Wi-Fi mati) dilaporkan berhasil oleh penyusun; bukti screenshot dari perangkat tersebut dilampirkan sendiri oleh penyusun dan belum disisipkan di dokumen ini.", size=10)
h2("7.2 Uji API lewat browser dan JSON (D.2 dan D.3)")
para("Endpoint GET dibuka di Firefox (Gambar 4.1 sampai 4.6). Operasi POST, PUT, DELETE dikirim dengan skrip HTTP (`scripts/ambil_json.py`) dan lewat antarmuka website (7.3). Seluruh respons JSON nyata ada di bab 4 (tabel 4.1 dan 4.2). **Postman belum diuji**; pengujian dilakukan dengan browser dan skrip.")
h2("7.3 CRUD lewat website: PostgreSQL")
para("Urutan di Dashboard mode SQL, tanpa login. Setiap langkah mengirim permintaan ke API (POST 201, PUT 200, DELETE 200) dan tampilan memuat ulang data dari database. Banner kuning mengingatkan bahwa siapa pun dapat mengubah data.", size=10)
figure("03-dashboard-sql.png", "Gambar 7.1  Kondisi awal Dashboard mode SQL.")
figure("04-sql-dialog-tambah.png", "Gambar 7.2  Create: dialog Tambah buku terisi.")
figure("05-sql-sesudah-create.png", "Gambar 7.3  Sesudah Create (POST 201): buku baru muncul di atas tabel; jumlah judul bertambah satu; notifikasi 'ditambahkan ke PostgreSQL'.")
figure("06-sql-dialog-ubah.png", "Gambar 7.4  Update: dialog Edit, judul dan stok diubah.")
figure("07-sql-sesudah-update.png", "Gambar 7.5  Sesudah Update (PUT 200): judul 'Edisi Revisi' dan stok 30.")
figure("08-sql-konfirmasi-hapus.png", "Gambar 7.6  Delete: dialog konfirmasi menyebut judul buku dan database yang terdampak.")
figure("09-sql-sesudah-delete.png", "Gambar 7.7  Sesudah Delete (DELETE 200): buku uji hilang; jumlah buku kembali seperti kondisi awal.")
h2("7.4 CRUD lewat website: MongoDB")
para("Pilihan NoSQL di Dashboard mengganti seluruh tampilan dan alamat API ke `/api/nosql/books`. Data MongoDB terpisah dari PostgreSQL.", size=10)
figure("10-dashboard-nosql.png", "Gambar 7.8  Mode NoSQL: banner 'Database aktif: MongoDB (NoSQL)'; id berupa ObjectId; data terpisah dari PostgreSQL.")
figure("11-nosql-dialog-tambah.png", "Gambar 7.9  Create di MongoDB: tombol dan petunjuk menyebut MongoDB.")
figure("12-nosql-sesudah-create.png", "Gambar 7.10  Sesudah Create (POST 201): dokumen baru tersimpan di MongoDB; PostgreSQL tidak ikut berubah.")
figure("13-nosql-sesudah-delete.png", "Gambar 7.11  Sesudah Delete: dokumen uji dihapus.")
h2("7.5 Ringkasan hasil pengujian")
table(["Pengujian", "Hasil", "Bukti"], [
    ["Unit test validasi (backend SQL dan NoSQL)", "14 tes lulus", "tests/, backend/tests/"],
    ["API SQL dan NoSQL: CRUD, validasi, 404, bentuk JSON, isolasi data", "PASS 87 pemeriksaan", "scripts/test_api.py"],
    ["Keamanan terarah: injeksi SQL/NoSQL, XSS, CSRF, CORS, port", "PASS 25 pemeriksaan", "scripts/test_keamanan.py"],
    ["Akses mode terbuka: CRUD tanpa login, CSRF, galat JSON, validasi, batas laju, header, port; lokal dan lewat alamat publik", "PASS 49 pemeriksaan (dua kali)", "scripts/test_akses.py"],
    ["UI Firefox: mode SQL/NoSQL, CRUD kedua database, dialog, Perbandingan, keyboard", "PASS 39 pemeriksaan, 0 gagal (1 pemeriksaan 'koleksi kosong' dilewati karena koleksi NoSQL berisi)", "scripts/run_ui_test.py"],
    ["Data bertahan setelah `down` lalu `up` tanpa `-v` (kedua volume)", "PASS: data sebelum = sesudah", "bukti/unified/ctl_restart-all_*.txt"],
    ["MongoDB dimatikan: API NoSQL 503 JSON, SQL tetap normal", "PASS", "bukti/unified/mongo_down_*.txt"],
    ["Screenshot dan JSON laporan ini (alamat publik)", "23 gambar dan 18 respons; data uji dihapus kembali", "bukti/laporan/"]], [7.2, 4.3, 4.5], size=8.5)
para("Catatan: bukti pengujian lama di `bukti/publik/` dan `bukti/unified/` dibuat saat login masih aktif (41 pemeriksaan akses); angka terbaru ada pada tabel di atas.", size=9.5, color="4A5F68")
para("**Belum diuji atau belum dibuktikan:** Postman; Funnel tetap aktif setelah reboot Kali; akses dari host Windows lewat NAT (tidak dibutuhkan untuk platform Docker); Cloudflare Tunnel dan Access (tidak dikerjakan, tidak ada domain); pembaca layar dan layar sentuh; benchmark beban.", size=10)

# ======================= 8. DEMO =======================
h1("8. Demonstrasi")
para("Bagian E PDF: presentasi minimal 5 menit per kelompok pada pertemuan setelah UTS, menampilkan (a) website berjalan, (b) endpoint API diakses melalui browser atau Postman, dan (c) penjelasan singkat arsitektur dan deployment flow. Rencana sekitar 6 menit; naskah lengkap di `docs/naskah.md`.")
table(["Waktu", "Bagian PDF", "Isi"], [
    ["0:00 - 0:40", "Pembukaan", "Identitas, kasus No. 15: Perpustakaan, Microservices (Docker), SQL; MongoDB sebagai tambahan"],
    ["0:40 - 2:00", "E.2.c Arsitektur dan deployment flow", f"Gambar 5.1: Browser, Funnel, Nginx, Flask, PostgreSQL/MongoDB, network, volume; tunjukkan `docker compose ps` dan `compose.yaml`"],
    ["2:00 - 3:40", "E.2.a Website berjalan", f"Buka {URL}: Beranda, Katalog (cari dan filter), Dashboard: tambah, ubah, hapus; ganti ke NoSQL"],
    ["3:40 - 4:50", "E.2.b Endpoint API", "Buka /api/sql/books dan /api/nosql/books di browser; /health; tunjukkan galat JSON (404) dan 403 untuk tulis tanpa header aplikasi"],
    ["4:50 - 6:00", "Penutup", "Bukti data bertahan setelah restart (volume), masalah dan solusi (bab 6), repositori GitHub"]], [2.4, 4.4, 9.2], size=9)

# ======================= 9. KESIMPULAN =======================
h1("9. Kesimpulan")
para("LibraryKu mengimplementasikan CRUD lengkap lewat website, REST API Flask, dan database PostgreSQL (kasus No. 15), dengan MongoDB sebagai database kedua dalam aplikasi yang sama. Docker Compose menjalankan lima service yang berkomunikasi lewat network bridge, volume menjaga data tetap ada setelah container dibuat ulang, dan Nginx menjadi satu-satunya pintu masuk. Aplikasi dapat dibuka lewat alamat HTTPS publik. Penulisan data tidak memakai login (mode terbuka, keputusan pemilik proyek) tetapi tetap dilindungi header aplikasi, pembatasan laju, dan validasi; risikonya, siapa pun yang tahu alamat dapat mengubah data, sehingga yang dimasukkan sebaiknya data contoh. Seluruh screenshot dan respons JSON di laporan ini berasal dari aplikasi yang berjalan. Hal yang belum diuji tercantum di akhir bab 7.")

# ======================= LAMPIRAN =======================
h1("Lampiran A. Repositori Kode dan Pengumpulan")
para(f"Sesuai ketentuan dosen, file code, Dockerfile, dan laporan dikumpulkan lewat tautan GitHub: {REPO}")
table(["Isi repositori", "Lokasi"], [
    ["Docker Compose dan Dockerfile", "compose.yaml, backend/Dockerfile, backend_nosql/Dockerfile"],
    ["Konfigurasi Nginx dan skrip inisialisasi database", "nginx/default.conf, database/init.sql, mongodb/init-app-user.js"],
    ["Kode backend dan frontend", "backend/, backend_nosql/, frontend/"],
    ["Skrip operasi dan pengujian", "scripts/ (ctl.sh, funnel.sh, uji.sh, test_api.py, test_akses.py, ambil_screenshot.py, ambil_json.py), tests/"],
    ["Dokumentasi dan bukti", "docs/, bukti/ (termasuk bukti/laporan/ untuk screenshot laporan ini)"],
    ["Laporan dan presentasi", "laporan/laporan.docx, laporan/presentasi.pptx"]], [6.5, 9.5], size=9)
para("Berkas rahasia tidak ada di repositori: `.env`, `nginx/auth/` (hash login lama, tidak dipakai lagi), kredensial, dan token (diatur di `.gitignore` dan dipindai sebelum push). Untuk menjalankan dari awal ikuti 3.4.", size=10)
para("Screenshot dapat dibuat ulang dengan `python3 scripts/ambil_screenshot.py` dan JSON dengan `python3 scripts/ambil_json.py`.", size=10)

doc.save(OUT)
print("tersimpan:", OUT)
