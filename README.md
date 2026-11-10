# LibraryKu | Project 1 Cloud Computing

## Identitas kelompok
| Nama | NIM |
|---|---|
| Muhammad Rafi Priyo Sembodo | 101072300038 |
| Atilla Pramudya Nugroho | 101072300039 |
| Muhammad Aprilio Rizal Arifin | 101072300040 |
| Aji Eka Saputra | 101072300071 |

Mata kuliah Cloud Computing, Telkom University. Kelas: S1TT-KJ-23-04.
Kasus: **No. 15, Perpustakaan, Microservices (Docker), SQL (PostgreSQL)** menurut tabel pembagian pada PDF penugasan; nomor kelompok resmi dikonfirmasi ke dosen. Mode NoSQL (MongoDB, setara No. 16) adalah **pengembangan tambahan** dalam aplikasi yang sama dan tidak otomatis dihitung sebagai tugas kedua.
Repositori kode: https://github.com/muhrafi-fsdev/libraryku-unified
Pengumpulan (ketentuan dosen): file code, Dockerfile, dan laporan dikumpulkan lewat tautan GitHub ini. Laporan: `laporan/laporan.docx`.

## Menjalankan
1. Salin `.env.example` menjadi `.env`, lalu isi semua kata sandi dengan nilai acak (berkas ini tidak pernah di-commit). Buat juga `nginx/auth/htpasswd` untuk login dashboard (lihat `docs/publik/`).
2. Jalankan `docker compose up -d --build` dari folder proyek ini. Website: http://127.0.0.1:8081
3. Dokumentasi: `docs/unified/` (arsitektur SQL+NoSQL, pengujian, keamanan) dan `docs/publik/` (akses HTTPS publik).

**Usulan kasus No. 15: Perpustakaan • Microservices (Docker) • SQL (PostgreSQL)**

> Pastikan kombinasi kasus cocok dengan pembagian kelompok yang ditentukan dosen. Tabel pada PDF penugasan memuat baris No. 15 = Perpustakaan, Microservices (Docker), SQL, tetapi nomor resmi kelompok belum dikonfirmasi. Kode ini disiapkan untuk dijalankan secara **lokal**, bukan untuk penggunaan publik di internet.

> **Lingkungan praktik: Kali Linux di VirtualBox, port 8081.** Port 8080 di VM Kali dipakai container proyek lain, sehingga frontend LibraryKu dipetakan ke `8081:80`. `compose.yaml` pada folder ini sudah memakai **8081**. Status bukti ada di `docs/matriks-persyaratan.md`, `docs/log-bukti.md`, dan folder `bukti/pengujian/`; skrip bukti Kali adalah `scripts/uji.sh` (lihat `docs/panduan-bukti.md`).

## Yang sudah dibuat

- Website empat halaman (V3): **Beranda** (rak buku, sekilas koleksi, koleksi terbaru dari API), **Katalog** (cari judul/penulis, filter kategori, tanpa tombol pengelolaan), **Dashboard** (tambah, ubah, hapus buku lewat dialog, dengan konfirmasi hapus) dan **Tentang** (tujuan, teknologi, arsitektur, peran Docker Compose, tautan API). Membaca data terbuka; menambah, mengubah, dan menghapus data memerlukan login dashboard (Basic Auth di Nginx).
- API Flask dengan output JSON (GET, POST, PUT, DELETE) dan validasi input.
- Tiga container Docker Compose: **Nginx** (frontend + reverse proxy), **Flask** (API), **PostgreSQL** (SQL database).
- Volume PostgreSQL agar data tetap tersimpan walaupun container dihentikan.
- Skrip isi tiga buku contoh dan tes validasi sederhana.

## 1. Persiapan Windows (paling mudah)

