# Checklist screenshot LibraryKu Unified

Semua gambar di `bukti/unified/screenshots/` diambil dari aplikasi nyata di Kali (Firefox 140 ESR, headless). Gambar tampilan mengubah data lewat API pada buku uji `[UJI] Cloud Computing Praktis`; tampilan membaca data dari database, dan buku uji sudah dihapus. Tidak ada gambar yang dibuat atau diubah secara manual. Screenshot **terminal** tidak bisa saya ambil; ambil sendiri dari terminal Anda (kolom "Perlu Anda").

| Kode | Isi | Berkas / sumber | Status |
|---|---|---|---|
| SS-01-Docker-Compose | `sudo docker compose ps`: lima container, health, hanya 8081 dibuka | **Perlu Anda**: jalankan `cd ~/LibraryKu_UIUX/LibraryKu_Project1 && sudo docker compose ps` lalu screenshot terminal. Teks asli sudah ada di `bukti/unified/ctl_restart-all_20261110_181951.txt` | Perlu Anda |
| SS-02-LibraryKu-Dashboard | Beranda, Katalog, Dashboard | `SS-02-beranda-sql.png`, `SS-02b-katalog-nosql.png`, `SS-03a-dashboard-sql.png`, `SS-04a-dashboard-nosql-kosong.png` | Ada |
| SS-03-PostgreSQL-CRUD | Dashboard mode SQL: Create, Update, Delete | `SS-03a-dashboard-sql.png`, `SS-03b-dashboard-sql-create.png`, `SS-03c-dashboard-sql-update.png`, `SS-03d-dashboard-sql-delete.png` | Ada |
| SS-04-MongoDB-CRUD | Dashboard mode NoSQL: dialog tambah, Create, Update, Delete | `SS-04d-dialog-tambah-nosql.png`, `SS-04b-dashboard-nosql-create.png`, `SS-04c-dashboard-nosql-update.png`, `SS-04e-dashboard-nosql-delete.png` | Ada |
| SS-05-API-JSON-SQL | JSON `/api/sql/books` dan health | `SS-05-api-json-sql.png`, `SS-05b-api-health-sql.png` | Ada |
| SS-06-API-JSON-NoSQL | JSON `/api/nosql/books` dan health | `SS-06-api-json-nosql.png`, `SS-06b-api-health-nosql.png` | Ada |
| SS-07-Database-Comparison | Halaman Perbandingan (data nyata + hasil ukur) | `SS-07-perbandingan.png` | Ada |
| SS-08-Galat-MongoDB-Mati | UI saat MongoDB mati | `SS-08-dashboard-nosql-mongo-mati.png`, `SS-08b-katalog-nosql-mongo-mati.png`, `SS-08c-perbandingan-mongo-mati.png` | Ada |
| SS-09-Verifikasi-Database | Isi dokumen MongoDB dan baris PostgreSQL langsung | **Perlu Anda**: `./scripts/ctl.sh verify` (ada dokumen uji hanya bila Anda membuatnya dulu), screenshot terminal. Teks asli: `ctl_verify_20261110_181627.txt` | Perlu Anda |
| SS-10-Persistensi | `restart-all`: volume tetap, data sebelum = sesudah | **Perlu Anda**: `./scripts/ctl.sh restart-all`, screenshot bagian "data SEBELUM"/"SESUDAH". Teks asli: `ctl_restart-all_20261110_181951.txt` | Perlu Anda |
| SS-11-Keamanan-Container | pengaturan container dan port | **Perlu Anda**: `./scripts/ctl.sh security`. Teks asli: `ctl_security_20261110_181049.txt` | Perlu Anda |
| SS-12-Mobile-Zoom | responsif dan zoom 200% | `SS-mobile450-dashboard.png`, `SS-mobile450-perbandingan.png`, `SS-zoom200-perbandingan.png` | Ada |

Catatan: ganti nama berkas sesuai kode di atas saat dimasukkan ke laporan; isi keterangan gambar harus jujur (Firefox headless, data dari database, perubahan lewat API pada buku uji).
