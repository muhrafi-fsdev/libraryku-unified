# Audit awal LibraryKu Unified (2026-11-10, read-only)

Dikerjakan sebelum mengubah source apa pun. Tidak ada rahasia yang dicantumkan.

## 1. Source aktif = deployment aktif?
| Pemeriksaan | Hasil |
|---|---|
| Folder aktif | `/home/riyooo/LibraryKu_UIUX/LibraryKu_Project1` (bukan salinan di `~/Unduhan`) |
| Frontend yang disajikan di `:8081` vs file di `frontend/` | SHA-256 `index.html`, `app.js`, `style.css` identik (bind mount read-only) |
| Backend yang berjalan vs `backend/` | Tidak bisa dibandingkan lewat image (akses Docker butuh sudo); perilaku API sama dengan kode (`/api/health`, `/api/books` mengembalikan 3 buku: id 10, 2, 1) |
| Repository Git | Tidak ada. Checkpoint memakai arsip `~/backup_libraryku_unified_20261110-174352.tar.gz` (tanpa `.env`, tanpa `__pycache__`; sudah dicek tidak memuat password) |

## 2. Lingkungan
| Hal | Hasil |
|---|---|
| OS | Kali Rolling, kernel 7.2.15 (VM baru menyala ulang 10 menit sebelum audit) |
| RAM / CPU / disk | 7,8 GiB (4,2 GiB tersedia) / 4 core / 18 GB kosong |
| CPU AVX/AVX2 | Ada. MongoDB 5+ membutuhkan AVX, jadi `mongo:7.0` bisa dipakai di VM ini |
| Docker | `dockerd` aktif; user `riyooo` tidak di grup `docker`, jadi semua perintah Docker butuh `sudo` yang dijalankan pengguna |
| Port terbuka | `0.0.0.0:8081` (LibraryKu), `127.0.0.1:5432, 8000, 8080, 3000` (praktikum/proyek lain, tidak disentuh). `27017` bebas |
| Registry | Docker Hub terjangkau (HTTP 401 pada `/v2/` = normal). Tag `mongo:7.0.45` (27 Okt 2026, amd64) tersedia |

## 3. Arsitektur sekarang
`frontend` (nginx:1.28-alpine, bind mount `frontend/` dan `nginx/default.conf`, publish 8081) -> `backend` (Flask + gunicorn, port 5000 `expose` saja) -> `database` (postgres:16-alpine, volume `postgres_data`, `init.sql` hanya jalan saat volume baru). Satu bridge `app_network`. Nama project Compose `libraryku-project1`. Password lewat `${POSTGRES_PASSWORD}` dari `.env` (tidak ada literal di `compose.yaml`).
Route Flask: `GET /api/health`, `GET|POST /api/books`, `GET|PUT|DELETE /api/books/<id>`. Tabel `books` (id identity, title, author, category, year, stock, created_at) dengan CHECK constraint. Nginx meneruskan `/api/` ke `backend:5000`.

## 4. Aman dipertahankan
Service `database`, `backend`, volume `postgres_data`, nama project, `init.sql`, endpoint `/api/books`, seluruh data (3 buku), UI V3 (Beranda, Katalog, Dashboard, Tentang).

## 5. Yang perlu ditambahkan (additive)
1. Service `mongodb` (image `mongo:7.0.45`, volume `mongo_data` terpisah, tanpa publish port, user aplikasi berhak terbatas, healthcheck, batas resource).
2. Service `backend-nosql` (Flask + PyMongo, image sendiri, non-root).
3. Nginx: `/api/sql/*` di-rewrite ke backend SQL lama (tanpa mengubah kode SQL), `/api/nosql/*` ke backend baru. Route lama `/api/books` tetap.
4. Variabel baru di `.env` (hanya ditambah, tidak ditimpa) dan placeholder di `.env.example`.
5. Frontend: pemilih mode SQL/NoSQL, indikator database aktif, halaman Perbandingan, penyesuaian ID (angka vs string) dan pembatalan request saat ganti mode.

## 6. Risiko integrasi MongoDB dan mitigasinya
| Risiko | Mitigasi |
|---|---|
| Menyentuh volume/konfigurasi PostgreSQL | Hanya menambah service dan volume; `database`, `backend`, `postgres_data`, dan nama project tidak diubah |
| `up -d` membuat ulang container frontend (depends_on berubah) | Downtime beberapa detik pada frontend saja; dijalankan atas izin pengguna |
| Tercampurnya data SQL dan NoSQL | Dua database dan dua API terpisah, tanpa sinkronisasi otomatis; frontend memakai satu mode aktif dan membatalkan request mode lama |
| NoSQL injection | Input hanya diterima lewat validasi tipe ketat (string/integer), ID divalidasi 24 heks sebelum query, tidak ada filter dari input pengguna |
| Port 27017 terbuka | Tidak dipublikasikan; hanya jaringan Docker |
| Kredensial bocor | Password acak di `.env` (mode 600, di `.gitignore`), tidak dicetak, tidak masuk backup |
| Image pull/tag | Tag dipin `7.0.45`; digest dicatat setelah pull |
| Akses Docker | Perintah Docker dijalankan pengguna lewat `scripts/ctl.sh` (bukti tersimpan di `bukti/unified/`) |

## 7. Strategi rollback
1. Kode: kembalikan dari `~/backup_libraryku_unified_20261110-174352.tar.gz` (frontend V3, compose, nginx lama).
2. Runtime: `sudo docker compose up -d` dari compose lama menghentikan peran NoSQL tanpa menyentuh `postgres_data`; container baru dihapus dengan `docker compose rm -sf mongodb backend-nosql` (tanpa `-v`). Volume `mongo_data` hanya dihapus jika pengguna memintanya.
3. Larangan tetap: tidak ada `down -v`, `volume prune`, `system prune`.

## 8. Alat keamanan yang tersedia
Skill terpasang: `api-security-testing`, `application-security-testing`, `owasp-top-10-testing`, `find-security-vulnerabilities-in-code`, `web-app-penetration-testing` (semua berbasis Strix), `zizi-skills:security-and-hardening`, dan `security-review` bawaan. CLI `strix`, `semgrep`, `trivy`, dan `bandit` tidak terpasang, jadi Strix tidak bisa dijalankan; review dikerjakan manual dengan pengujian terarah pada aplikasi lokal.
