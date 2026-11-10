# Status Verifikasi Proyek

Diperbarui 2026-11-05 di **Kali Linux (VirtualBox)**. Jenis bukti: `REAL_RUNTIME` = dijalankan terhadap Nginx + Flask + PostgreSQL asli di `http://localhost:8081`; `MOCK_TEST` = API tiruan (riwayat dari Windows, bukan bukti integrasi); `SOURCE_CHECK` = pemeriksaan source. Bukti mentah ada di `bukti/pengujian/`, catatan lengkap di `docs/log-bukti.md`, status per butir tugas di `docs/matriks-persyaratan.md`.

## Hasil

| Bagian | Jenis bukti | Status | Bukti |
|---|---|---|---|
| Validasi data buku (`unittest`, 8 tes) | SOURCE_CHECK | PASS | 8/8 lulus (Kali) |
| Sintaks Python dan JavaScript | SOURCE_CHECK | PASS | `compileall`, `node --check` |
| API Create (POST) | REAL_RUNTIME | PASS | HTTP 201, `hasil_crud_api.txt` |
| API Read (daftar dan satu buku) | REAL_RUNTIME | PASS | HTTP 200 |
| API Update (PUT) | REAL_RUNTIME | PASS | HTTP 200 |
| API Delete | REAL_RUNTIME | PASS | HTTP 200, lalu GET 404 |
| API data tidak valid dan tidak ditemukan | REAL_RUNTIME | PASS | HTTP 400 dan 404 |
| `/api/health` (koneksi database) | REAL_RUNTIME | PASS | `database: connected` |
| UI baru (beranda, navigasi, katalog, CRUD, filter, pencarian, validasi, XSS) terhadap API asli | REAL_RUNTIME | PASS | `hasil_regresi_ui.txt`; butir Update yang semula PARTIAL diuji ulang dengan klik nyata: PASS (`hasil_update_ui_nyata.txt`; kegagalan lama adalah kesalahan skrip uji) |
| UI di Firefox 140 ESR (navigasi, pencarian, filter, CRUD, validasi, keyboard Tab/Enter/Escape, mobile 450 px, zoom 200%) | REAL_RUNTIME | PASS | `hasil_firefox.json`, `41-` sampai `45-firefox-*.png` |
| Penanganan galat API tambahan (404, 400, 405) | REAL_RUNTIME | PASS (404/405 rute asing berformat HTML: PARTIAL) | `hasil_api_tambahan.txt` |
| Akses dari host Windows | - | NOT TESTED | `docs/akses-windows.md` (butuh tindakan di Windows); "alamat public": NEEDS CLARIFICATION |
| Konsol browser tanpa galat | REAL_RUNTIME | PASS | `hasil_regresi_ui.txt` |
| Aksesibilitas (label, nama kontrol, skip link, h1, aria-current, `:focus-visible` dan reduced-motion di CSS) | REAL_RUNTIME (pemeriksaan program) | PASS | `hasil_regresi_ui.txt` |
| Responsif 360 dan 768 tanpa overflow; screenshot desktop dan mobile | REAL_RUNTIME | PASS | `10-` sampai `14-*.png` |
| Impeccable `detect` pada halaman aktual | REAL_RUNTIME | PASS | 0 anti-pattern, 2 catatan advisory |
| Screenshot Create/Update/Delete (`01-` sampai `03-`) | REAL_RUNTIME | PASS untuk **UI lama** | Diambil sebelum UI baru dipasang; perlu diambil ulang untuk UI baru |
| `docker compose ps` (tiga container), health, jaringan, volume, port, SQL baca-saja | REAL_RUNTIME | PASS | `bukti/kali/docker_20261105_221809.txt`: backend dan database healthy, hanya frontend dibuka (8081), 2 buku asli |
| Data bertahan setelah `down` lalu `up` (tanpa `-v`) | REAL_RUNTIME | PASS | `bukti/kali/persist_20261105_222432.txt`: 7 PASS, 0 FAIL; buku uji bertahan, volume `postgres_data` utuh; 2 buku asli tidak berubah |
| Keyboard nyata (Tab/Enter), Firefox, zoom 200%, pembaca layar, layar sentuh | - | NOT TESTED | - |
| Laporan DOCX (V3): deskripsi, tabel CRUD, hasil uji, masalah, screenshot 4 dan 5 | - | PARTIAL | Diperbarui 2026-11-06 untuk V3; masih kosong: anggota kelompok dan satu baris masalah lain. PDF BELUM diekspor ulang (tidak ada LibreOffice/Word di Kali). Tampilan di Word belum diperiksa |
| Slide PPTX (slide 2, 3, 6, 9, 11 diperbarui untuk V3) | - | PARTIAL | Tata letak dihitung dari koordinat, belum dilihat secara visual; kartu Docker slide 9 masih tanpa gambar |
| Bukti tambahan | REAL_RUNTIME | PASS | `15-`, `16-` (JSON di browser), `20-` sampai `23-` (CRUD di UI baru), `resp_*.json` |

## Pengujian yang harus dijalankan di Kali

Dari `~/LibraryKu_UIUX/LibraryKu_Project1`:

```bash
./scripts/uji.sh docker      # bukti Docker, hanya membaca (memakai sudo bila perlu)
./scripts/uji.sh persist     # menghentikan lalu menyalakan lagi container, tanpa -v; meminta konfirmasi
```

Hasil tersimpan di `bukti/`. Jangan menjalankan `docker compose down -v`.

## LibraryKu Unified (2026-11-10)
Dual database (PostgreSQL + MongoDB) diuji pada aplikasi nyata: API 87/87, keamanan terarah 25/25, UI Firefox 40/40, uji MongoDB mati 8/8, persistensi `down`/`up` tanpa `-v` PASS. Rincian dan yang NOT TESTED: `docs/unified/pengujian.md`. Laporan DOCX (bagian 10 baru) dan PPTX (slide 12 sampai 14) sudah diperbarui; PDF laporan BELUM diekspor ulang (masih versi lama) dan tampilan DOCX/PPTX belum dilihat secara visual (tidak ada LibreOffice/Word di Kali).

## Akses publik (2026-11-10)
Pengamanan aplikasi aktif dan teruji lokal (kontrol akses 41/41, API 87/87, keamanan 25/25, UI 40/40). Tailscale Funnel AKTIF di https://libraryku-kali.tail342a2f.ts.net/: baca publik, tulis anonim ditolak, dan CRUD dengan login lewat alamat publik lulus 41/41 (diuji dari dalam Kali). Akses dari Android lewat data seluler DILAPORKAN BERHASIL oleh pengguna (bukti screenshot milik pengguna); belum diuji setelah reboot: lihat `docs/publik/pengujian.md`.

Laporan DOCX (bagian 11 Akses Publik) dan PPTX (slide 15-16) diperbarui; PDF laporan masih belum diekspor ulang dan tampilan DOCX/PPTX belum dilihat secara visual.
