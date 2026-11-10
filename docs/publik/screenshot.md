# Checklist screenshot akses publik (ambil sendiri)

Jangan menampilkan kredensial, token, atau halaman admin yang memuat rahasia. Samarkan alamat IP pribadi.

| Kode | Isi | Cara |
|---|---|---|
| P-01-Funnel-Status | `./scripts/funnel.sh status` menunjukkan Funnel aktif dan URL publik | screenshot terminal |
| P-02-Android-Beranda | Beranda dari **data seluler** (ikon sinyal seluler terlihat, Wi-Fi mati), bilah alamat `https://...ts.net` dengan gembok | screenshot Android |
| P-03-Android-Katalog-NoSQL | Katalog mode NoSQL di Android | screenshot Android |
| P-04-Android-Login | Dialog login muncul saat Tambah/Edit/Hapus di Dashboard (tanpa mengisi kata sandi terlihat) | screenshot Android |
| P-05-Android-Tulis-Ditolak | Pesan "Perlu login untuk mengubah data" setelah login dibatalkan | screenshot Android |
| P-06-Android-CRUD-Berhasil | Dashboard sesudah login: buku uji berhasil ditambah lalu dihapus (tanpa menampilkan kata sandi) | screenshot Android |
| P-07-Sertifikat-TLS | detail sertifikat (penerbit, masa berlaku) dari browser | screenshot browser |
| P-08-Uji-Dari-Kali | `./scripts/funnel.sh check` | screenshot terminal |
| P-09-Kontrol-Akses | `python3 scripts/test_akses.py` (ringkasan 41 PASS) | screenshot terminal |
| P-10-Docker | `sudo docker compose ps` (lima container, hanya `127.0.0.1:8081`) | screenshot terminal |
Nama berkas: `P-xx-...png`. Cantumkan di laporan bahwa P-02 sampai P-06 diambil dari Android di luar jaringan rumah (data seluler).
