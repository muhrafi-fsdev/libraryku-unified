# Catatan Bukti (EVIDENCE_LOG)

Tanggal: 2026-11-03. Pemeriksa bekerja di **Windows 11** (host), bukan di Kali. Dokumen ini hanya merekam yang benar-benar dijalankan. Tidak ada screenshot yang dibuat atau dimodifikasi untuk laporan.

| Jenis | Arti |
|---|---|
| `SOURCE_CHECK` | Membaca source, menjalankan alat statis atau tes tanpa database |
| `MOCK_TEST` | Diuji terhadap **API tiruan** (`mock_server.js`, Node, data di memori). Meniru kontrak API; **bukan** Flask, **bukan** PostgreSQL |
| `REAL_RUNTIME` | Dijalankan di Docker asli (Flask + PostgreSQL). **Belum ada** yang dihasilkan pemeriksa |
| `LAPORAN_PENGGUNA` | Disampaikan pengguna; belum dilampirkan |

## 1. Lingkungan pemeriksa

| Item | Keadaan |
|---|---|
| Docker Desktop Windows | Klien 29.6.1; **daemon tidak berjalan** (pipe `dockerDesktopLinuxEngine` tidak ada) |
| VirtualBox | VM "Rafi Priyo Kali Linux" dan "Rafi Priyo LM" terdaftar, **keduanya poweroff**. Tidak dinyalakan dan tidak diubah |
| Jaringan VM Kali (`VBoxManage showvminfo`, hanya baca) | `nic1=nat`, tanpa aturan port forwarding |
| Python / Node | Python 3.13.14; Node tersedia (mock server, `node --check`) |
| Browser | Browser pane aplikasi (Chromium, emulasi viewport) dan Microsoft Edge headless. **Firefox tidak diuji** |
| Skill | `impeccable` (detektor anti-pola, aturan *craft floor*) dan `ui-ux-pro-max` dimuat sesi ini. Skill `frontend-design` dan `libraryku-uiux` **tidak ada** di daftar skill terpasang sesi ini. Skrip pencarian `ui-ux-pro-max` tidak dijalankan |
| Alat dokumen | Microsoft Word dan PowerPoint (COM) tersedia |

## 2. SOURCE_CHECK

| Pemeriksaan | Hasil |
|---|---|
| `pdftotext -raw` pada PDF penugasan | Baris **15 = Perpustakaan, Microservices (Docker), SQL** terbaca. Dua berkas PDF isinya identik |
| `python -m unittest discover -s tests -v` | **8 tes, OK** (validasi buku; tanpa database) |
| `ast.parse` backend/app.py, validation.py, scripts/seed_demo.py | OK |
| `node --check frontend/app.js` | OK |
| ID HTML ganda; ID yang dipakai `app.js` ada di HTML | Tidak ada ID ganda; semua ID ditemukan |
| Pencarian `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval` di `app.js` | Tidak ada |
| `compose.yaml`: yang memakai `ports` | Hanya `frontend` (`8080:80` pada salinan Windows ini). `backend` hanya `expose: 5000`; `database` tidak dipublikasikan |
| Detektor `impeccable`, halaman terender | 1280, 1024, 768: **0 temuan**. 390 dan 360: 1 temuan *clipped-overflow-container* pada `.catalog` (**false positive diterima**: `overflow: hidden` untuk sudut membulat tabel, isinya hanya ikon pencarian) |
| Detektor `impeccable`, analisis statis | 2 temuan *cramped-padding* pada `hero`/`howto`: penganalisis tidak bisa menghitung `clamp()`; jarak sebenarnya 16 sampai 56px dan terbukti bersih pada pemindaian terender (**false positive diterima**) |

## 3. MOCK_TEST (UI terhadap API tiruan)

Seluruh bagian ini **bukan** bukti integrasi Flask/PostgreSQL.

