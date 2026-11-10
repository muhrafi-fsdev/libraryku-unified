# LibraryKu

Website katalog perpustakaan untuk Project 1 mata kuliah Cloud Computing, Telkom University. Kita bisa melihat, mencari, menambah, mengubah, dan menghapus data buku. Datanya disimpan di PostgreSQL atau MongoDB, tergantung mana yang dipilih di website. Semua bagiannya jalan sebagai container Docker.

Kelompok kami (kelas S1TT-KJ-23-04):

| Nama | NIM |
|---|---|
| Muhammad Rafi Priyo Sembodo | 101072300038 |
| Atilla Pramudya Nugroho | 101072300039 |
| Muhammad Aprilio Rizal Arifin | 101072300040 |
| Aji Eka Saputra | 101072300071 |

Kasus yang kami kerjakan adalah nomor 15 di tabel PDF penugasan: Perpustakaan, Microservices (Docker), SQL. Versi MongoDB kami tambahkan sebagai pengembangan di aplikasi yang sama, bukan sebagai tugas kedua. Nomor kelompok resminya masih perlu kami pastikan ke dosen.

## Isi aplikasi

Website punya lima halaman:

- **Beranda**: ringkasan koleksi dan buku terbaru.
- **Katalog**: cari buku berdasarkan judul atau penulis, dan saring menurut kategori. Halaman ini hanya untuk melihat.
- **Dashboard**: tempat menambah, mengubah, dan menghapus buku. Sebelum buku dihapus akan ada konfirmasi.
- **Perbandingan**: data asli dari PostgreSQL dan MongoDB berdampingan, lengkap dengan perbedaan cara kerjanya.
- **Tentang**: penjelasan singkat teknologi yang dipakai dan tautan untuk mencoba API.

Di Katalog dan Dashboard ada tombol **SQL / NoSQL**. SQL memakai PostgreSQL, NoSQL memakai MongoDB. Datanya terpisah dan tidak saling disalin.

## Cara menjalankan

Yang dibutuhkan hanya Docker dan Docker Compose. Kami menjalankannya di Kali Linux dalam VirtualBox, tetapi di Linux lain atau Windows dengan Docker Desktop caranya sama.

1. Salin contoh pengaturan, lalu isi kata sandinya dengan nilai acak buatan sendiri. Ada tiga: `POSTGRES_PASSWORD`, `MONGO_ROOT_PASSWORD`, dan `MONGO_APP_PASSWORD`. File `.env` jangan pernah di-commit.

   ```bash
   cp .env.example .env
   nano .env
   ```

2. Bangun dan jalankan semuanya.

   ```bash
   docker compose up -d --build
   docker compose ps
   ```

   Tunggu sampai `database`, `backend`, `mongodb`, dan `backend-nosql` berstatus healthy.

3. Buka http://127.0.0.1:8081 di browser.

Kalau di Windows, pakai PowerShell dan ganti `cp` dengan `Copy-Item`. Di Kali, tambahkan `sudo` di depan perintah `docker`.

Port 8081 sengaja hanya terbuka di komputer itu sendiri (`127.0.0.1`). Kalau ingin membukanya ke jaringan lokal, isi `FRONTEND_BIND=0.0.0.0` di `.env`.

Mau mengisi contoh data? Jalankan `python scripts/seed_demo.py` untuk menambah tiga buku contoh ke PostgreSQL.

## Cara kerjanya

```text
Browser
   |
   v
Nginx (container frontend, satu-satunya yang terbuka ke host: port 8081)
   |-- /api/sql/*    --> Flask SQL    --> PostgreSQL
   |-- /api/nosql/*  --> Flask NoSQL  --> MongoDB
```

Ada lima container:

| Container | Fungsinya |
|---|---|
| `frontend` | Nginx. Menyajikan halaman website dan meneruskan permintaan API ke backend yang tepat. |
| `backend` | Flask untuk PostgreSQL. |
| `database` | PostgreSQL 16. |
| `backend-nosql` | Flask untuk MongoDB. |
| `mongodb` | MongoDB 7. |

