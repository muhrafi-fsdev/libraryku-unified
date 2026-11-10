# Panduan demonstrasi LibraryKu Unified (minimal 5 menit)

Kombinasi penugasan: **No. 15 (Perpustakaan, Microservices Docker, SQL)** adalah kombinasi resmi kelompok yang perlu dikonfirmasi dosen. **No. 16 (NoSQL)** didemonstrasikan sebagai pengembangan tambahan dalam aplikasi yang sama. Satu aplikasi dual-database tidak otomatis dihitung sebagai dua tugas resmi; sebutkan itu dengan jelas.

## Persiapan (10 menit sebelumnya)
1. Terminal di folder aktif: `cd ~/LibraryKu_UIUX/LibraryKu_Project1` dan `sudo docker compose ps` (lima container: empat healthy (database, backend, mongodb, backend-nosql), frontend running).
2. Firefox: tab 1 `http://localhost:8081`, tab 2 `http://localhost:8081/api/sql/books`, tab 3 `http://localhost:8081/api/nosql/books`.
3. Pastikan mode awal SQL dan data asli ada (3 buku). NoSQL boleh kosong (itu bagus untuk menunjukkan terpisahnya data).
4. Zoom browser 110-125%.

## Alur (sekitar 6 menit)
| Waktu | Layar | Aksi | Poin yang disampaikan |
|---|---|---|---|
| 0:00-0:40 | Beranda | Tunjuk hero, rak buku, "Sekilas koleksi" | Perpustakaan digital; angka dari database aktif (bukan data tetap) |
| 0:40-1:40 | Tentang (diagram) lalu terminal `docker compose ps` | Jelaskan Nginx -> dua Flask -> PostgreSQL/MongoDB; lima container, dua jaringan, dua volume, hanya 8081 terbuka | Microservices Docker, network, storage |
| 1:40-2:40 | Katalog | Cari judul, filter kategori, tunjukkan empty state | Read dan pencarian; tanpa tombol edit |
| 2:40-3:40 | Dashboard, mode **SQL** | Tambah buku, edit stok, hapus dengan dialog | CRUD ke PostgreSQL; indikator "Database aktif: PostgreSQL" |
| 3:40-4:40 | Dashboard, pilih **NoSQL** | Tampilan kosong (data terpisah); tambah buku, edit, hapus | CRUD ke MongoDB; id berupa ObjectId; data tidak disalin dari SQL |
| 4:40-5:20 | Tab JSON | Buka `/api/sql/books` dan `/api/nosql/books` | Bentuk JSON sama, beda tipe id |
| 5:20-6:00 | Perbandingan | Data nyata kedua DB, tabel perbedaan, tombol "Ukur sekarang" | SQL vs NoSQL; angka diukur nyata di browser, bukan benchmark |
| (opsional) | Terminal | `./scripts/ctl.sh verify` | Data benar-benar ada di PostgreSQL dan MongoDB; akses tanpa kredensial ditolak |

## Jika ditanya
- **Apakah Dashboard aman?** Belum: tidak ada login. Hanya memisahkan tampilan; gunakan di jaringan lokal.
- **Kenapa dua backend?** Memisahkan implementasi SQL dan NoSQL agar bisa dibandingkan; frontend memakai kontrak JSON yang sama.
- **Apa yang terjadi jika MongoDB mati?** NoSQL membalas 503 JSON dan UI menampilkan galat; mode SQL tetap normal (sudah diuji).
- **Apakah data bertahan?** Ya, volume `postgres_data` dan `mongo_data` tetap setelah `down` lalu `up` tanpa `-v` (sudah diuji). Jangan menjalankan `down -v`.
- **Angka performa?** Hanya hasil ukur nyata di halaman Perbandingan; bukan benchmark.

## Cadangan jika demo gagal
Tampilkan `docs/unified/pengujian.md`, screenshot di `bukti/unified/screenshots/`, dan berkas `bukti/unified/*.txt`; katakan itu rekaman pengujian sebelumnya, bukan demo langsung.

## Setelah demo
Hapus buku yang Anda tambahkan saat demo agar data asli tetap bersih (SQL: id 1, 2, 10; NoSQL: kosong).