1. Instal **Docker Desktop** dari [dokumentasi resmi](https://docs.docker.com/desktop/setup/install/windows-install/). Pilih backend WSL 2 apabila diminta. Aktifkan virtualisasi di BIOS jika sistem meminta. Instalasi WSL 2 jika belum ada dapat menggunakan PowerShell administrator: `wsl --install`; lakukan restart jika diminta.
2. Buka **Docker Desktop** dan pastikan status engine berjalan.
3. Buka PowerShell, periksa: `docker --version` dan `docker compose version`.
4. Ekstrak ZIP, buka folder `LibraryKu_Project1`.
5. Di folder tersebut, buat file `.env` dari `.env.example`:

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

   **Ganti** nilai `POSTGRES_PASSWORD` dengan password lokal buatan sendiri, lalu simpan. Jangan masukkan file `.env` ke GitHub.
6. Di terminal PowerShell dari folder yang berisi `compose.yaml`, jalankan:

   ```powershell
   docker compose up -d --build
   docker compose ps
   ```

7. Setelah tiga service siap, buka **http://localhost:8081**. Tampilan awal kosong sampai kamu memasukkan buku. Atau jalankan seeder pada langkah berikut.

   *Alternatif:* klik dua kali `START_WINDOWS.bat` setelah Docker Desktop aktif.

## 2. Isi contoh data agar siap demo

Dengan Python di host Windows (opsional):

```powershell
python scripts/seed_demo.py
```

Atau langsung tambahkan buku lewat formulir di website. Seeder dapat dijalankan ulang tanpa menambah judul contoh yang sama.

## 3. Uji API dari browser atau Postman

| Tujuan | Method | URL |
|---|---|---|
| Status koneksi | GET | `http://localhost:8081/api/health` |
| Daftar buku | GET | `http://localhost:8081/api/books` |
| Detail buku | GET | `http://localhost:8081/api/books/1` |
| Tambah buku | POST | `http://localhost:8081/api/books` |
| Ubah buku | PUT | `http://localhost:8081/api/books/1` |
| Hapus buku | DELETE | `http://localhost:8081/api/books/1` |

**Contoh JSON body untuk POST/PUT:**

```json
{
  "title": "Dasar Jaringan Komputer",
  "author": "Dina Lestari",
  "category": "Pendidikan",
  "year": 2022,
  "stock": 5
}
```

Di Postman pilih **Body → raw → JSON**, tempel payload di atas. Contoh respons sukses dari POST (ID dinamis):

```json
{
  "message": "Buku berhasil ditambahkan.",
  "data": {
    "id": 1,
    "title": "Dasar Jaringan Komputer",
    "author": "Dina Lestari",
    "category": "Pendidikan",
    "year": 2022,
    "stock": 5
  }
}
```

**Penting:** JSON di atas adalah contoh respons yang dirancang oleh API, **bukan bukti hasil uji aktual**. Untuk laporan, jalankan aplikasi dan ambil tangkapan layar dari komputer sendiri.

## 4. Perintah teknis penting

```bash
docker compose ps                  # melihat status container
docker compose logs --tail=100     # melihat log
docker compose logs backend        # log API Flask
docker compose down                # mematikan service, data database tetap ada
docker compose up -d              # menghidupkan kembali
docker compose down -v             # HATI-HATI: hapus volume dan semua data buku
```

## 5. Alternatif: Docker di dalam VirtualBox (Kali Linux)

Jika Docker Compose sudah terpasang di Kali Linux VM, ekstrak proyek ke Kali dan jalankan:

```bash
cp .env.example .env
nano .env
sudo docker compose up -d --build
sudo docker compose ps
```

Pada browser Kali buka `http://localhost:8081`. VM memakai **NAT**, sehingga Windows host belum bisa membuka alamat itu. Jika dosen memang meminta akses dari host, tambahkan aturan **VirtualBox → Settings → Network → Adapter 1 → Advanced → Port Forwarding** (VM dimatikan dulu), misalnya **TCP, Host IP `127.0.0.1`, Host Port `18081`, Guest Port `8081`**, lalu buka `http://127.0.0.1:18081` di Windows. Tanyakan dulu ke dosen apa yang dimaksud "alamat public" pada PDF (lihat catatan di bagian akhir).

Verifikasi dan pengambilan bukti dengan skrip (hasil tersimpan di `bukti/`):

```bash
./scripts/uji.sh docker     # container, health, port, network, volume, SELECT (hanya baca)
./scripts/uji.sh api        # POST, GET, PUT, GET, DELETE, GET dengan satu buku uji (meminta konfirmasi)
./scripts/uji.sh persist    # data bertahan setelah docker compose down tanpa -v (meminta konfirmasi)
```

Untuk memasang Docker Engine di Kali, ikuti dokumentasi resmi [Docker Engine Debian](https://docs.docker.com/engine/install/debian/) dengan perhatian khusus bagian distribusi turunan seperti Kali. **Jangan** secara otomatis memakai nama rilis `kali-rolling` sebagai codename repo resmi Debian.

## 6. Arsitektur & hubungan dengan materi kuliah

```text
Browser (localhost:8081)
           |
           v
    Nginx frontend (container)
           | /api/* HTTP/JSON
           v
     Flask API (container)
           | SQL/TCP 5432
           v
   PostgreSQL (container)
           |
           v
     Docker named volume
```

- **Container:** tiap komponen menjalankan proses dan dependensi terpisah.
- **Network:** Docker bridge `app_network` memungkinkan backend menemukan database menggunakan hostname `database`.
- **Storage:** volume bernama `postgres_data` menyimpan database secara persisten.
- **API:** frontend mengirim permintaan HTTP ke Flask; Flask mengembalikan respons JSON.
- **Port:** host 8081 diteruskan ke port 80 di container Nginx; backend dan database tidak dipublikasikan langsung ke host.
- **Istilah:** ini arsitektur *containerized three-tier* dengan pemisahan layanan frontend, API, dan database. Dalam pengertian arsitektur software yang ketat, satu API bisnis ini **belum** merupakan beberapa microservice bisnis independen. Untuk kebutuhan instruksi Project 1 yang menggolongkan Docker sebagai “Microservices”, stack ini menunjukkan pemisahan service dan komunikasi antarcontainer secara konkret.

## 7. Masalah umum dan penyelesaian

| Masalah | Langkah pemeriksaan |
|---|---|
| `docker` tidak dikenali | Jalankan Docker Desktop, cek `docker --version`; bila belum tersedia, instal Docker Desktop. |
| `Cannot connect to Docker daemon` | Pastikan Docker Desktop/daemon Docker sudah menyala. |
| Port 8081 telah dipakai | Cek `sudo ss -ltnp \| grep :8081`. Hentikan aplikasi lain tersebut, atau ubah `8081:80` pada Compose ke port bebas (misalnya `8082:80`) dan gunakan port itu. |
| Website terbuka, data gagal dimuat | `docker compose ps` lalu `docker compose logs backend` / `docker compose logs database`. |
| Login database gagal | Periksa nilai `.env`; perubahan password setelah volume terbentuk **tidak mengubah** password internal PostgreSQL secara otomatis. |
| Tabel `books` tidak ditemukan | Pastikan file `database/init.sql` ada saat volume pertama dibuat. Jangan menghapus volume sembarangan. |
| VM tidak bisa diakses dari Windows | Pastikan aturan VirtualBox NAT port forwarding dan tidak ada aplikasi lain di port host 8081. |

## 8. Checklist bukti penilaian

Sebagian besar bukti dihasilkan oleh `./scripts/uji.sh`; daftar screenshot lengkap beserta cara mengambilnya ada di `docs/panduan-bukti.md`.

- [ ] Screenshot Docker Compose `ps`: frontend/backend/database aktif dan health check sehat.
- [ ] Screenshot halaman website dan data tabel buku.
- [ ] Screenshot aksi Create (buku bertambah).
- [ ] Screenshot aksi Update (data buku berubah).
- [ ] Screenshot aksi Delete (baris terhapus).
- [ ] Screenshot endpoint GET `/api/books` menampilkan JSON di browser.
- [ ] Screenshot Postman atau browser API POST/PUT/DELETE bila dosen ingin melihat method.
- [ ] Jelaskan flow: browser → Nginx → Flask → PostgreSQL → volume.
- [ ] Ulangi `docker compose down` lalu `up -d`, pastikan data tetap ada.

## File laporan & presentasi

Lihat `laporan/laporan.docx`, `laporan/presentasi.pptx`, dan `docs/naskah.md` yang disertakan. **Laporan dan slide memuat kotak kuning "BELUM DIISI"** untuk screenshot dan JSON aktual yang hanya bisa diambil dari aplikasi yang berjalan. Isi dengan hasil asli (bukan contoh), lalu ekspor ulang PDF laporan.

## Catatan kecil pada instruksi tugas

PDF penugasan menyatakan aplikasi berjalan secara lokal (`localhost`) dan **tidak perlu di-deploy ke cloud**, tetapi di bagian verifikasi juga tertulis “alamat public”. Implementasi ini mengikuti petunjuk umum dan menampilkan alamat yang bisa diakses dari host (melalui port Docker/VM). Jika dosen memang mensyaratkan IP publik internet, klarifikasikan terlebih dahulu karena itu berbeda dari instruksi umum.

## LibraryKu Unified: SQL (PostgreSQL) + NoSQL (MongoDB)

Satu website, dua database terpisah, dipilih lewat pilihan **SQL / NoSQL** di Katalog dan Dashboard. Endpoint: `/api/sql/books` (PostgreSQL, alamat lama `/api/books` tetap berlaku) dan `/api/nosql/books` (MongoDB). Dokumentasi lengkap di `docs/unified/`:
`audit.md`, `arsitektur.md`, `pengujian.md`, `keamanan.md`, `demo.md`, `screenshot.md` (di folder `docs/unified/`). Operasi Docker dijalankan lewat `./scripts/ctl.sh` (bukti di `bukti/unified/`). Tambahkan `MONGO_ROOT_PASSWORD` dan `MONGO_APP_PASSWORD` ke `.env` (lihat `.env.example`). Penulisan data wajib login dashboard (kredensial di `~/.libraryku_dashboard_credentials`, bukan di repository); port 8081 hanya di `127.0.0.1`. Akses publik HTTPS lewat Tailscale Funnel: https://libraryku-kali.tail342a2f.ts.net/ (aktif; teruji dari Kali dan dilaporkan berhasil dari Android data seluler). Panduan di `docs/publik/` dan `./scripts/funnel.sh`.