Beberapa hal yang kami atur supaya rapi dan aman:

- Container saling menemukan lewat nama service di network `app_network`. Misalnya Flask menghubungi database di alamat `database:5432`.
- MongoDB berada di network `nosql_network` yang tertutup. Hanya backend NoSQL yang bisa menjangkaunya.
- Data tersimpan di volume `postgres_data` dan `mongo_data`, jadi tetap ada walaupun container dihentikan atau dibuat ulang.
- Selain Nginx, tidak ada container yang membuka port ke host.

Satu catatan jujur soal istilah: ini sistem berlapis (web, API, database) yang dipisah ke beberapa container. Satu API perpustakaan belum otomatis berarti banyak microservice bisnis yang berdiri sendiri. Tapi untuk tujuan praktikum, yaitu memisahkan service, menghubungkannya lewat network, menyimpan data di volume, dan mengaksesnya lewat API, semuanya sudah kami tunjukkan.

## Mencoba API

Alamat dasarnya `http://127.0.0.1:8081`. Ganti `sql` dengan `nosql` untuk memakai MongoDB.

| Tujuan | Method | Alamat |
|---|---|---|
| Cek koneksi | GET | `/api/sql/health` |
| Daftar buku | GET | `/api/sql/books` |
| Satu buku | GET | `/api/sql/books/{id}` |
| Tambah buku | POST | `/api/sql/books` |
| Ubah buku | PUT | `/api/sql/books/{id}` |
| Hapus buku | DELETE | `/api/sql/books/{id}` |

Id di PostgreSQL berupa angka, sedangkan di MongoDB berupa teks 24 karakter. Alamat lama `/api/books` masih jalan dan mengarah ke PostgreSQL.

Untuk menambah buku, kirim JSON seperti ini. Permintaan yang mengubah data harus menyertakan header `X-Requested-With: libraryku` (website sudah mengirimnya sendiri, tapi di curl atau Postman perlu ditambahkan).

```bash
curl -X POST http://127.0.0.1:8081/api/sql/books \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: libraryku" \
  -d '{"title":"Dasar Jaringan Komputer","author":"Dina Lestari","category":"Pendidikan","year":2022,"stock":5}'
```

Kalau berhasil, balasannya begini (nilai `id` akan berbeda):

```json
{
  "message": "Buku berhasil ditambahkan.",
  "data": {
    "id": 1,
    "title": "Dasar Jaringan Komputer",
    "author": "Dina Lestari",
    "category": "Pendidikan",
    "year": 2022,
    "stock": 5
  }
}
```

Aturan datanya: judul maksimal 150 karakter, penulis 100, kategori 60, tahun antara 1900 dan tahun depan, stok antara 0 dan 1.000.000. Data yang tidak sesuai dijawab status 400, dan semua pesan galat berbentuk JSON dengan kunci `error`.

## Tanpa login, jadi hati-hati

Website ini tidak meminta nama pengguna dan kata sandi. Siapa pun yang bisa membuka alamatnya bisa menambah, mengubah, dan menghapus buku, jadi isi dengan data contoh saja. Perlindungan yang tetap ada: header `X-Requested-With`, pembatasan jumlah permintaan, batas ukuran data, dan validasi di backend.

Kalau nanti butuh login lagi, ubah satu baris di `nginx/default.conf` (cari `map $request_method $auth_realm`). Langkah lengkapnya ada di `docs/publik/arsitektur.md`.

## Akses dari internet

Supaya bisa dibuka dari luar komputer, kami memakai Tailscale Funnel. Cukup sambungan keluar dari VM, jadi tidak perlu membuka port di router atau mengatur port forwarding VirtualBox. Alamat HTTPS kami: https://libraryku-kali.tail342a2f.ts.net/ (hanya aktif selama komputer dan VM-nya menyala).

