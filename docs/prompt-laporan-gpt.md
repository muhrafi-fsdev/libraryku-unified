# Prompt untuk GPT: laporan Project 1 Cloud Computing (LibraryKu)

Salin seluruh isi di dalam blok di bawah ke GPT. Lampirkan juga PDF "Penugasan Project 1" bila GPT mendukung unggah berkas. Screenshot dari `bukti/laporan/` ditempel sendiri ke Word di tempat yang ditandai `[SCREENSHOT: ...]`.

~~~
PERAN
Kamu asisten penulis laporan praktikum mahasiswa Teknik Telekomunikasi (Telkom University), mata kuliah Cloud Computing. Tulis laporan Project 1 dalam bahasa Indonesia baku, nada akademis tetapi mudah dipahami, kalimat pendek, tanpa basa-basi dan tanpa kalimat promosi.

TUGAS
Susun laporan lengkap yang menjelaskan proyek saya SESUAI ketentuan dosen. Urutan bab WAJIB mengikuti bagian "Laporan dan Dokumentasi" pada PDF penugasan, lalu bagian Verifikasi dan Testing (D) dan Demonstrasi (E):

1. Identitas: nama, NIM, kelas, kategori kasus yang didapat
2. Deskripsi proyek: ringkasan aplikasi dan framework
3. Langkah deployment: dengan perintah CLI atau screenshot konfigurasi
4. Endpoint API: URL dan contoh respons JSON
5. Analisis teknis: hubungan antara konsep VM/container, network, storage, dan API
6. Masalah dan solusi: kendala yang ditemui dan cara mengatasinya
7. Verifikasi dan testing: (D.1) aplikasi dapat diakses lewat alamat public, (D.2) uji API lewat browser atau Postman, (D.3) tampilkan respons JSON
8. Demonstrasi: (E) website berjalan, endpoint API diakses lewat browser/Postman, penjelasan singkat arsitektur dan deployment flow (minimal 5 menit)
9. Kesimpulan

Ketentuan dari PDF: aplikasi web sederhana dengan CRUD (Create, Read, Update, Delete) ke database, berbasis Flask atau Express, dijalankan lokal memakai VM atau Docker. Kombinasi kasus saya: nomor 15 pada tabel pembagian = Perpustakaan, Microservices (Docker), SQL. Untuk platform Docker, konfigurasi yang diminta adalah Docker network atau Docker Compose agar antar service saling berkomunikasi. (Bagian NAT dan port forwarding pada PDF berlaku untuk platform VM Monolithic.)

