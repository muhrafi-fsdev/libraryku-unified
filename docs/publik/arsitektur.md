# Akses publik HTTPS LibraryKu Unified (Tailscale Funnel)

Status (2026-11-10): pengamanan aplikasi aktif dan teruji. Funnel **aktif**, alamat publik: **https://libraryku-kali.tail342a2f.ts.net/** (teruji dari dalam Kali lewat alamat publik; dilaporkan berhasil dari Android/data seluler oleh pengguna, lihat `pengujian.md`).

## 1. Arsitektur
```
HP / perangkat di luar jaringan rumah (data seluler)
   | HTTPS (443)
   v
Relay Tailscale Funnel (internet)
   | tunel terenkripsi (relay tidak dapat mendekripsi isi)
   v
tailscaled di Kali (mengakhiri TLS, sertifikat otomatis untuk *.ts.net)
   | HTTP ke 127.0.0.1:8081 (hanya di dalam Kali)
   v
Nginx (container frontend)  -- baca terbuka; tulis wajib login, header CSRF, pembatasan laju
   |-- /api/sql/*   -> Flask SQL   -> PostgreSQL
   |-- /api/nosql/* -> Flask NoSQL -> MongoDB
```

## 2. Keterkaitan VirtualBox, Kali, Docker, dan Nginx
- Windows menjalankan VirtualBox; VM Kali memakai jaringan NAT (`10.0.2.15`). **Tidak ada port forwarding, tidak ada pembukaan port di router, VirtualBox, atau Windows Firewall**: tailscaled di Kali hanya membuat sambungan KELUAR ke Tailscale.
- Di dalam Kali, Docker Compose menjalankan lima container. Hanya Nginx yang dipublikasikan ke host, dan kini hanya ke `127.0.0.1:8081` (bukan `0.0.0.0`). PostgreSQL, MongoDB, dan kedua backend tidak punya port ke host.
- Funnel meneruskan HTTPS publik ke `127.0.0.1:8081`. Yang dipublikasikan hanya satu layanan itu.

## 3. Cara kerja HTTPS dari internet
Pengunjung membuka alamat `https://...ts.net`. Nama itu menunjuk ke relay Tailscale. Relay membuka sambungan terenkripsi ke tailscaled di Kali, yang mengakhiri TLS dengan sertifikat yang diterbitkan otomatis untuk nama tersebut, lalu meneruskan permintaan ke Nginx. Karena TLS berakhir di Kali, relay tidak dapat membaca isi lalu lintas. Funnel hanya menerima HTTPS (port 443, 8443, atau 10000).

## 4. Pengamanan API CRUD
| Lapisan | Isi | Bukti uji |
|---|---|---|
| Baca publik (read-only) | GET/HEAD terbuka untuk semua pengunjung | `kontrol_akses_*.txt` |
| Tulis wajib login | POST/PUT/DELETE di `/api/sql`, `/api/nosql`, dan `/api/books` memakai Basic Auth Nginx; anonim, kata sandi salah, dan nama pengguna salah -> 401 JSON | idem (41 PASS) |
| Perlindungan CSRF | Tulis wajib header `X-Requested-With: libraryku` (tanpanya 403, walau login benar); POST ala form `text/plain` ditolak; preflight CORS lintas-origin tidak diizinkan | idem |
| Pembatasan laju | tulis 2 permintaan/detik (burst 5), baca 20/detik (burst 40); percobaan login salah ikut dibatasi (429 JSON + Retry-After) | idem |
| Validasi input | tipe ketat, ID MongoDB 24 heks, query berparameter; injeksi SQL/NoSQL dan XSS diuji | `security_tests_*.txt` |
| Tidak ada port internal terbuka | 8081 hanya di loopback; PostgreSQL, MongoDB, 5000 tidak terbuka | `kontrol_akses_*.txt` |
| Tanpa kebocoran | galat JSON generik; kredensial tidak diteruskan ke backend; header keamanan di semua respons | idem |
Kredensial dashboard ada di `~/.libraryku_dashboard_credentials` (izin 600, bukan di repository). Hash-nya di `nginx/auth/htpasswd` (di `.gitignore`).

## 5. Keterbatasan (jujur)
- Funnel tidak punya gerbang identitas seperti Cloudflare Access: siapa pun dengan alamatnya dapat **melihat** koleksi. Mengubah data tetap butuh login dashboard.
- Basic Auth dikirim di setiap permintaan tulis; aman karena selalu lewat HTTPS publik, tetapi kata sandi dibagikan manual (jangan di laporan atau screenshot).
- Semua pengunjung Funnel tampak berasal dari satu alamat di Nginx, sehingga pembatas tulis dipakai bersama (dapat dihabiskan satu orang; konsekuensinya hanya penolakan tulis sementara).
- Funnel memiliki batas bandwidth yang tidak dapat diatur.
- Akses publik hidup hanya selama komputer Windows, VirtualBox, VM Kali, Docker, dan internet menyala. Tidak ada janji uptime 24 jam.
- Nama perangkat Tailscale tercatat di log transparansi sertifikat publik.

## 6. Alternatif: Cloudflare Tunnel + Access (butuh domain)
Belum dipakai karena belum ada domain. Skrip `scripts/tunnel.sh` sudah tersedia. Urutan yang benar (dokumentasi Cloudflare): domain aktif di Cloudflare -> buat aplikasi Access (kebijakan email Anda dan dosen) -> baru buat tunnel dan rute hostname. Dengan Access, identitas pengunjung diperiksa sebelum permintaan sampai ke Nginx.
