# Matriks Persyaratan Project 1 (Cloud Computing) vs LibraryKu

Sumber persyaratan: `Penugasan Project 1 (1).pdf` (dibaca langsung; teks identik dengan `Penugasan Project 1.pdf`).
Tanggal pemeriksaan: 2026-11-03. Lingkungan kerja pemeriksa: Windows 11 (bukan Kali). Docker Desktop di Windows mati dan kedua VM VirtualBox berstatus *poweroff*, jadi **tidak ada uji runtime asli yang dijalankan dari sini**.

**Arti status**

| Status | Arti |
|---|---|
| PASS | Terbukti oleh bukti pada kolom "Bukti" |
| PARTIAL | Kode/dokumen ada, tetapi bukti runtime asli belum lengkap |
| NOT TESTED | Belum diuji sama sekali; ada cara uji di kolom terakhir |
| FAIL | Diuji dan gagal |
| PERLU KLARIFIKASI | Butuh jawaban dosen/kelompok, bukan pekerjaan teknis |

**Jenis bukti** (rinciannya di `docs/log-bukti.md`): `SOURCE_CHECK` = membaca/menjalankan alat statis pada source. `MOCK_TEST` = UI diuji terhadap API **tiruan** (Node, bukan Flask/PostgreSQL), sehingga **bukan** bukti integrasi. `REAL_RUNTIME` = dijalankan di Docker asli. `LAPORAN_PENGGUNA` = disampaikan pengguna (screenshot praktik Kali) dan belum dilampirkan ke repositori.

## 1. Petunjuk Pengerjaan (A sampai E)

| Butir PDF | Lokasi implementasi | Bukti | Status | Pekerjaan berikutnya |
|---|---|---|---|---|
| **A.1 Create** | `backend/app.py` `create_book`; form di `frontend/index.html` | SOURCE_CHECK: unittest validasi 8/8 OK. MOCK_TEST: tambah buku lewat UI PASS. REAL_RUNTIME: tidak ada | PARTIAL | `./scripts/uji.sh api` (POST harus HTTP 201) lalu SELECT |
| **A.2 Read** | `list_books`, `get_book`; katalog + "Sekilas koleksi" | MOCK_TEST PASS. LAPORAN_PENGGUNA: dua buku tampil di Firefox Kali, status "Database terhubung" | PARTIAL | Simpan JSON asli `GET /api/books` (lihat `docs/panduan-bukti.md`) |
| **A.3 Update** | `update_book`; tombol Edit | MOCK_TEST PASS (termasuk kategori di luar dropdown). REAL_RUNTIME: tidak ada | PARTIAL | `./scripts/uji.sh api` (PUT harus 200, dibaca ulang) |
| **A.4 Delete** | `delete_book`; dialog konfirmasi | MOCK_TEST PASS. REAL_RUNTIME: tidak ada | PARTIAL | `./scripts/uji.sh api` (DELETE 200, lalu GET 404) |
| A.5 Validasi dan galat (400/404/503) | `backend/validation.py`, `handle_database_error` | SOURCE_CHECK: 8/8 tes validasi OK. MOCK_TEST: 400/404/502/503 ditampilkan benar di UI | PARTIAL | `./scripts/uji.sh api` menguji 400 dan 404 pada server asli; 503 hanya bisa diuji dengan mematikan container database (tidak dilakukan skrip) |
| **B. Database SQL** | `database/init.sql`; service `database` (`postgres:16-alpine`) pada `compose.yaml` | SOURCE_CHECK: skema `books` dengan CHECK. LAPORAN_PENGGUNA: database *Healthy* | PARTIAL | `./scripts/uji.sh docker` menampilkan `\d books` dan `SELECT` |
| **C.2 Docker network / Compose** | `compose.yaml`: bridge `app_network`; backend memakai `DB_HOST=database`; `nginx/default.conf` meneruskan `/api/` ke `backend:5000` | SOURCE_CHECK: hanya `frontend` yang memakai `ports`; `backend` hanya `expose`; `database` tidak dipublikasikan. LAPORAN_PENGGUNA: frontend Running, database dan backend Healthy | PARTIAL | `./scripts/uji.sh docker` (ps, network inspect, DNS `database`, jalur Nginx ke Flask) |
| Port 8080 bentrok dan pindah 8081 | `compose.yaml` pada VM Kali (diubah pengguna). **ZIP/folder Windows ini tetap 8080** | LAPORAN_PENGGUNA: 8080 dipakai `kali-compose-lab-web-1`; frontend dipindah ke 8081 | PARTIAL | Lampirkan screenshot `docker ps`/`ss` yang memperlihatkan konflik (jika masih ada). Jangan menimpa `compose.yaml` Kali |
| **D.1 Alamat public** | - | `localhost:8081` terbuka di Firefox guest Kali (LAPORAN_PENGGUNA). Diperiksa read-only lewat `VBoxManage showvminfo`: VM Kali memakai **NAT tanpa aturan port forwarding**, sehingga host Windows belum bisa mengakses guest | PERLU KLARIFIKASI DOSEN | PDF menyebut "localhost, tanpa cloud" (Petunjuk Umum) dan "alamat public" (D.1). Tanyakan maksudnya. Bila cukup akses dari host, ada perintah NAT forwarding di `docs/panduan-bukti.md` (belum dijalankan; perlu izin Anda) |
| **D.2 Uji API lewat browser/Postman** | Halaman *Tentang* memuat tautan GET `/api/health` dan `/api/books`; `scripts/uji.sh api` | Tidak ada | NOT TESTED | Peragakan di browser (GET) dan Postman atau konsol Firefox (POST/PUT/DELETE); snippet ada di panduan |
| **D.3 Respons JSON aktual di laporan** | Laporan bagian 5 dan 6 | Tidak ada. Laporan kini memuat slot bertanda "BELUM DIISI" untuk JSON aktual, bukan contoh yang disamarkan | NOT TESTED | Jalankan `./scripts/uji.sh api`, tempel isi `bukti/kali/api_*.txt` |
| **E. Demonstrasi lima menit** | `docs/naskah.md`, `laporan/presentasi.pptx` | Naskah dan slide diperbarui (Kali, 8081, alur demo). Belum dilatih, belum berisi screenshot asli | PARTIAL | Latihan dengan stopwatch; isi screenshot asli ke slide |

