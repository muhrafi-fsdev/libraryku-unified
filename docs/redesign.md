# LibraryKu V3: redesign landing page dan Dashboard (2026-11-06)

Hanya frontend yang berubah (`frontend/index.html`, `style.css`, `app.js`). Backend, database, `compose.yaml`, `.env`, port 8081, dan nginx tidak diubah. Backup frontend V2: `~/backup_frontend_v2_20261106-225706/` (juga `frontend.bak-sebelum-redesain/` untuk V1).

## Struktur website
Satu halaman HTML dengan rute hash: `#beranda`, `#katalog`, `#dashboard`, `#tentang` (satu tampilan aktif; judul tab, `aria-current`, dan fokus ke h1 mengikuti rute; hash tak dikenal diabaikan).

| Halaman | Isi |
|---|---|
| Beranda | Hero (judul fungsional + dua tombol: Jelajahi Katalog, Lihat Dashboard), rak buku yang punggungnya dibuat dari buku terbaru di database (slot kosong bergaris putus = belum ada buku, bukan data palsu), "Sekilas koleksi" (judul, stok, kategori dari API), "Koleksi terbaru" (kartu dengan pembatas buku berwarna kategori), "Untuk apa LibraryKu?", footer |
| Katalog | Pencarian judul/penulis, filter kategori, kartu dengan tahun terbit dan stok, empty state, skeleton, state galat. Tanpa tombol dan form pengelolaan |
| Dashboard | Ringkasan 3 angka, catatan jujur "belum memakai login", tabel buku, pencarian, filter, Tambah buku, Muat ulang; form tambah/edit di dialog modal; dialog konfirmasi hapus menyebut judul; toast sukses/galat; galat API tampil juga di dalam dialog |
| Tentang | Tujuan, fitur, teknologi, alur Nginx -> Flask -> PostgreSQL, peran Docker Compose, daftar endpoint API |

## Perubahan UI/UX utama
- CRUD dipindah dari halaman publik ke Dashboard; katalog menjadi tampilan baca saja.
- Identitas visual: serif editorial, satu aksen teal, rak buku dan pembatas buku sebagai motif perpustakaan; tanpa gambar stok, gradien, atau animasi dekoratif.
- Form menjadi dialog modal (fokus awal di judul, Escape/Batal menutup dan mengembalikan fokus ke tombol pemicu).
- Statistik ditampilkan sebagai satu baris angka, bukan deretan kartu.

## Skill yang benar-benar dipakai
`impeccable` 4.8.0 (detektor pada halaman aktual), `antislop-human` (pengecek kontras), `ui-ux-pro-max` (panduan UX tabel/empty state/konfirmasi, kueri sebelumnya). `frontend-design` tidak terpasang; `design` tidak dipakai (tidak ada kebutuhan logo/gambar). Playwright tidak terpasang; browser dikendalikan lewat Firefox Marionette (Firefox 140 ESR) dan Chromium headless.

## Hasil pengujian (aplikasi dan API asli, tanpa mock)
| Pemeriksaan | Status | Bukti |
|---|---|---|
| Beranda terbuka; 4 menu berfungsi (tampilan, judul, aria-current, fokus h1) | PASS (Firefox) | `v3/hasil_fungsional_firefox.txt` |
| Katalog = data PostgreSQL; tanpa tombol Tambah/Edit/Hapus dan tanpa form | PASS (Firefox) | idem |
| Form CRUD hanya di Dashboard | PASS (Firefox) | idem |
| Create 201, Update 200, Delete 200, GET id, validasi 5 galat, batal hapus | PASS (Firefox) | idem |
| Pencarian, filter, empty state, Hapus filter | PASS (Firefox) | idem |
| Statistik Beranda dan Dashboard = hitungan API; Katalog/Beranda memuat buku baru | PASS (Firefox) | idem |
| Refresh tidak menghilangkan data (persisten di PostgreSQL) | PASS | idem |
| Keyboard: Tab logis, outline fokus, Enter membuka dialog, Escape menutup dan fokus kembali, fokus tidak keluar dari modal | PASS (Firefox) | `v3/hasil_firefox_keyboard_responsif.json` |
| Responsif: tanpa overflow di Firefox 450 px dan zoom 200% (4 halaman); Chromium 360/390 px | PASS (overflow Chromium dinilai dari screenshot) | `v3/*.png` |
| Galat JavaScript | PASS (Firefox, sesi uji) | idem |
| Impeccable `detect` pada 4 rute | PASS (0 anti-pattern) | setelah perbaikan di bawah |
| Kontras warna baru (punggung buku, catatan, tag) | PASS (min. 5,26:1) | `contrast-check.py` |

## Bug dan masalah yang ditemukan dan diperbaiki
1. **Bug nyata (timer):** timer penanda baris dari simpan sebelumnya dapat mengosongkan `changedId` milik simpan berikutnya yang terjadi < 2,6 detik kemudian, sehingga filter tidak dibersihkan dan baris yang diubah tidak terlihat. Diperbaiki di `revealChanged()` dan alur simpan; 3 kali uji ulang, semua PASS.
2. **Impeccable: kicker di atas heading** (label kecil kapital): dihapus di semua halaman.
3. **Impeccable: lompatan heading** (h1 ke h3 di Katalog): judul kartu Katalog menjadi h2.
4. Urutan `dd`/`dt` pada ringkasan diperbaiki; warna punggung buku dipetakan agar kategori standar berwarna berbeda.

## Belum diuji / batasan
- Uji fungsional otomatis hanya di Firefox 140 ESR. Chromium: screenshot dan Impeccable saja, belum menjalankan ulang skrip fungsional.
- Firefox headless tidak mau lebih sempit dari 450 px; 390 px hanya di Chromium (screenshot).
- Pembaca layar, layar sentuh asli, Postman, dan galat 503 saat database mati: NOT TESTED.
- Dashboard TIDAK aman: belum ada login; memisahkan halaman hanya memisahkan tampilan.
- Laporan DOCX dan PPTX sudah diperbarui untuk V3 (2026-11-06) tetapi belum dibuka di Word/PowerPoint; PDF laporan belum diekspor ulang dan masih UI lama (tidak ada LibreOffice/Word di Kali).
- Tes memakai buku sementara `[UJI-V3]`; semuanya dihapus. Penghitung id PostgreSQL bertambah. Tiga buku asli (id 1, 2, 10) tidak berubah.