**Rangkaian fungsi (browser pane, emulasi 1366×900), 36 pemeriksaan unik lulus**: status koneksi, ringkasan 4/1.213/4, tiga buku terbaru berurutan, opsi filter dari data, filter kategori + hitungan, pencarian, keadaan tanpa hasil + tombol "Hapus filter", Create/Update/Delete lewat UI, kategori di luar dropdown (`Sains`) tetap terpilih saat edit, filter ter-reset saat kategorinya hilang, injeksi HTML tampil sebagai teks (`window.__xss` tidak terdefinisi), tombol hero, menu aktif untuk Beranda/Katalog/Tentang, judul seksi tidak tertutup header sticky, tautan API membuka tab baru dengan `rel=noopener`, status galat lalu pulih. **Regresi akhir setelah semua perubahan CSS: 10/10 PASS.**

**Keadaan gagal pada muat pertama:** 503 (DB mati), 502 (gateway berisi HTML), dan "Coba lagi" setelah layanan pulih: ketiganya sesuai.

**Putaran pertama 25 PASS, 5 FAIL. Hasil analisis, bukan disembunyikan:**
- 1 FAIL (H1) kesalahan skrip uji saya (daftar belum disegarkan setelah menghapus buku XSS via API).
- 4 FAIL (G1 sampai G4: scroll dan penanda menu) **disebabkan browser pane tidak merender frame saat tidak difokus**: `requestAnimationFrame` dan `IntersectionObserver` terukur tidak berjalan; setelah tab difrontkan, animasi smooth-scroll tetap sangat lambat. Pemeriksaan diulang dengan scroll instan di dalam skrip uji, dan semuanya lulus.
- **Yang tidak dapat dinilai di pane ini: kehalusan animasi smooth-scroll.** Yang terbukti hanyalah logikanya.

**Responsif:** tanpa overflow horizontal pada 360, 390, 768, dan 1024 (lebar dokumen = lebar viewport, selisih hanya lebar scrollbar). Tangkapan layar Edge headless 1366, 1024, 768 diperiksa mata. Pada 360 dan 390 tidak ada kontrol interaktif di bawah 44px (setelah perbaikan di bawah).

### Cacat nyata yang ditemukan pengujian dan sudah diperbaiki

1. **Navigasi meluber di HP (≤720px).** Saya menulis `order`/`flex-basis` untuk menaruh navigasi di baris kedua tetapi lupa `flex-wrap: wrap`; halaman melebar dan Chrome mobile melaporkan `innerWidth` 641 sampai 656. Terdeteksi dari angka viewport yang janggal, diperbaiki.
2. **Regresi akibat "perbaikan" detektor.** Mengganti pola sembunyi-visual pada `thead` dengan `clip-path` membuat teks header memperlebar halaman (408px). Dikembalikan ke `overflow: hidden` + `clip`, dengan komentar alasan di CSS.
3. Tautan API 21px tingginya (di bawah target sentuh): diberi tinggi 44px pada layar sempit.
4. Placeholder pencarian terpotong ("kategor"), tombol "Muat ulang" jatuh sendirian ke baris kedua pada 768px, kotak kode alamat API melebar, judul hero 3 baris: semuanya dirapikan.
5. (Sesi sebelumnya) Buku dengan kategori di luar dropdown (mis. `Sains` dari Postman) tidak bisa disimpan saat diedit; diperbaiki dengan opsi dinamis dan kini diuji ulang.

**Potongan konsol Firefox pada `docs/panduan-bukti.md`** dijalankan terhadap mock di browser pane: POST 201, PUT 200, GET 200, DELETE 200, GET 404, jumlah buku kembali seperti semula. Versi pertama potongan itu **salah** (membaca badan respons dua kali, akan melempar *body already used*); diperbaiki sebelum dipublikasikan.

### Dokumen (SOURCE_CHECK)

| Pemeriksaan | Hasil |
|---|---|
| Laporan DOCX dibuka di Microsoft Word (COM), diekspor ke PDF, tiap halaman dirender dan dilihat | 8 halaman, 13 tabel, 1 gambar; tanpa galat saat dibuka |
| Cacat yang ditemukan saat render dan sudah diperbaiki | Backtick dan tanda `*` tampil mentah pada judul kotak kuning dan teks; kotak kuning lebih lebar daripada tabel lain |
| Presentasi PPTX dibuka di PowerPoint (COM), semua slide diekspor ke PNG dan dilihat | 10 slide; satu label diagram menimpa garis tepi, diperbaiki |
| Sisa angka 8080 pada laporan dan slide | Hanya pada penjelasan masalah port 8080 bentrok (disengaja) |
| Diagram arsitektur (`laporan/diagram.png`) | Dibuat dari `compose.yaml` dan `nginx/default.conf`; **diagram, bukan tangkapan layar** |
| Screenshot di laporan dan slide | **Tidak ada yang dibuat.** Semua slot bertanda kuning "BELUM DIISI" |