## 2. Laporan dan Dokumentasi (6 elemen)

| Elemen | Lokasi | Bukti | Status | Pekerjaan berikutnya |
|---|---|---|---|---|
| 1. Identitas | Sampul `laporan/laporan.docx` | Nama, NIM, kelas ada. PDF memuat baris **No. 15 = Perpustakaan, Microservices (Docker), SQL** (diverifikasi dari teks PDF) yang cocok dengan LibraryKu. Pembagian resmi kelompok belum dikonfirmasi; anggota lain belum diisi | PARTIAL / PERLU KLARIFIKASI | Konfirmasi nomor resmi ke dosen; isi anggota kelompok yang benar |
| 2. Deskripsi dan framework | Bagian 1 dan 2 laporan | Disinkronkan dengan UI baru (beranda, katalog, filter, tentang) | PASS (dokumen) | - |
| 3. Langkah deployment | Bagian 4 laporan | Ditulis ulang untuk Kali Linux VirtualBox, Docker Compose, port 8081, dan `scripts/uji.sh`. Screenshot konfigurasi belum ada | PARTIAL | Isi screenshot dari `docs/panduan-bukti.md` |
| 4. Endpoint API dan JSON | Bagian 5 laporan | Tabel endpoint sesuai `app.py`. JSON aktual belum ada | PARTIAL | Lihat D.3 |
| 5. Analisis VM/container, network, storage, API | Bagian 7 laporan | Ditulis ulang: VirtualBox VM (NAT) > Docker bridge > Nginx > Flask > PostgreSQL > volume | PASS (dokumen) | Tambahkan hasil `./scripts/uji.sh docker` sebagai bukti |
| 6. Masalah dan solusi | Bagian 8 laporan | Berisi masalah yang benar-benar terjadi (lihat `docs/log-bukti.md`), dipisah dari perkiraan | PARTIAL | Tambahkan masalah lain yang Anda alami di Kali bila ada |

## 3. Tambahan di luar PDF (permintaan pengguna)

