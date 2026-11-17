# LibraryKu

Kami membuat LibraryKu untuk Project 1 mata kuliah Cloud Computing di Telkom University. Kasus yang kami ambil dari PDF penugasan adalah nomor 15, yaitu perpustakaan dengan Docker dan database SQL. PostgreSQL dipakai untuk proyek utama. MongoDB kami tambahkan supaya kedua database bisa dicoba dari satu website.

## Anggota kelompok

Kelas S1TT-KJ-23-04

| Nama | NIM |
|---|---|
| Muhammad Rafi Priyo Sembodo | 101072300038 |
| Atilla Pramudya Nugroho | 101072300039 |
| Muhammad Aprilio Rizal Arifin | 101072300040 |
| Aji Eka Saputra | 101072300071 |
| Panji Ramadhan | 101072330134 |

## Yang bisa dicoba

Di **Katalog**, cari buku berdasarkan judul atau penulis, atau pilih kategori yang mau dilihat. Untuk menambah, mengubah, atau menghapus buku, buka **Dashboard**. Pilihan **SQL / NoSQL** menentukan database yang dipakai. Koleksi di PostgreSQL dan MongoDB disimpan terpisah, jadi buku yang ditambahkan di satu mode tidak otomatis muncul di mode lain.

Menu **Peminjaman** hanya ada di mode SQL. Pilih buku, isi nama, kelas, NIM, dan tanggal pinjam, lalu tentukan batas pengembaliannya. Stok berkurang satu saat pinjaman dicatat. Ketika buku dikembalikan, klik **Kembalikan**. Tanggal pengembalian dicatat dan stok bertambah lagi.

> Login dimatikan pada konfigurasi bawaan repo. Orang yang bisa membuka demo dapat mengubah katalog serta melihat dan mengubah data peminjaman. Gunakan nama, kelas, dan NIM fiktif untuk demo.

## Menjalankan di komputer sendiri

Kami menjalankannya di Kali Linux pada VirtualBox. Yang dibutuhkan adalah Docker dan Docker Compose.

```bash
git clone https://github.com/muhrafi-fsdev/libraryku-unified.git
cd libraryku-unified
cp .env.example .env
```

Buka `.env` dan ganti `POSTGRES_PASSWORD`, `MONGO_ROOT_PASSWORD`, serta `MONGO_APP_PASSWORD` dengan kata sandi sendiri. Jangan commit file `.env`. Kalau pakai PowerShell, gunakan `Copy-Item .env.example .env` untuk menyalin file.

```bash
docker compose up -d --build
docker compose ps
```

Tunggu sampai backend dan database berstatus `healthy`, lalu buka [http://127.0.0.1:8081](http://127.0.0.1:8081). Jika Docker di Kali meminta izin, tambahkan `sudo` pada perintah `docker`.

- Untuk mengisi tiga buku contoh di PostgreSQL, jalankan `python3 scripts/seed_demo.py`.
- Kalau memakai volume PostgreSQL dari versi sebelum ada menu Peminjaman, jalankan `bash scripts/migrasi.sh` dari folder proyek aktif di Kali. Instalasi baru sudah membuat tabel peminjaman saat inisialisasi database.
- Untuk menghentikan aplikasi, gunakan `docker compose down`. Jangan tambahkan `-v` kalau data buku dan pinjaman masih dibutuhkan.

## Frontend, backend, dan API

Kode tampilan ada di [`frontend/`](frontend/). Nginx menampilkan halaman dan meneruskan permintaan API berdasarkan mode yang dipilih. Kode Flask untuk PostgreSQL ada di [`backend/`](backend/), sedangkan kode untuk MongoDB ada di [`backend_nosql/`](backend_nosql/). Database tidak membuka port langsung ke komputer host.

| Kalau mau… | Method | Path |
|---|---|---|
| Cek koneksi PostgreSQL | `GET` | `/api/sql/health` |
| Lihat daftar buku | `GET` | `/api/sql/books` |
| Lihat satu buku | `GET` | `/api/sql/books/{id}` |
| Tambah buku | `POST` | `/api/sql/books` |
| Ubah buku | `PUT` | `/api/sql/books/{id}` |
| Hapus buku | `DELETE` | `/api/sql/books/{id}` |
| Lihat riwayat peminjaman | `GET` | `/api/sql/loans` |
| Catat peminjaman | `POST` | `/api/sql/loans` |
| Kembalikan buku | `POST` | `/api/sql/loans/{id}/return` |

Untuk mencoba katalog MongoDB, ganti `/api/sql/` menjadi `/api/nosql/`. ID buku di PostgreSQL berupa angka. Di MongoDB, ID-nya berupa teks 24 karakter. Pada URL pengembalian, `{id}` adalah ID pinjaman, bukan ID buku.

Contoh menambah buku di PostgreSQL dari terminal:

```bash
curl -i http://127.0.0.1:8081/api/sql/books \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Requested-With: libraryku' \
  -d '{"title":"Dasar Jaringan Komputer","author":"Dina Lestari","category":"Teknologi","year":2022,"stock":5}'
```

Kalau berhasil, API mengembalikan status `201 Created` dan data buku yang baru disimpan. Halaman LibraryKu sudah mengirim header `X-Requested-With` saat menyimpan perubahan. Kalau pakai curl atau Postman, tambahkan header itu sendiri.

## Demo dan pengujian

[Buka demo LibraryKu](https://libraryku-kali.tail342a2f.ts.net/). Alamat demo bisa tidak aktif saat VM atau tunnel dimatikan. Cara menyiapkan akses dari luar ada di [panduan Tailscale Funnel](docs/publik/aktivasi.md).

Untuk menguji katalog di kedua database pada instalasi lokal, gunakan `python3 scripts/test_api.py`. Pengujian peminjaman ada di [`scripts/test_peminjaman.py`](scripts/test_peminjaman.py) dan perlu dijalankan pada stack uji terpisah, bukan database demo.

Kalau halaman terbuka tapi buku tidak muncul, cek `docker compose ps` dan `docker compose logs backend` untuk mode SQL, atau `docker compose logs backend-nosql` untuk mode NoSQL.

[Dokumentasi proyek](docs/) · [Bukti pengujian](bukti/) · [Laporan dan presentasi](laporan/)
