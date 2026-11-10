# Review keamanan LibraryKu Unified (2026-11-10)

> Pembaruan 2026-11-10 (malam): temuan "tanpa autentikasi" di bawah sudah dimitigasi: penulisan kini wajib login (Basic Auth Nginx), header CSRF, dan pembatasan laju; 8081 hanya di 127.0.0.1. Bukti: `docs/publik/pengujian.md`. Baca tetap terbuka; HTTPS publik belum aktif.

Cakupan: aplikasi lokal milik sendiri (`localhost:8081`). Tidak ada pemindaian jaringan lain dan tidak ada pengujian destruktif; semua data uji dihapus.

## Alat
| Alat | Status |
|---|---|
| Skill Strix (`penetration-testing-with-strix`, `owasp-top-10-testing`, `api-security-testing`, `web-app-penetration-testing`, dll.) | Terpasang sebagai instruksi, tetapi CLI `strix` tidak ada, jadi **tidak dijalankan** |
| Skill `security-review` dan `zizi-skills:security-and-hardening` | Tersedia di sesi; review dikerjakan manual mengikuti daftar yang diminta, dengan skrip uji sendiri |
| Uji terarah | `scripts/test_keamanan.py` (25 pemeriksaan), `scripts/test_api.py` (87), uji XSS UI di Firefox |
| `pip-audit` 2.10.1 (venv terisolasi `~/.venvs/libraryku-sec`) | Dijalankan untuk dependensi kedua backend |
| `semgrep`, `trivy`, `bandit` | Tidak terpasang, tidak dijalankan |

## Hasil per butir
| # | Butir | Status | Bukti dan catatan |
|---|---|---|---|
| 1 | Validasi input | PASS | Judul, penulis, kategori harus string (panjang dibatasi), tahun dan stok integer dalam rentang, boolean ditolak, badan JSON maks 16 KB. Kedua backend memakai aturan yang sama |
| 2 | SQL injection | PASS | Payload `'); DROP TABLE books; --`, `' OR '1'='1`, `UNION` tersimpan sebagai teks biasa (query berparameter); tabel utuh; id URL `1 OR 1=1`, `1;DROP...` -> 404 |
| 3 | NoSQL injection | PASS | `{"$ne":""}`, `{"$gt":0}`, `{"$where":...}`, array di kolom -> 400; operator di query string diabaikan; ID bukan 24 heks (termasuk `$ne`, JSON, newline) -> 400 tanpa query; kolom asing (`$where`, `role`, `_id`) tidak tersimpan |
| 4 | XSS | PASS | Judul/penulis berisi `<img onerror>` dan `<script>`: API mengirim JSON `application/json` + `nosniff`; UI memakai `textContent` (tanpa `innerHTML`); diuji di Firefox pada 3 halaman x 2 mode, tidak ada eksekusi, tidak ada elemen `img`/`script` tersisip. CSP `script-src 'self'` tanpa pelanggaran |
| 5 | CORS | PASS | Tidak ada header `Access-Control-Allow-Origin`; preflight dari origin asing tidak diberi izin |
| 6 | CSRF | Relevansi rendah | Tidak ada cookie/sesi; POST ala form (`text/plain`) ditolak 400. Risiko sebenarnya: **tidak ada autentikasi** (lihat temuan 1) |
| 7 | Exposure port | PASS | Hanya `0.0.0.0:8081` (Nginx). 27017, 5432, 5000 milik LibraryKu tidak dipublikasikan; `ss` tidak menampilkan 27017/5000. MongoDB berada di jaringan `internal` |
| 8 | Pengelolaan kredensial | PASS (dengan catatan) | Password di `.env` (mode 600, `.gitignore`), tidak ada di `compose.yaml`, dokumen, bukti, atau backup (dipindai mentah). Password PostgreSQL lama bersifat demo (sesuai komentar `.env.example`) |
| 9 | Least privilege database | PASS | Pengguna aplikasi MongoDB hanya `readWrite` pada `libraryku_nosql`; akses tanpa kredensial dan ke `admin` ditolak (`Unauthorized`) |
| 10 | Keamanan container | PARTIAL | Baru (mongodb, backend-nosql): `no-new-privileges`, batas memori/CPU/proses, backend-nosql non-root + read-only + `cap_drop ALL`, mongod uid 999. Lama (backend SQL, PostgreSQL, Nginx): root tanpa `cap_drop`/batas resource, tidak diubah |
| 11 | Kerentanan dependensi | PARTIAL | `pip-audit`: Flask 3.1.3, Werkzeug 3.1.9, PyMongo 4.19.0, psycopg2 2.9.13, dll. bersih. Hanya `pip` bawaan image yang rentan: sudah 26.3 di image NoSQL, masih 25.0.1 di image SQL (alat instal, bukan runtime) |
| 12 | Informasi sensitif di JSON | PASS | Tidak ada kredensial, URI koneksi, nama pengguna DB, path, atau jejak tumpukan di respons normal maupun galat; galat DB memakai pesan generik 503 |
| 13 | Error handling | PASS | 400/404/405/413/503 berformat JSON (NoSQL); galat tak terduga -> 500 generik; MongoDB mati -> 503, Nginx tetap hidup |
| 14 | Konfigurasi Nginx | PASS | `server_tokens off`, `client_max_body_size 16k`, `X-Content-Type-Options`, `X-Frame-Options DENY`, `Referrer-Policy`, `Permissions-Policy`, CSP ketat, timeout proxy 3/15 dtk, `TRACE`/`CONNECT` tidak diterima. HTTPS dan pembatasan laju belum ada |

## Temuan menurut risiko
| Risiko | Temuan | Rekomendasi |
|---|---|---|
| **Tinggi** (bila dijangkau jaringan lain) | Dashboard dan kedua API tanpa autentikasi: siapa pun yang menjangkau port 8081 dapat membuat, mengubah, menghapus data. Memisahkan halaman Dashboard hanya memisahkan tampilan | Tetap di jaringan lokal/NAT loopback (lihat `docs/akses-windows.md`); sebelum diekspos, tambah autentikasi dan HTTPS. Tidak dikerjakan (di luar permintaan) |
| Sedang | Container lama berjalan sebagai root tanpa batas resource/capability | Perketat saat jendela perawatan berikutnya (build ulang backend SQL non-root, `cap_drop`, batas resource) |
| Rendah | Tidak ada pembatasan laju; HTTP tanpa TLS | Tambah `limit_req` dan TLS bila diekspos |
| Rendah | `pip` 25.0.1 di image SQL punya kerentanan yang dilaporkan | Perbarui pip saat image SQL dibangun ulang |
| Rendah | Rute asing di backend SQL membalas HTML bawaan Flask | Tambah handler JSON atau abaikan (tidak melanggar tugas) |
| Info | Strix tidak terpasang | Jalankan Strix terhadap `localhost:8081` bila ingin pentest otomatis (butuh persetujuan pemasangan) |
