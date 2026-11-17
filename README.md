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
