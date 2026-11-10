# Hasil pengujian LibraryKu Unified (2026-11-10)

Semua pengujian dijalankan pada aplikasi yang berjalan (Nginx, Flask, PostgreSQL, MongoDB di Docker Compose, Kali VirtualBox), tanpa mock. Data uji diberi penanda `[UJI...]` dan dihapus; tiga buku asli (id 1, 2, 10) tidak diubah. Status: PASS, FAIL, NOT TESTED.

| # | Pengujian | Status | Bukti |
|---|---|---|---|
| 1 | Audit awal (source aktif = deployment, sumber daya, port) | PASS | `docs/unified/audit.md` |
| 2 | `docker compose up` tambahan: MongoDB dan backend NoSQL healthy, PostgreSQL tidak dibuat ulang | PASS | `bukti/unified/ctl_up_*.txt` |
| 3 | API SQL: health, CRUD, validasi (5 jenis), 404, bentuk JSON | PASS | `api_tests_*.txt` (87 pemeriksaan, 0 gagal) |
| 4 | API NoSQL: health, CRUD, id ObjectId 24 heks, validasi, 404, 400 id tidak valid | PASS | idem |
| 5 | Dua database tidak tercampur (aksi di satu sisi tidak mengubah sisi lain) | PASS | idem + UI |
| 6 | Kompatibilitas alamat lama `/api/health`, `/api/books` = isi `/api/sql/books` | PASS | idem |
| 7 | Respons galat berformat JSON (405, 404 rute NoSQL, 413, Content-Type salah) | PASS (NoSQL); SQL: 404/405 rute asing berformat HTML (bawaan Flask) | idem |
| 8 | Perubahan data benar-benar di database: dokumen MongoDB dan baris PostgreSQL dibaca langsung | PASS | `ctl_verify_20261110_181627.txt` |
| 9 | UI Firefox: mode SQL/NoSQL, CRUD kedua DB, pencarian, filter, dialog, Perbandingan, indikator database aktif | PASS (40 pemeriksaan) | `ui_firefox_fungsional.txt` |
| 10 | Ganti mode saat request SQL tertunda: respons lama tidak menimpa tampilan NoSQL | PASS | idem |
| 11 | Keyboard: panah kiri/kanan pada pilihan database, Tab, Escape, fokus dialog | PASS | `ui_firefox_keyboard_responsif.json` |
| 12 | Responsif: lima halaman tanpa overflow di Firefox 450 px (lebar minimum headless) dan zoom 200% | PASS | idem |
| 13 | MongoDB mati: API NoSQL 503 JSON (sekitar 3 dtk), SQL tetap 200 dan CRUD SQL jalan | PASS | `mongo_down_*.txt` |
| 14 | MongoDB mati: UI menampilkan galat jelas (header, dashboard, katalog, dialog, perbandingan), pindah ke SQL normal | PASS (8 pemeriksaan) | `ui_mongo_mati_firefox.txt` |
| 15 | MongoDB dinyalakan lagi: API pulih, dokumen tetap ada | PASS | `ctl_start-nosql_*.txt` |
| 16 | Persistensi: `down` lalu `up -d` tanpa `-v`; volume `postgres_data` dan `mongo_data` tetap; data SQL (4 baris) dan NoSQL (1 dokumen) identik sebelum dan sesudah | PASS | `ctl_restart-all_20261110_181951.txt` dan `..._182139.txt` (dijalankan dua kali, keduanya sama) |
| 17 | Regresi penuh setelah restart (API 87/87, keamanan 25/25, UI 40/40, unit test 14) | PASS | `api_tests_setelah_restart_*.txt`, dll. |
| 18 | Impeccable `detect` pada 5 rute (halaman ter-render) | PASS (0 temuan) | dijalankan 2026-11-10 |
| 19 | Kontras warna (aksen NoSQL #00684A, banner) | PASS (min. 6,8:1) | `contrast-check.py` |
| 20 | Unit test validasi dan ID (14 tes) | PASS | `tests/` |
| 21 | Keamanan terarah (25 pemeriksaan) dan XSS di UI | PASS | lihat `keamanan.md` |
| 22 | Waktu respons nyata di halaman Perbandingan (diukur browser, bukan benchmark) | PASS (fitur jalan); contoh sesi: median SQL sekitar 12-18 ms, NoSQL sekitar 4-9 ms | `ui_firefox_fungsional.txt` |
| 23 | Akses dari host Windows lewat NAT port forwarding | NOT TESTED oleh Claude (pengguna melaporkan berhasil) | `docs/akses-windows.md` |
| 24 | Postman, pembaca layar, layar sentuh, Chromium (skrip fungsional), Firefox lebar 390 px | NOT TESTED | - |
| 25 | Beban/benchmark (latensi, throughput) | NOT TESTED (sengaja tidak dibuat; tidak ada angka karangan) | - |

Catatan temuan selama pengerjaan: screenshot NoSQL pertama ternyata masih mode SQL karena pindah rute hanya mengganti hash; skrip screenshot diperbaiki dan semua gambar NoSQL diambil ulang dengan memuat ulang halaman. Tiga teks tetap yang menyebut PostgreSQL diganti agar mengikuti database aktif.

## Dokumen
Laporan DOCX (bagian 10) dan PPTX (slide 12-14) diperbarui 2026-11-10 dari bukti di atas. PDF laporan belum diekspor ulang. Tampilan DOCX/PPTX belum diperiksa secara visual.