**Kesalahan proses yang saya buat selama pengujian dokumen (dicatat agar tidak membingungkan):** gambar halaman yang saya lihat sempat basi karena skrip render terpotong oleh `Select-Object -First 2`; diketahui dari perbandingan waktu tulis berkas dan diulang.

## 4. MOCK_TEST skrip `scripts/uji.sh`

Dijalankan dari salinan di folder sementara. Mode `api` melawan mock; mode `docker` dan `persist` memakai **`docker` palsu** yang hanya mencatat argumen. Ini menguji *alur skrip*, **bukan** Docker/PostgreSQL.

| Skenario | Hasil |
|---|---|
| `api --yes` (mock sehat) | exit 0; 24 PASS, 0 FAIL; jumlah buku kembali seperti semula |
| `api` dengan jawaban `n` | exit 0; "Dibatalkan"; tidak ada permintaan dikirim |
| `api` dengan jawaban `y` | exit 0; 24 PASS |
| Server mati (port 1) | exit 1; 9 FAIL; tidak menggantung, tidak ada sisa data |
| Database mati (mock 503) | exit 1; 9 FAIL; jumlah buku tidak berubah |
| `docker` dengan docker palsu | exit 0; backend dan database dilaporkan "TIDAK dibuka ke host" |
| `persist --yes` dengan docker palsu | exit 0; 7 PASS; urutan `down` lalu `up` |
| Tanpa argumen | exit 2 dan teks bantuan |
| Semua perintah `docker` yang dipanggil skrip | Tidak ada `-v`, `--volumes`, `rm`, `prune`, `stop`, `kill` |

**Tidak teruji:** jalur pembersihan (`trap EXIT`) saat skrip terputus di tengah (mis. Ctrl+C setelah POST); perilaku `sudo` di Kali; `docker-compose` v1.

## 5. REAL_RUNTIME

**Tidak ada yang dijalankan pemeriksa.** Daftar yang menunggu Anda di Kali ada di `docs/panduan-bukti.md`.

## 6. LAPORAN_PENGGUNA (belum dilampirkan)

- Docker berjalan di Kali; database dan backend *Healthy*, frontend *Running*.
- Firefox Kali membuka `http://localhost:8081`: dua buku dan "Database terhubung".
- Port 8080 bentrok dengan container proyek lain (`kali-compose-lab-web-1`); `compose.yaml` dan skrip di Kali diubah ke 8081.

## 7. Paket untuk Kali (SOURCE_CHECK)

`LibraryKu_Patch_Frontend.zip` (26.838 byte, 6 berkas): `frontend/` (3 berkas), `scripts/uji.sh`, `docs/panduan-bukti.md`, `BACA_INI.txt`. Diverifikasi: zip utuh; path memakai `/`; `scripts/uji.sh` berizin 0755 dan tanpa CR; **tidak memuat** `compose.yaml`, `scripts/jalankan.sh`, `.env`, `backend/`, `database/`, `nginx/`; hash SHA-256 berkas di zip sama dengan sumber proyek; `scripts/uji.sh` di zip identik dengan salinan yang diuji pada bagian 4; hasil ekstrak lolos `node --check` dan `bash -n`.

Perubahan CSS/HTML terakhir setelah rangkaian fungsi (placeholder pencarian dan basis lebar kolom pencarian) diverifikasi dengan pengukuran tata letak pada 768 dan 1366 piksel, **bukan** dengan menjalankan ulang seluruh rangkaian fungsi.

Yang **tidak** dilakukan dari sesi ini: menyalakan VM Kali atau Docker Desktop, menyentuh `compose.yaml`/`.env`/port/volume, menambah aturan NAT port forwarding, dan membuat screenshot untuk laporan.