| Butir | Lokasi | Bukti | Status | Catatan |
|---|---|---|---|---|
| Beranda, navigasi Beranda/Katalog/Tentang | `frontend/index.html`, `style.css`, `app.js` | MOCK_TEST: 36 pemeriksaan unik PASS; menu aktif mengikuti bagian halaman | PASS (tiruan) | Belum dicoba di Firefox |
| Statistik dan "terbaru" dari API | `renderSummary`, `renderRecent` | MOCK_TEST PASS (angka berubah setelah Create/Update/Delete) | PASS (tiruan) | Bukan data hardcode |
| Filter kategori | `syncCategoryFilter`, `filterBooks` | MOCK_TEST PASS (termasuk kategori di luar dropdown dan reset saat kategori hilang) | PASS (tiruan) | - |
| Cara menggunakan, Tentang, tautan API | `index.html` | SOURCE_CHECK | PASS | Teks hanya memuat fitur yang ada (tanpa peminjaman/login) |
| Keamanan tampilan (XSS) | `app.js` memakai `textContent`/`new Option` | MOCK_TEST: judul `<img onerror=...>` tampil sebagai teks | PASS (tiruan) | Tidak ada `innerHTML` |
| Responsif 360/390/768/1024/1366 | `style.css` | MOCK_TEST: tanpa overflow horizontal pada 360, 390, 768, 1024; target sentuh 44px pada HP | PASS (tiruan) | Firefox, zoom 200%, perangkat sentuh asli: NOT TESTED |
| Aksesibilitas | skip link, label, `aria-live`, `aria-current`, fokus terlihat | SOURCE_CHECK + MOCK_TEST sebagian | PARTIAL | Pembaca layar dan reduced-motion di browser: NOT TESTED |
| Data bertahan setelah `down` lalu `up` | volume `postgres_data` | Tidak ada | NOT TESTED | `./scripts/uji.sh persist` (meminta konfirmasi) |
| Database/Flask tidak terbuka ke host | `compose.yaml` | SOURCE_CHECK PASS | PARTIAL | Bukti runtime lewat `./scripts/uji.sh docker` ("TIDAK dibuka ke host") |

## 4. Prioritas

- **P0 (wajib dosen), tindakan Anda:** jalankan `./scripts/uji.sh docker`, `api`, `persist` di Kali, ambil screenshot, isi laporan dan slide, konfirmasi nomor kasus, tanyakan arti "alamat public".
- **P1 (selesai):** landing page, navigasi, statistik dari API, katalog dengan filter.
- **P2:** tidak ada yang ditambahkan selain filter kategori; sengaja tidak menambah peminjaman, login, atau paginasi.

## 5. Pembaruan di Kali Linux (2026-11-05): bukti REAL_RUNTIME

Menimpa kolom "Bukti" di atas untuk butir berikut; baris lama tetap sebagai riwayat. Bukti: `bukti/pengujian/`.

| Butir | Bukti REAL_RUNTIME | Status |
|---|---|---|
| A.1 Create | POST HTTP 201 (`hasil_crud_api.txt`); UI baru membuat buku dan statistik berubah (`hasil_regresi_ui.txt`) | PASS |
| A.2 Read | GET daftar dan satu buku HTTP 200; JSON aktual tersimpan | PASS |
| A.3 Update | PUT HTTP 200; di UI, total stok server berubah ke 1.109 | PASS (satu pemeriksaan teks baris UI PARTIAL) |
| A.4 Delete | DELETE HTTP 200, GET sesudahnya 404; dialog konfirmasi diuji | PASS |
| A.5 Validasi dan galat | 400 dan 404 pada server asli; validasi per kolom di UI | PASS (503 tidak diuji) |
| B. Database SQL | PostgreSQL 16 asli: `\d books` (5 CHECK) dan SELECT dua baris di `bukti/kali/docker_20261105_221809.txt` | PASS |
| C.2 Docker network / Compose | `bukti/kali/docker_20261105_221809.txt`: tiga container up, bridge `app_network`, DNS `database`, hanya 8081 dibuka | PASS |
| D.2 Uji API lewat browser/Postman | GET lewat curl dan browser terbukti; Postman belum | PARTIAL |
| D.3 JSON aktual untuk laporan | `bukti/pengujian/hasil_crud_api.txt` siap ditempel | PARTIAL (belum ditempel ke laporan) |
| Beranda, navigasi, statistik dari API, filter, cara pakai, Tentang | Diuji terhadap Flask + PostgreSQL asli di Chromium Kali; konsol bersih; Impeccable 0 anti-pattern | PASS (Chromium); Firefox NOT TESTED |
| Responsif | 360 dan 768 tanpa overflow; screenshot desktop dan mobile | PASS |
| Data bertahan setelah `down` lalu `up` | `bukti/kali/persist_20261105_222432.txt`: 7 PASS, 0 FAIL | PASS |
