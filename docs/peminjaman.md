# Fitur Peminjaman dan Pengembalian Buku

Khusus mode SQL (PostgreSQL). Menu **Peminjaman** hanya muncul di mode SQL dan halamannya hanya bisa dipakai petugas.

## Cara kerja singkat
- Satu transaksi meminjam satu eksemplar. Saat dipinjam, stok buku berkurang satu; saat dikembalikan, stok bertambah satu. Keduanya terjadi dalam satu transaksi database bersama pencatatannya.
- Buku diambil dengan `SELECT ... FOR UPDATE`, jadi dua permintaan bersamaan tidak bisa sama-sama mengambil eksemplar terakhir. Pengembalian kedua untuk pinjaman yang sama ditolak (409) dan tidak menambah stok.
- Buku yang masih dipinjam tidak bisa dihapus (409). Setelah semua pinjamannya selesai, buku boleh dihapus dan riwayat tetap menyimpan judulnya (kolom `book_title`; `book_id` menjadi NULL).
- Tanggal aktual dikembalikan diisi otomatis saat petugas menekan Kembalikan, memakai tanggal hari ini di WIB (UTC+7).
- NIM disimpan sebagai teks (5 sampai 20 digit) sehingga nol di depan tidak hilang. Tidak ada denda, reservasi, notifikasi, atau akun mahasiswa.

## Berkas yang berubah
| Berkas | Isi |
|---|---|
| `database/migrations/002_peminjaman.sql` | Tabel `loans` (aman diulang, tidak menyentuh `books`) |
| `backend/app.py`, `backend/validation.py` | Endpoint peminjaman, validasi, pengecekan saat hapus buku |
| `nginx/default.conf` | Penjagaan login petugas untuk `/api/sql/loans` dan `/api/loans` |
| `compose.yaml` | Migrasi ikut dijalankan hanya pada volume database BARU |
| `frontend/index.html`, `frontend/app.js`, `frontend/style.css` | Menu dan halaman Peminjaman |
| `scripts/migrasi.sh` | Menerapkan migrasi ke database yang sedang berjalan |
| `scripts/uji_peminjaman.sh` dan skrip `test_peminjaman.py`, `run_ui_peminjaman.py` | Uji pada stack sementara |

## Endpoint (lewat Nginx; semua wajib login petugas, termasuk GET)
| Metode | Alamat | Fungsi |
|---|---|---|
| GET | `/api/sql/loans` | Riwayat peminjaman (terbaru di atas) |
| POST | `/api/sql/loans` | Catat peminjaman: `book_id`, `borrower_name`, `borrower_class`, `borrower_nim` (teks), `loan_date`, `due_date`, `note` (opsional) |
| POST | `/api/sql/loans/{id}/return` | Kembalikan buku |

Status penting: 201 dibuat, 400 data tidak valid, 401 belum login, 403 tanpa header `X-Requested-With`, 404 buku atau pinjaman tidak ada, 409 stok habis atau sudah dikembalikan, 503 tabel belum dimigrasi atau login petugas belum dikonfigurasi. Hapus buku yang masih dipinjam: `DELETE /api/sql/books/{id}` memberi 409.

## Akses petugas
Memakai mekanisme login yang sudah ada: Basic Auth Nginx dengan berkas `nginx/auth/htpasswd` (tidak masuk repositori, tanpa kredensial di kode). Browser meminta nama pengguna dan kata sandi saat halaman Peminjaman dibuka. Dashboard, Katalog, dan API katalog tetap publik.
- **Gagal tertutup:** bila `nginx/auth/htpasswd` tidak ada atau tidak terbaca, endpoint peminjaman membalas 503 dan permintaan tidak pernah sampai ke backend.
- Membuat akun petugas: `mkdir -p nginx/auth && printf 'petugas:%s\n' "$(openssl passwd -apr1 'KATA_SANDI_BARU')" > nginx/auth/htpasswd` lalu `./scripts/ctl.sh reload-nginx`.

## Menerapkan ke instalasi yang sudah berjalan (urutan)
1. `./scripts/migrasi.sh` (menambah tabel `loans`; data buku tidak berubah).
2. `sudo docker compose up -d --build backend` (API peminjaman aktif).
3. `./scripts/ctl.sh reload-nginx` dan segarkan browser dengan Ctrl+Shift+R.

Sebelum langkah 1, halaman Peminjaman menampilkan pesan bahwa tabel belum dibuat, dan hapus buku tetap berfungsi seperti biasa.

## Pengujian
`./scripts/uji_peminjaman.sh` membuat stack sementara (proyek Compose `libraryku-uji`, volume dan kata sandi fiktif sendiri, port 127.0.0.1:55081) dan menghapusnya lagi. Proyek asli dan datanya tidak disentuh.