```bash
./scripts/funnel.sh install   # pasang Tailscale
./scripts/funnel.sh login     # masuk ke akun Tailscale
./scripts/funnel.sh enable    # aktifkan alamat publik
./scripts/funnel.sh off       # matikan lagi
```

Langkah rincinya ada di `docs/publik/aktivasi.md`.

## Pengujian

```bash
python3 scripts/test_api.py        # CRUD di PostgreSQL dan MongoDB
python3 scripts/test_keamanan.py   # injeksi, XSS, CSRF, port
python3 scripts/test_akses.py      # akses tanpa login, batas laju, galat JSON
python3 scripts/run_ui_test.py     # uji tampilan di Firefox
./scripts/ctl.sh verify            # baca isi database langsung dari container
```

Semua skrip hanya membuat buku uji dan menghapusnya lagi. Uji tampilan butuh Firefox terpasang.

## Perintah Docker yang sering dipakai

```bash
docker compose ps                 # status container
docker compose logs --tail=100    # log terakhir
docker compose logs backend       # log API SQL
docker compose down               # hentikan, data tetap aman
docker compose up -d              # nyalakan lagi
```

Jangan menjalankan `docker compose down -v`. Opsi `-v` menghapus volume, jadi semua data buku ikut hilang.

## Kalau ada masalah

| Gejala | Yang bisa dicek |
|---|---|
| Perintah `docker` tidak dikenali | Pastikan Docker sudah terpasang dan menyala (di Windows, buka Docker Desktop). |
| Muncul `permission denied` pada Docker | Tambahkan `sudo` di depan perintah, atau masukkan akun ke grup `docker`. |
| Port 8081 sudah dipakai | Cek dengan `sudo ss -ltnp \| grep :8081`. Hentikan aplikasi yang memakainya, atau ganti `8081:80` di `compose.yaml` ke port lain. Di Kali kami sendiri bentrok di 8080, makanya memakai 8081. |
| Website terbuka tapi data tidak muncul | Lihat `docker compose ps`, lalu `docker compose logs backend` atau `docker compose logs database`. |
| Database menolak kata sandi | Kata sandi di `.env` yang diubah setelah volume dibuat tidak otomatis mengubah kata sandi di dalam database. |
| Tabel `books` tidak ada | File `database/init.sql` hanya dijalankan saat volume pertama dibuat. Jangan hapus volume sembarangan. |
| Muncul "Terlalu banyak permintaan" | Batas jumlah permintaan sedang tercapai. Tunggu beberapa detik, lalu coba lagi. |

## Isi folder

| Folder | Isinya |
|---|---|
| `backend/`, `backend_nosql/` | Kode API Flask beserta Dockerfile-nya |
| `frontend/` | Halaman website (HTML, CSS, JavaScript) |
| `nginx/` | Pengaturan Nginx |
| `database/`, `mongodb/` | Skema awal PostgreSQL dan pengguna awal MongoDB |
| `scripts/` | Skrip pengujian dan pengelolaan (`ctl.sh`, `funnel.sh`) |
| `tests/` | Unit test validasi |
| `docs/` | Dokumentasi arsitektur, keamanan, pengujian, dan akses publik |
| `bukti/` | Hasil pengujian dan screenshot |
| `laporan/` | Laporan (`laporan.docx`) dan slide presentasi |

Dokumentasi lanjutan ada di `docs/unified/` (arsitektur dua database, pengujian, keamanan, panduan demo) dan `docs/publik/` (akses dari internet).

## Catatan soal "alamat public"

PDF penugasan menyebut aplikasi dijalankan lokal tanpa perlu di-deploy ke cloud, tetapi bagian verifikasinya meminta aplikasi bisa dibuka lewat "alamat public". Kami menyediakan keduanya: alamat lokal `127.0.0.1:8081` dan alamat HTTPS lewat Tailscale Funnel. Arti pastinya masih perlu kami tanyakan ke dosen.
