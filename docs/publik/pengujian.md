# Hasil pengujian akses publik (2026-11-10)

Status ditentukan oleh bukti. Pengujian lokal tidak dihitung sebagai bukti akses internet.

## A. Pengamanan aplikasi (lokal, di Kali): selesai
| Pengujian | Status | Bukti |
|---|---|---|
| Baca terbuka (7 endpoint dan halaman utama) | PASS | `bukti/publik/kontrol_akses_*.txt` |
| Tulis tanpa login ditolak (9 kombinasi metode x endpoint) -> 401 JSON + `WWW-Authenticate` | PASS | idem |
| Kata sandi salah dan nama pengguna salah -> 401 | PASS | idem |
| Login benar tanpa header aplikasi -> 403; POST ala form `text/plain` -> 400; preflight CORS lintas-origin tidak diizinkan | PASS | idem |
| Dengan login: Create 201, Update 200, Delete 200, data terhapus (SQL dan NoSQL) | PASS | idem |
| Pembatasan laju: rentetan percobaan login salah -> 429 JSON; 30 pembacaan cepat tetap normal | PASS | idem |
| Header keamanan lengkap pada respons 200, 401, dan 403; versi Nginx tersembunyi; badan 40 KB -> 413 | PASS | idem |
| Port: 8081 hanya di 127.0.0.1; tidak ada listener 27017/5432/5000 publik | PASS | idem (total 41 PASS, 0 FAIL) |
| Regresi API SQL + NoSQL dengan login | PASS (87/87) | `api_tests_setelah_auth_*.txt` |
| Uji keamanan terarah (injeksi, XSS, CSRF, CORS, port) | PASS (25/25) | `security_tests_setelah_auth2_*.txt` |
| Regresi UI Firefox (kredensial disuntikkan harness; dialog Basic Auth tidak bisa dijawab browser headless) | PASS (40/40) | `ui_firefox_fungsional_setelah_auth.txt` |
| Unit test | PASS (14) | `tests/` |
| Dialog login Basic Auth di browser sungguhan dan pesan setelah dibatalkan | NOT TESTED (perlu uji manual) | lihat `aktivasi.md` bagian E |

Satu bug ditemukan dan diperbaiki: `limit_except` pada Nginx melewati pengecekan header CSRF dan handler proxy sehingga tulis dengan login menghasilkan 500. Diganti dengan `auth_basic` berbasis variabel (nilai `off` untuk GET/HEAD); semua pengujian di atas dijalankan sesudah perbaikan.

## B. Akses publik (alamat: https://libraryku-kali.tail342a2f.ts.net/)
Funnel aktif sejak 2026-11-10 (diaktifkan oleh pengguna; `tailscale funnel status` menunjukkan `Funnel on`, `/` -> `http://127.0.0.1:8081`). Pengujian di bawah dilakukan **dari dalam Kali lewat alamat publik** (jalur Kali -> internet -> relay -> Kali). Ini bukti kuat bahwa alamat, sertifikat, dan kontrol akses berfungsi, tetapi **bukan bukti akses dari luar jaringan**.
| Pengujian | Status | Bukti |
|---|---|---|
| Tailscale terpasang (1.104.5), perangkat `libraryku-kali` login, `tailscaled` aktif dan aktif saat boot | PASS | `funnel_install_*.txt` |
| Funnel aktif dan alamat HTTPS publik | PASS (dilihat dari Kali) | `tailscale funnel status` |
| Sertifikat TLS: Let's Encrypt, CN = nama perangkat, berlaku 10 Nov 2026 sampai 8 Feb 2027; HTTP/2; HTTP port 80 tidak terjangkau | PASS (dari Kali) | dicek `openssl s_client`, `curl` |
| Baca publik: halaman, `/api/sql/*`, `/api/nosql/*` -> 200 | PASS (dari Kali) | `kontrol_akses_lewat_alamat_publik_*.txt` |
| Tulis anonim lewat alamat publik -> 401; tanpa header aplikasi -> 403 | PASS (dari Kali) | idem |
| CRUD dengan login lewat alamat publik (SQL dan NoSQL): 201, 200, 200 | PASS (dari Kali) | idem (41 PASS, 0 FAIL) |
| Header keamanan (HSTS, CSP, nosniff, X-Frame-Options) dan `WWW-Authenticate` sampai ke klien publik | PASS (dari Kali) | idem |
| **Akses dari Android lewat data seluler (bukan Wi-Fi yang sama)** | **PASS (dilaporkan pengguna, 2026-11-10)**: website terbuka dan berfungsi dari Android di luar jaringan lokal. Saya tidak mengamatinya langsung; screenshot P-02 sampai P-06 diambil pengguna untuk laporan | screenshot pengguna (belum disimpan di proyek) |
| Dialog login Basic Auth muncul di browser sungguhan (HP) | NOT TESTED | - |
| Funnel tetap aktif setelah reboot Kali | NOT TESTED | - |
| Cloudflare Tunnel + Access | NOT TESTED (belum ada domain; tidak dikerjakan) | - |
Catatan kecil: kontrol akses dijalankan dua kali (lokal dan lewat alamat publik), keduanya 41/41. Pada pengujian pertama lewat alamat publik 9 pemeriksaan tampak gagal karena skrip uji mencari nama header dengan huruf besar padahal HTTP/2 mengirim huruf kecil; skrip diperbaiki, aplikasi tidak berubah. Header `WWW-Authenticate` terkirim dua kali (satu dari `auth_basic`, satu dari konfigurasi tambahan); tidak berbahaya dan dapat dirapikan pada muat ulang Nginx berikutnya.
Akses internet dari Android data seluler dilaporkan berhasil oleh pengguna; bukti screenshot dilampirkan pengguna di laporan. Rincian yang belum dikonfirmasi: apakah dialog login Basic Auth muncul dan CRUD dengan login berhasil di Android (kolom di bawah tetap NOT TESTED sampai pengguna mengonfirmasi), dan Funnel setelah reboot.
