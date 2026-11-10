# Naskah Presentasi Project 1 Cloud Computing (sekitar 6 menit)

**Cara memakai:** ini bahan bicara, bukan teks yang dihafal. Ucapkan dengan kata-kata sendiri. Kalimat tentang hasil ("berhasil", "data tetap ada") hanya diucapkan **setelah** Anda benar-benar melihatnya di layar saat demo. Jika ada yang gagal, jangan dipaksakan: tunjukkan screenshot di slide 9 atau berkas `bukti/*.txt`, lalu jelaskan apa yang terjadi.

**Persiapan sebelum maju (2 menit sebelumnya):**
1. VM Kali menyala, `sudo docker compose ps` menunjukkan tiga service aktif.
2. Firefox terbuka di `http://localhost:8081`, sudah di-refresh paksa (Ctrl+Shift+R).
3. Tab kedua: `http://localhost:8081/api/health`. Tab ketiga: `http://localhost:8081/api/books`.
4. Terminal Kali terbuka di folder proyek. Postman, atau konsol Firefox (F12) dengan potongan dari `docs/panduan-bukti.md`.
5. Pastikan slide 9 sudah berisi screenshot asli (sebagai cadangan).

## 0:00 sampai 1:40 | Pembuka dan arsitektur (slide 1 sampai 5)

**Slide 1 dan 2.** "Selamat pagi. Kami membuat LibraryKu, website untuk mengelola koleksi buku perpustakaan. Kasusnya Perpustakaan, platformnya Docker, dan databasenya SQL, yaitu PostgreSQL. Kami demonstrasikan sekitar enam menit dengan urutan yang ada di slide ini."

**Slide 3 dan 4.** "Aplikasinya terdiri dari tiga service. Nginx menyajikan halaman dan meneruskan permintaan API. Flask adalah API-nya: memeriksa data lalu menjalankan SQL. PostgreSQL menyimpan datanya. Ketiganya berjalan sebagai container dan dihubungkan Docker Compose."

**Slide 5 (diagram).** "Ini hubungan antarkomponennya. Kami menjalankan semuanya di VM Kali Linux di VirtualBox. Di dalam VM, Docker membuat jaringan bridge bernama `app_network`. Hanya Nginx yang dibuka ke VM, lewat port 8081. Flask dan PostgreSQL tidak dibuka, jadi hanya bisa dijangkau dari dalam jaringan Docker. Datanya disimpan di volume `postgres_data`, supaya tidak hilang kalau container dimatikan."

## 1:40 sampai 3:30 | Demo website (slide 6)

"Sekarang kita lihat websitenya di Firefox pada VM ini, alamatnya `localhost:8081`."

**Urutan klik:**
1. **Beranda:** tunjukkan "Sekilas koleksi" (jumlah judul, total stok, kategori, tiga buku terbaru). Sebut bahwa angka ini diambil dari API, bukan tulisan statis.
2. **Tambah buku:** tekan *Tambah buku*, isi satu buku, *Simpan buku*. Tunjukkan buku muncul di atas dan angka di beranda ikut berubah.
3. **Cari dan filter:** ketik satu kata, lalu pilih satu kategori.
4. **Edit:** tekan *Edit* pada buku tadi, ubah stok, *Simpan perubahan*.
5. **Hapus:** tekan *Hapus*, jelaskan dialog konfirmasinya, lalu konfirmasi.

"Setiap tombol itu sebenarnya mengirim satu permintaan HTTP ke API. Itu yang kita lihat berikutnya."

## 3:30 sampai 4:40 | Demo API (slide 7)

"Sekarang API-nya kita buka langsung, tanpa website."

1. Tab `/api/health`: "Ini mengecek API dan koneksi ke database." Bacakan isi JSON yang tampil.
2. Tab `/api/books`: "Ini daftar buku dalam format JSON." Tunjuk `data` dan `total`.
3. Postman atau konsol Firefox: jalankan **POST**, **PUT**, lalu **DELETE** pada satu buku uji. Tunjukkan **status HTTP** tiap permintaan (201, 200, 200) dan JSON balasannya. Jika memakai konsol Firefox, panggilan `GET` terakhir akan menunjukkan 404 karena bukunya sudah dihapus.
4. Jika sempat: kirim data tidak valid (misalnya tahun 1800) dan tunjukkan **400** beserta pesan galatnya.

