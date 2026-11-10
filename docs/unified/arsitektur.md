# LibraryKu Unified: arsitektur dan deployment

Satu website (`http://localhost:8081`) dengan dua database terpisah: PostgreSQL (SQL) dan MongoDB (NoSQL). Dikerjakan di Kali Linux (VirtualBox) dengan Docker Compose.

## 1. Alur permintaan
```
Browser
  -> Nginx (frontend, satu-satunya yang dibuka ke host, 8081)
       |- /            : file statis HTML/CSS/JS (bind mount read-only)
       |- /api/sql/*   : di-rewrite ke /api/* -> Flask SQL (backend)        -> PostgreSQL (database)
       |- /api/books   : alamat lama, tetap ke Flask SQL (kompatibilitas)
       |- /api/nosql/* : Flask NoSQL (backend-nosql)                        -> MongoDB (mongodb)
```
"Database Mode Router" = (1) pilihan SQL/NoSQL di frontend yang menentukan awalan alamat API (`/api/sql` atau `/api/nosql`) dan (2) Nginx yang meneruskan tiap awalan ke backend yang sesuai. Kedua database tidak pernah saling menyalin data.

## 2. Container
| Service | Image | Peran | Port ke host | Jaringan |
|---|---|---|---|---|
| frontend | nginx:1.28-alpine | web server dan router | **8081** | app_network |
| backend | build `./backend` (Flask, gunicorn) | API SQL (tidak diubah) | tidak ada (expose 5000) | app_network |
| database | postgres:16-alpine | PostgreSQL | tidak ada | app_network |
| backend-nosql | build `./backend_nosql` (Flask, PyMongo, gunicorn) | API NoSQL | tidak ada (expose 5000) | app_network, nosql_network |
| mongodb | mongo:7.0.45 | MongoDB | tidak ada (27017 tidak dipublikasikan) | nosql_network (internal) |

Nama project Compose tetap `libraryku-project1`. Service `database`, `backend`, `frontend` dan volume `postgres_data` tidak diubah (bagian lama `compose.yaml` identik dengan backup).

## 3. Docker networking
- `app_network` (bridge): frontend, backend, database, backend-nosql.
- `nosql_network` (bridge, `internal: true`): hanya `mongodb` dan `backend-nosql`; MongoDB tidak punya jalur keluar-masuk ke host.
- Nginx memakai resolver Docker (`127.0.0.11`) dan variabel upstream, sehingga Nginx tetap hidup bila backend NoSQL atau MongoDB mati (hasilnya 503 JSON, bukan Nginx gagal start).

## 4. Penyimpanan dan persistensi
| Volume | Dipakai | Isi |
|---|---|---|
| `postgres_data` | database | data PostgreSQL (tabel `books`) |
| `mongo_data` | mongodb | data MongoDB (database `libraryku_nosql`, koleksi `books`) |

`docker compose down` tanpa `-v` menghapus container dan jaringan, tetapi kedua volume tetap ada (terbukti pada uji `restart-all`). Jangan pernah memakai `down -v`.

## 5. Skema data
- SQL: tabel `books(id integer identity, title, author, category, year, stock, created_at)` dengan CHECK (lihat `database/init.sql`).
- NoSQL: dokumen `{_id: ObjectId, title, author, category, year, stock, created_at}` di koleksi `books`. API mengirim `_id` sebagai string `id` (24 karakter heksadesimal).
- Kontrak JSON kedua API sama: `{data:[...], total}` untuk daftar, `{message, data}` untuk tulis, `{error, details?}` untuk galat. Bedanya hanya tipe `id` (integer vs string).

