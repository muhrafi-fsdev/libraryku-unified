# Matriks Kesesuaian Teknis LibraryKu dengan PDF Project 1 (2026-11-05)

Status: PASS = terbukti oleh berkas di `bukti/pengujian/` atau `bukti/`; FAIL; PARTIAL; NOT TESTED; NEEDS CLARIFICATION = bergantung tafsir dosen. Pengujian di aplikasi asli (Nginx + Flask + PostgreSQL, Docker Compose, Kali VirtualBox, `http://localhost:8081`).

| Butir | Status | Bukti dan catatan |
|---|---|---|
| A. Website Flask, CRUD lengkap | PASS | CRUD API (`hasil_crud_api.txt`), UI Chromium (`hasil_regresi_ui.txt`, `hasil_update_ui_nyata.txt`), UI Firefox (`hasil_firefox.json`) |
| A.1 Create | PASS | POST 201 di API dan UI (Chromium dan Firefox) |
| A.2 Read | PASS | GET daftar dan per id 200 |
| A.3 Update | PASS | PUT 200; GET per id sama; UI terbukti dengan filter aktif, refresh, statistik (`hasil_update_ui_nyata.txt`) |
| A.4 Delete | PASS | DELETE 200, GET sesudahnya 404; dialog konfirmasi dengan mouse dan keyboard (Enter, Escape) |
| A.5 Validasi dan galat | PASS | 400 (kosong, tipe salah, bukan JSON, tanpa badan) dan 404 (PUT/DELETE/GET id tidak ada); lihat `hasil_api_tambahan.txt` |
| A.5 Konsistensi format galat | PARTIAL | Rute tak dikenal (`/api/tidakada`, id bukan angka) dan metode salah (405) membalas HTML bawaan Flask, bukan JSON. Tidak melanggar PDF; perbaikan butuh ubah backend dan restart container (belum dilakukan, menunggu izin) |
| A.5 Galat 503 saat database mati | NOT TESTED | Memerlukan mematikan database sementara (downtime) |
| B. Database SQL | PASS | PostgreSQL 16, tabel `books` dengan 5 CHECK, 2 baris (`docker_20261105_221809.txt`) |
| C.1 Deployment lokal Docker Compose | PASS | Tiga container up; backend dan database healthy; hanya 8081 dibuka |
| C.2 Jaringan Docker | PASS | Bridge `app_network`, DNS `database`, volume `postgres_data` |
| C.3 Data bertahan setelah `down` lalu `up` | PASS | `persist_20261105_222432.txt`: 7 PASS 0 FAIL |
| D.1 Alamat public | NEEDS CLARIFICATION | Localhost terbukti. Akses dari Windows: NOT TESTED (VM NAT; panduan di `docs/akses-windows.md`). Alamat internet tidak diterapkan dan tidak boleh tanpa autentikasi |
| D.2 Uji API lewat browser/Postman | PARTIAL | GET di browser (Chromium, `15-api-books-json.png`); POST/PUT/DELETE lewat curl dan UI. Postman NOT TESTED |
| D.3 Respons JSON aktual | PASS | `resp_*.json`, `hasil_crud_api.txt`, `hasil_api_tambahan.txt` |
| E. Demonstrasi 5 menit | PARTIAL | `docs/unified/demo.md` dan naskah siap; belum dilatih dengan stopwatch |
| Nomor kasus 15 (Perpustakaan, Microservices Docker, SQL) | NEEDS CLARIFICATION | Konfirmasi alokasi resmi kelompok oleh dosen/asisten |

## Antarmuka (tambahan di luar PDF)

| Butir | Status | Bukti dan catatan |
|---|---|---|
| Beranda, navigasi Beranda/Katalog/Tentang | PASS | Chromium dan Firefox 140 ESR (`hasil_firefox.json`) |
| Pencarian dan filter kategori | PASS | Firefox: "1 dari 2", tanpa hasil, filter, reset |
| Validasi form | PASS | 5 galat saat kosong, fokus ke kolom judul, galat tahun/stok |
| Keyboard Tab/Enter/Escape | PASS (Firefox) | Urutan Tab logis dari skip link; outline fokus terlihat; Enter membuka dialog hapus (fokus di dalam), Escape menutup dan fokus kembali ke tombol Hapus; hapus lewat keyboard berhasil |
| Mobile | PASS (Chromium 360/390, Firefox 450) | Tanpa overflow; Firefox headless tidak mau lebih sempit dari 450 px, jadi 390 px hanya di Chromium |
| Zoom 200% | PASS (Firefox) | Tanpa overflow, menu terlihat (`45-firefox-zoom200.png`) |
| Galat JavaScript | PASS (terbatas) | Tidak ada galat runtime saat sesi uji; semua sumber 200. Galat saat pemuatan awal tidak terekam oleh skrip uji |
| Impeccable pada halaman aktual | PASS | 0 anti-pattern |
| Pembaca layar, layar sentuh asli | NOT TESTED | - |
| Postman | NOT TESTED | - |

## Masalah tersisa

1. Akses dari Windows belum diuji: butuh tindakan Anda di Windows (`docs/akses-windows.md`).
2. "Alamat public" dan nomor kasus 15: butuh jawaban dosen.
3. Balasan 404/405 berupa HTML: perbaikan opsional, butuh izin (rebuild backend, downtime singkat).
4. Galat 503 belum diuji: butuh mematikan database sementara.
5. Laporan DOCX/PDF dan PPTX sengaja belum difinalkan sesuai instruksi; perlu disinkronkan dengan matriks ini kemudian.