"Jadi websitenya hanyalah satu cara memakai API ini."

## 4:40 sampai 6:00 | Docker, masalah nyata, penutup (slide 8 sampai 10)

**Terminal:** jalankan `sudo docker compose ps`. "Tiga service jalan. Database dan backend berstatus healthy." Bila ada waktu: `./scripts/uji.sh docker` untuk menunjukkan port yang dibuka (hanya frontend) dan network.

**Slide 8 (masalah nyata).** "Satu kendala yang benar-benar kami alami: port 8081 sudah dipakai container proyek lain di VM ini. Kami periksa dengan `ss` dan `docker ps`, lalu memindahkan pemetaan frontend ke 8081. Proyek lain tidak kami hentikan, dan data PostgreSQL tidak disentuh."

**Persistensi (opsional, hanya jika sudah dilatih):** `./scripts/uji.sh persist`. "Skrip ini menambah satu buku uji, mematikan container tanpa `-v`, menyalakannya lagi, lalu memeriksa bukunya masih ada." Jangan pernah menjalankan `down -v` di depan dosen.

**Slide 10 (kesimpulan).** "Dari tugas ini kami belajar tiga hal. Network: service saling menemukan lewat nama di jaringan Docker. Storage: volume menjaga data database. API: Flask menerima permintaan HTTP dan membalas JSON. Aplikasi ini hanya dijalankan lokal untuk praktikum, tidak di-deploy ke cloud. Terima kasih."

## Pertanyaan yang mungkin muncul

**Kenapa Docker?** Supaya frontend, API, dan database terpisah dengan dependensinya masing-masing, tetapi tetap bisa dijalankan bersama dengan satu perintah.

**Kenapa PostgreSQL?** Datanya terstruktur (judul, penulis, kategori, tahun, stok), jadi cocok untuk database relasional. Ada aturan CHECK pada tabel, dan datanya mudah diperiksa dengan SQL.

**Apa fungsi Docker network?** Ketiga container berada di satu jaringan, sehingga Flask bisa mengakses `database:5432` memakai nama service, tanpa membuka port database ke luar.

**Apa fungsi volume?** Menyimpan isi database di luar siklus hidup container. Data tetap ada walau container dihentikan atau dibuat ulang. Kecuali volumenya dihapus dengan `down -v`.

**Apa bedanya port 8081 dan 5000?** 8081 adalah port di VM yang diteruskan ke Nginx (port 80 di container). 5000 dipakai Flask hanya di jaringan Docker dan tidak dibuka ke VM.

**Kenapa 8081, bukan 8081?** Di VM Kali, 8081 sudah dipakai container proyek lain. Pemetaan port ke 8081 menyelesaikannya tanpa mengganggu proyek itu.

**Apa itu REST API?** Cara mengakses data lewat URL dan method HTTP (GET, POST, PUT, DELETE) dengan JSON sebagai format datanya.

**Kenapa tidak diakses dari Windows?** VM memakai adaptor NAT tanpa port forwarding, jadi website dibuka dari Firefox di dalam VM. Jika dibutuhkan, bisa ditambah aturan NAT port forwarding di VirtualBox.

**Soal "alamat public" di PDF?** Petunjuk umum menyebut aplikasi dijalankan lokal tanpa cloud, sedangkan butir D.1 menyebut "alamat public". Kami mengikuti petunjuk umum dan menanyakan maksudnya ke dosen. Database dan Flask tidak kami buka ke internet.

**Apakah ini microservices penuh?** Ini pemisahan layanan frontend, API, dan database dalam container. API bisnisnya masih satu service, jadi lebih tepat disebut multi-container tiga lapis daripada banyak microservice bisnis. Sesuai fokus tugas, yang kami tekankan adalah Docker Compose, network, storage, dan komunikasi antarservice.

**Apakah datanya aman dari XSS atau SQL injection?** Perintah SQL memakai parameter, bukan menyambung string. Di halaman, teks buku ditulis dengan `textContent`, sehingga tidak ditafsirkan sebagai HTML.