## 6. Endpoint
| Metode | SQL (PostgreSQL) | NoSQL (MongoDB) |
|---|---|---|
| GET | `/api/sql/health` | `/api/nosql/health` |
| GET | `/api/sql/books` | `/api/nosql/books` |
| GET | `/api/sql/books/{id}` | `/api/nosql/books/{id}` |
| POST | `/api/sql/books` | `/api/nosql/books` |
| PUT | `/api/sql/books/{id}` | `/api/nosql/books/{id}` |
| DELETE | `/api/sql/books/{id}` | `/api/nosql/books/{id}` |
Alamat lama `/api/health` dan `/api/books...` tetap ke PostgreSQL. Status HTTP: 200, 201, 400 (data atau id tidak valid), 404 (tidak ditemukan), 413 (badan > 16 KB), 503 (database tidak tersedia).
Perbedaan perilaku id tidak valid: SQL (`/api/sql/books/abc`) 404 dari router Flask; NoSQL 400 JSON ("ID buku tidak valid") karena ID divalidasi sebelum query.

## 7. Konfigurasi MongoDB
- Image dipin `mongo:7.0.45` (digest tercatat di `bukti/unified/ctl_up_*.txt`).
- Root admin dan pengguna aplikasi lewat environment dari `.env` (`MONGO_ROOT_PASSWORD`, `MONGO_APP_PASSWORD`). `.env` berizin 600, ada di `.gitignore`; `.env.example` hanya berisi placeholder.
- Pengguna aplikasi `libraryku_app` hanya berhak `readWrite` pada database `libraryku_nosql` (dibuat idempoten oleh `mongodb/init-app-user.js` saat volume kosong). Backend NoSQL memakai pengguna ini, bukan root.
- Healthcheck: login sebagai pengguna aplikasi lalu `ping`. Batas resource: 640 MB RAM, 1 CPU, 300 proses; cache WiredTiger 0,25 GB; `no-new-privileges`; log berputar (10 MB x 3). Proses `mongod` berjalan sebagai uid 999 (non-root, terbukti).
- Backend NoSQL: pengguna `appuser` (uid 10001), filesystem root read-only, `cap_drop: ALL`, `no-new-privileges`, batas 256 MB dan 0,5 CPU; koneksi memakai timeout 3 detik.

## 8. Menjalankan dan mengoperasikan
Semua dari `~/LibraryKu_UIUX/LibraryKu_Project1` (bukan salinan di Unduhan). Docker butuh `sudo`, jadi dijalankan pengguna lewat skrip; hasilnya tersimpan di `bukti/unified/`.
| Perintah | Fungsi |
|---|---|
| `./scripts/ctl.sh up` | tarik image, bangun backend NoSQL, nyalakan MongoDB dan backend NoSQL, muat ulang Nginx (service SQL tidak dibuat ulang) |
| `./scripts/ctl.sh status` | container, port, resource, jaringan, volume, health |
| `./scripts/ctl.sh verify` | isi MongoDB dan PostgreSQL langsung, uji autentikasi |
| `./scripts/ctl.sh security` | pengaturan keamanan container, port, pustaka, Nginx |
| `./scripts/ctl.sh stop-nosql` / `start-nosql` | uji galat saat MongoDB mati |
| `./scripts/ctl.sh restart-all` | down lalu up tanpa `-v`, bandingkan data |
Pengujian otomatis (tanpa Docker, hanya HTTP): `python3 scripts/test_api.py`, `python3 scripts/test_keamanan.py`, `python3 -m unittest discover -s tests`.

## 9. Rollback
1. Kode: pulihkan dari `~/backup_libraryku_unified_20261110-174352.tar.gz` (tanpa `.env`).
2. Runtime: hentikan peran NoSQL dengan `docker compose rm -sf mongodb backend-nosql` (tanpa `-v`); PostgreSQL tidak tersentuh. Volume `mongo_data` hanya dihapus bila Anda memintanya.

## 10. Batasan yang diketahui
- Pembaruan 2026-11-10: penulisan data kini wajib login (Basic Auth Nginx), dengan header CSRF dan pembatasan laju; 8081 hanya di `127.0.0.1`. Lihat `docs/publik/`. Membaca tetap terbuka.
- HTTP saja (tanpa HTTPS), dan tanpa pembatasan laju permintaan.
- Container SQL lama (backend, PostgreSQL, Nginx) tidak diperketat (root, tanpa batas resource); mengubahnya berarti membuat ulang container SQL.