ATURAN KERAS (jangan dilanggar)
- Pakai HANYA fakta di bagian DATA PROYEK di bawah. Jangan mengarang angka, perintah, hasil uji, nama berkas, atau screenshot.
- Bila butuh bukti yang tidak ada di data, tulis penanda `[ISI SENDIRI: ...]`. Jangan menebak.
- Tempat screenshot ditulis `[SCREENSHOT: nama-berkas.png | keterangan gambar]`. Jangan mendeskripsikan isi gambar yang tidak tercantum di daftar.
- Jangan menulis bahwa Postman sudah diuji; belum. Uji API dilakukan lewat browser dan skrip.
- Akses dari Android lewat data seluler adalah laporan pengguna, bukan hasil uji otomatis; tulis sebagai itu.
- Jelaskan terus terang bahwa website memakai mode terbuka tanpa login dan apa risikonya.
- Nomor kasus resmi kelompok masih perlu dikonfirmasi ke dosen; NoSQL (setara No. 16) hanya pengembangan tambahan, bukan tugas kedua.
- Setiap bab harus menjelaskan APA yang dilakukan, MENGAPA, dan BUKTINYA (perintah, JSON, atau screenshot). Jangan hanya menyebut daftar.
- Pada bab 5, jangan hanya mendefinisikan istilah; jelaskan HUBUNGAN keempat konsep (lihat bahan analisis).
- Format keluaran: Markdown dengan judul bertingkat (#, ##), tabel untuk data terstruktur, blok kode untuk perintah dan JSON. Panjang sekitar 12 sampai 18 halaman bila dicetak. Beri nomor gambar (Gambar 2.1, 4.1, dst.) dan nomor tabel.

=== DATA PROYEK ===

IDENTITAS
- Penyusun: Muhammad Rafi Priyo Sembodo, NIM 101072300038, kelas S1TT-KJ-23-04
- Anggota: Atilla Pramudya Nugroho (101072300039), Muhammad Aprilio Rizal Arifin (101072300040), Aji Eka Saputra (101072300071)
- Mata kuliah: Cloud Computing, Project 1. Kasus No. 15: Perpustakaan, Microservices (Docker), SQL
- Repositori: https://github.com/muhrafi-fsdev/libraryku-unified
- Alamat publik: https://libraryku-kali.tail342a2f.ts.net/

DESKRIPSI APLIKASI
LibraryKu adalah website katalog perpustakaan kampus. Halaman: Beranda, Katalog (cari judul/penulis, filter kategori, hanya melihat), Dashboard (tambah, ubah, hapus buku lewat dialog; hapus memakai dialog konfirmasi), Perbandingan (data nyata PostgreSQL vs MongoDB), Tentang. Pengguna dapat memilih database SQL (PostgreSQL, kasus resmi) atau NoSQL (MongoDB, tambahan); kedua database terpisah, kontrak JSON sama. Atribut buku: title (maks 150), author (maks 100), category (maks 60), year (1900 sampai tahun berjalan + 1), stock (0 sampai 1.000.000).
Teknologi: frontend HTML/CSS/JavaScript biasa disajikan Nginx 1.28; backend Flask (Python 3.12) + gunicorn; PostgreSQL 16 (psycopg2); MongoDB 7.0 (PyMongo); Docker Compose; Tailscale Funnel untuk alamat HTTPS publik.
Operasi CRUD: Create = POST (201; 400 bila tidak valid); Read = GET daftar dan GET per id (200; 404); Update = PUT (200; 400; 404); Delete = DELETE (200; 404).

LINGKUNGAN
VM Kali Linux di VirtualBox (jaringan NAT), Docker Engine dan Docker Compose. Nama project Compose: libraryku-project1. Tidak ada deployment ke layanan cloud.

STRUKTUR DEPLOYMENT (lima service)
- frontend: nginx:1.28-alpine, satu-satunya yang punya port ke host: 127.0.0.1:8081 -> 80. Menjadi reverse proxy: /api/sql/* di-rewrite ke /api/* lalu ke backend SQL; /api/nosql/* ke backend NoSQL; /api/books (alamat lama) ke backend SQL
- backend: build ./backend (Flask SQL), expose 5000
- database: postgres:16-alpine, volume postgres_data, init.sql dijalankan sekali saat volume baru dibuat, healthcheck pg_isready
- mongodb: mongo:7.0.45, volume mongo_data, hanya di nosql_network, pengguna aplikasi hak readWrite pada satu database, batas 640 MB RAM
- backend-nosql: build ./backend_nosql (Flask + PyMongo), terhubung ke app_network dan nosql_network, non-root, read-only
- Network: app_network (bridge) untuk frontend, backend, database, backend-nosql; nosql_network (bridge, internal: true) hanya mongodb dan backend-nosql
- Volume: postgres_data dan mongo_data. Frontend dan nginx/default.conf dipasang bind mount read-only
- depends_on dengan healthcheck: database sehat dulu, lalu backend, lalu frontend
- restart: unless-stopped

PERINTAH DEPLOYMENT (pakai persis ini)
```
cd ~/LibraryKu_UIUX/LibraryKu_Project1
cp .env.example .env && nano .env        # isi kata sandi database acak; .env tidak masuk repositori
sudo docker compose up -d --build
sudo docker compose ps
# buka http://127.0.0.1:8081
./scripts/ctl.sh verify       # baca isi PostgreSQL dan MongoDB langsung
./scripts/ctl.sh security     # periksa port dan pengaturan container
python3 scripts/test_api.py   # CRUD SQL dan NoSQL
```
Peringatan penting: jangan menjalankan `docker compose down -v` karena menghapus volume dan seluruh data.
Hasil `docker compose ps` (lima container; database, backend, mongodb, backend-nosql berstatus healthy; hanya frontend memetakan port ke host). Teks asli menampilkan 0.0.0.0:8081 sebelum pengamanan; sekarang 127.0.0.1:8081.

Akses publik (Tailscale Funnel; dipilih karena belum punya domain untuk Cloudflare Tunnel):
```
./scripts/funnel.sh install
./scripts/funnel.sh login
./scripts/funnel.sh enable
./scripts/funnel.sh status
./scripts/funnel.sh off
```
Tidak ada port forwarding VirtualBox, tidak ada port router yang dibuka; tailscaled di Kali membuat sambungan keluar ke relay Tailscale, TLS dari Let's Encrypt, HTTP/2.

ENDPOINT API
Alamat dasar publik https://libraryku-kali.tail342a2f.ts.net (lokal http://127.0.0.1:8081). Awalan /api/sql untuk PostgreSQL dan /api/nosql untuk MongoDB.
GET /api/{sql|nosql}/health -> 200 (503 bila database tidak terjangkau)
GET /api/{sql|nosql}/books -> 200
GET /api/{sql|nosql}/books/{id} -> 200; 404
POST /api/{sql|nosql}/books -> 201; 400; 403; 413; 429
PUT /api/{sql|nosql}/books/{id} -> 200; 400; 403; 404; 429
DELETE /api/{sql|nosql}/books/{id} -> 200; 403; 404; 429
Perbedaan: id integer di SQL, ObjectId (string 24 heksadesimal) di NoSQL. Penulisan wajib header `X-Requested-With: libraryku` (website mengirim otomatis; pada curl/Postman tambahkan sendiri), tanpanya 403. Semua galat, termasuk 404 dan 405, berformat JSON dengan kunci error.

CONTOH RESPONS JSON NYATA (dari aplikasi berjalan; id bisa berbeda)
- GET /api/sql/health -> 200 {"database":"connected","service":"libraryku-api","status":"ok"}
- GET /api/nosql/health -> 200 {"database":"connected","engine":"mongodb","service":"libraryku-nosql-api","status":"ok"}
- GET /api/sql/books -> 200 {"data":[{"author":"GUS RUSDI","category":"Pendidikan","id":2,"stock":1000,"title":"REKAYASA AGAMA","year":2022}, ...],"total":N}
- POST /api/sql/books -> 201 {"data":{"author":"Kelompok Cloud","category":"Teknologi","id":87,"stock":12,"title":"Cloud Computing Praktis","year":2025},"message":"Buku berhasil ditambahkan."}
- POST data tidak valid -> 400 {"details":{"title":"Wajib diisi dengan teks.","year":"Tahun harus angka bulat antara 1900 dan 2027."},"error":"Data buku tidak valid."}
- GET id yang sudah dihapus -> 404 {"error":"Buku tidak ditemukan."}
- DELETE -> 200 {"id":87,"message":"Buku berhasil dihapus."}
- NoSQL: bentuk sama, id seperti "6af319ca8dd302eadcb33b8c"
- Alamat tidak ada -> 404 {"error":"Endpoint tidak ditemukan."}
- Tulis tanpa header aplikasi -> 403 {"error":"Permintaan tulis harus berasal dari aplikasi LibraryKu."}
- Terlalu banyak permintaan -> 429 {"error":"Terlalu banyak permintaan. Tunggu sebentar lalu coba lagi."}

BAHAN ANALISIS (bab 5: jelaskan HUBUNGAN, bukan sekadar definisi)
- VM vs container: VirtualBox menjalankan VM Kali dengan kernel sendiri; di dalamnya Docker menjalankan lima container yang berbagi kernel VM; container ringan dan sementara.
- Network: lapis 1 NAT VirtualBox (VM bisa keluar, host tidak bisa masuk tanpa port forwarding; tidak dipakai); lapis 2 app_network (container saling menemukan lewat nama service, mis. Flask ke database:5432, Nginx ke backend:5000); nosql_network internal agar MongoDB tidak bisa dijangkau dari luar; hanya Nginx dipublikasikan ke host.
- Storage: data database di volume, bukan di container; `down` tanpa -v menghapus container dan network tetapi volume tetap, terbukti pada uji restart (data sebelum = sesudah); init.sql hanya jalan saat volume baru.
- API: REST + JSON; metode HTTP menentukan operasi; Nginx sebagai gateway memilih backend lewat awalan; validasi di backend; SQL berparameter (anti SQL injection); ID MongoDB divalidasi; frontend memakai textContent (anti XSS).
- Hubungan: container menjalankan program; network menghubungkan program itu; storage menyimpan hasilnya; API adalah jalur browser meminta semuanya. Tanpa network yang sama Flask tak menemukan database; tanpa volume data hilang saat container dibuat ulang; tanpa API browser tak punya jalur ke database.
- Alur satu permintaan Create (jelaskan berurutan): klik Simpan -> POST lewat HTTPS ke alamat publik -> relay Tailscale -> tailscaled di Kali (akhiri TLS) -> 127.0.0.1:8081 -> port 80 container Nginx (cek header CSRF dan batas laju, rewrite ke /api/books) -> backend:5000 -> Flask validasi -> INSERT ... RETURNING ke database:5432 -> disimpan di volume postgres_data -> balas 201 + JSON -> website menampilkan buku baru.
- Catatan istilah: ini sistem berlapis dengan beberapa container (gateway, dua backend, dua database); satu backend API tidak otomatis berarti banyak microservice bisnis independen, tetapi sesuai fokus praktikum (pemisahan service di Docker, networking, storage, API).

KEAMANAN
Awalnya penulisan memakai login Basic Auth; dicabut atas keputusan pemilik proyek karena menyulitkan penggunaan (mode terbuka). Perlindungan yang tetap: header X-Requested-With (CSRF), pembatasan laju 10 permintaan/detik (burst 20), batas badan 16 KB, validasi backend, header keamanan (HSTS, CSP, nosniff, X-Frame-Options). Risiko yang diterima: siapa pun yang tahu alamat publik dapat menambah atau menghapus buku, jadi isi data contoh saja. Login dapat diaktifkan lagi dengan satu baris di nginx/default.conf.

MASALAH DAN SOLUSI (hanya yang benar-benar terjadi; buat tabel: masalah | penyebab | solusi)
1. Port 8080 bentrok dengan container proyek lain -> frontend dipetakan ke 8081:80.
2. Belum punya domain untuk Cloudflare Tunnel/Access -> pakai Tailscale Funnel; pengamanan dipindah ke aplikasi.
3. API tulis terbuka di internet -> awalnya login Basic Auth + CSRF + batas laju; lalu login dicabut, perlindungan lain dipertahankan.
4. Pesan "Terlalu banyak permintaan" -> dari log Nginx: batas tulis awal 2/detik dipakai bersama karena semua pengunjung Funnel tampak satu alamat; dinaikkan menjadi 10/detik (burst 20).
5. API SQL membalas HTML saat alamat tidak ada -> tambah handler galat di Flask sehingga semua galat berformat JSON.
6. Nginx gagal start bila nama service upstream belum ada -> resolver Docker + variabel upstream; saat backend mati Nginx membalas 503 JSON.
7. `limit_except` di Nginx membuat tulis gagal 500 dan melewati pengecekan CSRF -> diganti auth_basic berbasis variabel.
8. add_header di dalam location menghapus header keamanan tingkat server -> header diulang di location galat.
9. File .env tertimpa karena heredoc tanpa tanda kutip menjalankan perintah cp di dalam teks -> dipulihkan dari variabel container yang berjalan (scripts/restore_env.sh), volume database tidak tersentuh.
10. Id berbeda tipe (integer vs ObjectId) memecah UI -> frontend memperlakukan id sebagai string.
11. Respons mode lama menimpa tampilan mode baru -> request dibatalkan (AbortController) dan dicocokkan dengan mode aktif.
12. Dropdown kategori tak memuat kategori lain -> dibuat dinamis dari data.
13. Halaman melebar di layar HP -> flex-wrap pada header, diukur di 360 sampai 1024 piksel.
14. Uji otomatis melaporkan 9 kegagalan lewat alamat publik -> skrip mencari nama header huruf besar padahal HTTP/2 huruf kecil; skrip diperbaiki, aplikasi tidak berubah.
15. Token GitHub tempelan terkontaminasi karakter kontrol -> skrip push membersihkan dan memvalidasi token.

HASIL PENGUJIAN (pakai angka ini)
- Unit test validasi: 14 lulus
- API SQL+NoSQL (CRUD, validasi, 404, bentuk JSON, isolasi data): 87 dari 87 lulus
- Keamanan terarah (injeksi SQL/NoSQL, XSS, CSRF, CORS, port): 25 dari 25 lulus
- Kontrol akses mode terbuka, lokal dan lewat alamat publik: masing-masing 49 dari 49 lulus (CRUD tanpa login, CSRF 403, galat selalu JSON, validasi 400, batas laju 429, header keamanan, port 8081 hanya di 127.0.0.1)
- UI Firefox: 39 pemeriksaan lulus, 0 gagal (1 pemeriksaan dilewati karena koleksi NoSQL tidak kosong)
- Persistensi: setelah `down` lalu `up` tanpa -v, data sebelum = sesudah (kedua volume)
- MongoDB dimatikan: API NoSQL 503 JSON, SQL tetap normal
- BELUM diuji: Postman, akses dari host Windows lewat NAT, Funnel setelah reboot Kali, Cloudflare Tunnel/Access, pembaca layar, layar sentuh, benchmark beban

DAFTAR SCREENSHOT YANG TERSEDIA (nama berkas -> isi). Pakai hanya ini, di bab yang sesuai:
- 01-beranda.png: Beranda, rak buku dari data database
- 02-katalog-sql.png: Katalog mode SQL, cari, filter, pemilih SQL/NoSQL
- 03-dashboard-sql.png: Dashboard mode SQL, tabel buku, tombol Edit/Hapus/Tambah
- 04-sql-dialog-tambah.png: dialog Tambah buku terisi
- 05-sql-sesudah-create.png: sesudah Create (POST 201), buku baru di atas tabel
- 06-sql-dialog-ubah.png: dialog Edit
- 07-sql-sesudah-update.png: sesudah Update (PUT 200)
- 08-sql-konfirmasi-hapus.png: dialog konfirmasi hapus menyebut judul dan database
- 09-sql-sesudah-delete.png: sesudah Delete (DELETE 200)
- 10-dashboard-nosql.png: Dashboard mode NoSQL (MongoDB), id ObjectId
- 11-nosql-dialog-tambah.png, 12-nosql-sesudah-create.png, 13-nosql-sesudah-delete.png: CRUD di MongoDB
- 15-perbandingan.png: halaman Perbandingan; 16-tentang.png: halaman Tentang
- 20-api-sql-books.png, 24-api-sql-book-by-id.png, 22-api-sql-health.png: respons JSON SQL di browser
- 21-api-nosql-books.png, 25-api-nosql-book-by-id.png, 23-api-nosql-health.png: respons JSON NoSQL di browser
- 30-mobile-beranda.png, 31-mobile-dashboard.png: tampilan layar sempit
- diagram.png: diagram arsitektur lima service (Gambar 5.1)

DEMONSTRASI (bab 8, jadwal sekitar 6 menit)
0:00-0:40 pembukaan dan identitas kasus; 0:40-2:00 arsitektur dan deployment flow (docker compose ps, compose.yaml); 2:00-3:40 website berjalan (Beranda, Katalog, Dashboard CRUD, ganti ke NoSQL); 3:40-4:50 endpoint API di browser (/api/sql/books, /api/nosql/books, /health, contoh galat JSON); 4:50-6:00 bukti data bertahan setelah restart, masalah dan solusi, repositori GitHub.

LANGKAH KERJA
1. Tulis dulu kerangka bab (judul + 1 kalimat isi tiap bab) dan tunggu saya setuju.
2. Setelah disetujui, tulis isi lengkap bab demi bab. Bila satu jawaban tidak cukup, berhenti di akhir sebuah bab dan tulis "lanjut?".
3. Di akhir, beri daftar semua penanda `[ISI SENDIRI: ...]` dan `[SCREENSHOT: ...]` yang masih harus saya isi.
~~~

## Catatan pemakaian
- Kata sandi, token, dan isi `.env` sengaja tidak dimasukkan ke prompt.
- Bila GPT menambahkan klaim di luar data (misalnya "Postman sudah diuji"), minta ia menghapusnya.
- Hasil dari GPT tetap perlu dicocokkan dengan `laporan/laporan.docx` yang sudah ada dan dengan bukti di folder `bukti/`.
