# LibraryKu | Panduan Kali Linux (VirtualBox)

Project menggunakan **Docker Compose** dan mempunyai tiga service: frontend Nginx, backend Flask, serta database PostgreSQL. Buka terminal di Kali Linux, bukan PowerShell Windows.

> **Catatan port:** panduan ini memakai port `8081` (alamat `http://localhost:8081`). Jika port 8081 di VM Anda bentrok (cek `sudo ss -ltnp | grep :8081`), pindahkan pemetaan frontend ke port bebas lain pada `compose.yaml`. Jangan menimpa `compose.yaml`, `.env`, atau `scripts/jalankan.sh` yang sudah disesuaikan di VM.

## Cara tercepat (satu skrip)

Setelah Docker terpasang (bagian A), cukup:

```bash
unzip LibraryKu_Kali_Linux_UIUX.zip
cd LibraryKu_Project1
./scripts/jalankan.sh
```

Skrip membuat `.env` dengan password acak jika belum ada (file `.env` yang sudah ada tidak pernah ditimpa), membangun dan menjalankan container, lalu menunggu sampai API menjawab. Setelah muncul tulisan "Siap", buka `http://localhost:8081`. Hentikan dengan `./scripts/jalankan.sh stop` (data database tetap tersimpan). Jika skrip tidak bisa dijalankan langsung, pakai `bash scripts/jalankan.sh`.

Langkah manual di bawah tetap berlaku bila Anda ingin mengatur sendiri.

## A. Siapkan Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose unzip
sudo systemctl enable --now docker
sudo docker --version
```

> Jalankan `sudo docker compose version` untuk memeriksa apakah subcommand Compose tersedia. Pada beberapa instalasi Kali, yang tersedia adalah perintah `docker-compose` (dengan tanda hubung). Gunakan salah satu yang berhasil.

## B. Buka arsip ZIP

Jika berkas ada di folder Downloads Kali Linux:

```bash
cd ~/Downloads
unzip LibraryKu_Kali_Linux_UIUX.zip
cd LibraryKu_Project1
cp .env.example .env
nano .env
```

Ganti `POSTGRES_PASSWORD` dengan password lokal yang kuat. Simpan di nano dengan `Ctrl+O`, `Enter`, lalu `Ctrl+X`.

## C. Jalankan aplikasi

Jika `sudo docker compose version` berhasil:

```bash
sudo docker compose up -d --build
sudo docker compose ps
```

Jika perintah tersebut tidak tersedia namun `docker-compose` berhasil:

```bash
sudo docker-compose up -d --build
sudo docker-compose ps
```

**Catatan kompatibilitas:** `compose.yaml` menggunakan `depends_on: condition: service_healthy`, yang membutuhkan Compose dengan dukungan kondisi kesehatan service. Jika Compose lama menolak berkas, pasang Docker Compose plugin versi baru sesuai dokumentasi resmi Docker untuk Debian, lalu gunakan `docker compose`.

Buka browser **di Kali Linux** pada `http://localhost:8081`. Tunggu sampai service siap dan uji tambah, edit, serta hapus buku.

## D. Screenshot untuk laporan

1. `sudo docker --version` dan versi Docker Compose.
2. `sudo docker compose ps` / `sudo docker-compose ps` saat tiga service aktif.
3. Tampilan `http://localhost:8081` dan operasi tambah/edit/hapus buku.
4. Respons `http://localhost:8081/api/books` berupa JSON.

## E. Troubleshooting singkat

- Docker service belum aktif: `sudo systemctl status docker`.
- Container restart/error: `sudo docker compose logs --tail=60` atau `sudo docker-compose logs --tail=60`.
- Port 8081 terpakai: cek `sudo ss -ltnp | grep :8081`.
- Keluar: `sudo docker compose down` (data PostgreSQL tetap tersimpan di volume).

Jangan gunakan `down -v` jika ingin mempertahankan data database.

## F. Uji dan bukti untuk laporan

```bash
./scripts/uji.sh docker     # bukti Docker, hanya membaca
./scripts/uji.sh api        # uji CRUD dengan satu buku uji (meminta konfirmasi)
./scripts/uji.sh persist    # uji data bertahan setelah restart (meminta konfirmasi, tanpa -v)
```

Hasil tersimpan di folder `bukti/`. Port dibaca dari Compose, jadi tetap benar bila Anda memakai 8081. Panduan lengkap beserta daftar screenshot: `docs/panduan-bukti.md`.
