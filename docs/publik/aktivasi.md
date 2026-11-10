# Langkah aktivasi dan pengoperasian akses publik

> **Pembaruan (mode terbuka):** nama pengguna dan kata sandi untuk menambah, mengubah, dan menghapus data **sudah dicabut** atas permintaan pemilik proyek. Penulisan kini hanya dilindungi header `X-Requested-With` (CSRF), pembatasan laju 10 permintaan/detik (burst 20), batas badan 16 KB, dan validasi backend. Akibatnya siapa pun yang tahu alamat publik dapat mengubah data. Untuk mengaktifkan login lagi: di `nginx/default.conf` ganti `default off;` pada `map $request_method $auth_realm` menjadi `default "LibraryKu Dashboard";`, pastikan `nginx/auth/htpasswd` ada, lalu `./scripts/ctl.sh reload-nginx`. Bagian di bawah yang menyebut login menggambarkan keadaan sebelum perubahan ini.


Semua perintah dari folder proyek aktif (bukan salinan di Unduhan):
`cd ~/LibraryKu_UIUX/LibraryKu_Project1`

## A. Sudah dikerjakan dan teruji
1. `./scripts/ctl.sh apply-frontend` dan `./scripts/ctl.sh reload-nginx`: Nginx baru aktif (tulis wajib login, header CSRF, pembatasan laju), port 8081 hanya di `127.0.0.1`.
2. `python3 scripts/test_akses.py`: 41 PASS, 0 FAIL.

## B. Pasang dan hubungkan Tailscale
1. `./scripts/funnel.sh install` (skrip instalasi resmi tailscale.com; menambah repositori apt dan mengaktifkan `tailscaled` saat boot).
2. `./scripts/funnel.sh login` lalu buka URL yang dicetak di browser, masuk ke akun Tailscale, setujui perangkat `libraryku-kali`.

## C. Pengaturan di https://login.tailscale.com/admin
1. DNS: pastikan **MagicDNS** aktif dan aktifkan **HTTPS Certificates** (membuat sertifikat untuk `*.ts.net`).
2. Izin Funnel: saat `enable` pertama, Tailscale mencetak tautan untuk mengaktifkan Funnel pada perangkat (atribut `funnel` di kebijakan tailnet). Ikuti tautan itu.

## D. Aktifkan Funnel
`./scripts/funnel.sh enable`. Skrip menolak jika tulis anonim belum 401 dan meminta konfirmasi. Catat URL publik yang dicetak. Cek dari Kali: `./scripts/funnel.sh check` (hanya bukti pendukung).

## E. Uji dari luar jaringan (bukti PASS)
Alamat saat ini: https://libraryku-kali.tail342a2f.ts.net/

Di Android, **matikan Wi-Fi, pakai data seluler**, buka URL publik:
1. Beranda dan Katalog tampil (gembok HTTPS, sertifikat valid).
2. Pindah SQL / NoSQL di Katalog; data sesuai.
3. Dashboard: tombol Tambah buku -> browser meminta login; batalkan -> muncul pesan "Perlu login". Masuk dengan kredensial -> tambah, edit, hapus buku uji berhasil; hapus buku ujinya.
Ambil screenshot sesuai `screenshot.md`. Jangan menampilkan kredensial.

## F. Mengambil kredensial dashboard (hanya untuk Anda)
`cat ~/.libraryku_dashboard_credentials` (di terminal Anda; jangan ditempel ke chat, laporan, atau screenshot). Memberi akses ke dosen: kirim langsung secara pribadi, dan ganti setelah penilaian (hapus berkas lalu buat ulang: `rm ~/.libraryku_dashboard_credentials nginx/auth/htpasswd` dan minta saya membuat ulang).

## G. Setelah Kali di-reboot
- Container Docker memakai `restart: unless-stopped` dan Docker aktif saat boot, jadi LibraryKu naik sendiri; periksa `sudo docker compose ps`.
- `tailscaled` aktif saat boot. Periksa `./scripts/funnel.sh status`. Jika Funnel tidak aktif, jalankan `./scripts/funnel.sh enable` lagi. (Perilaku setelah reboot belum diuji; uji dengan reboot lalu `status`.)
- Komputer Windows, VirtualBox, dan VM harus menyala agar website online.

## H. Menghentikan akses publik
`./scripts/funnel.sh off`. Website lokal (`http://127.0.0.1:8081`) dan Docker tidak terpengaruh.

## I. Mengembalikan akses NAT/LAN lama (tidak disarankan)
Tambahkan `FRONTEND_BIND=0.0.0.0` di `.env`, lalu `./scripts/ctl.sh apply-frontend`. Penulisan tetap butuh login.

## J. Pemecahan masalah
- Halaman tidak terbuka di HP: pastikan `./scripts/funnel.sh status` menunjukkan Funnel aktif dan Kali punya internet; cek `./scripts/funnel.sh logs`.
- `enable` menolak: jalankan `./scripts/ctl.sh apply-frontend`.
- Dashboard menampilkan "Perlu login": masukkan nama pengguna dan kata sandi dashboard di dialog browser.
- 429: terlalu banyak permintaan tulis; tunggu beberapa detik.
