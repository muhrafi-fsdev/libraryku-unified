# Panduan Bukti di Kali Linux

Semua perintah dijalankan **di Kali**, di folder proyek yang berisi `compose.yaml` (contoh: `~/LibraryKu_UIUX/LibraryKu_Project1`). Port di panduan ini 8081 (milik Anda). Skrip membaca port yang benar dari Compose, jadi tidak perlu diubah.

## 0. Pasang tampilan baru (hanya frontend, aman)

Tampilan baru berada di paket `LibraryKu_Patch_Frontend.zip`. Paket ini **tidak memuat** `compose.yaml` maupun `scripts/jalankan.sh`, jadi konfigurasi 8081 Anda tidak tertimpa. Folder `frontend` dipasang ke container sebagai read-only, **tanpa build ulang** dan tanpa menyentuh volume database.

```bash
cd ~/LibraryKu_UIUX/LibraryKu_Project1
cp -r frontend frontend.bak-sebelum-redesain
unzip -o ~/Downloads/LibraryKu_Patch_Frontend.zip -d /tmp/lk_patch
cp -r /tmp/lk_patch/LibraryKu_Patch_Frontend/frontend/. frontend/
cp /tmp/lk_patch/LibraryKu_Patch_Frontend/uji_kali.sh .
chmod +x scripts/uji.sh
```

Buka `http://localhost:8081` di Firefox, lalu **Ctrl+Shift+R** (hard refresh). Untuk kembali ke tampilan lama: `rm -r frontend && mv frontend.bak-sebelum-redesain frontend`.

## 1. Bukti Docker (hanya baca, tidak mengubah apa pun)

```bash
./scripts/uji.sh docker
```

Menampilkan `docker compose ps`, status health, port yang dibuka ke host (hanya frontend), network dan anggotanya, volume, DNS `database` dari backend, jalur Nginx ke Flask, struktur tabel, dan `SELECT` isi tabel `books`. Hasil tersimpan di `bukti/kali/docker_*.txt`.

## 2. Uji CRUD asli lewat API (menambah lalu menghapus SATU buku uji)

```bash
./scripts/uji.sh api
```

Skrip meminta konfirmasi, lalu menjalankan `POST` > `GET` > `PUT` > `GET` > `DELETE` > `GET` dengan satu buku bernama "Buku Uji API ...", memeriksa status HTTP 201/200/404/400, dan menampilkan JSON asli. Buku Anda yang lain tidak disentuh. Hasil di `bukti/kali/api_*.txt`: **inilah JSON aktual untuk laporan bagian 5 dan 6.** Bila perlu menentukan alamat sendiri: `./scripts/uji.sh api http://localhost:8081`.

## 3. Uji lewat browser (yang diminta PDF: browser atau Postman)

**GET (Firefox):** buka `http://localhost:8081/api/health` dan `http://localhost:8081/api/books` (juga ada tautannya di bagian *Tentang* pada website). Ambil screenshot yang menampilkan **alamat di address bar dan JSON-nya**.

**POST/PUT/DELETE (Firefox DevTools)**, bila Postman belum terpasang: tekan **F12**, tab **Console**, ketik `allow pasting` lalu Enter, kemudian tempel:

```javascript
(async () => {
  const call = async (method, path, body) => {
    const r = await fetch(path, { method, headers: { 'Content-Type': 'application/json' }, body: body && JSON.stringify(body) });
    const data = await r.json();
    console.log(method, path, '->', r.status, data);
    return data;
  };
  const buku = { title: 'Buku Uji Konsol', author: 'Uji', category: 'Uji', year: 2024, stock: 2 };
  const id = (await call('POST', '/api/books', buku)).data.id;
  await call('PUT', `/api/books/${id}`, { ...buku, stock: 9 });
  await call('GET', `/api/books/${id}`);
  await call('DELETE', `/api/books/${id}`);
  await call('GET', `/api/books/${id}`); // harus 404: buku sudah dihapus
})();
```

Setiap baris hasil menampilkan **method, URL, status HTTP, dan JSON**. Potongan ini hanya menyentuh satu buku, yaitu yang baru dibuatnya sendiri ("Buku Uji Konsol"), dan menghapusnya di akhir. Screenshot konsolnya cocok untuk laporan dan slide demo.

## 4. Uji data bertahan setelah restart (meminta konfirmasi)

```bash
./scripts/uji.sh persist
```

Menambah buku uji, menjalankan `docker compose down` (**tanpa `-v`**), `up -d`, memeriksa buku uji masih ada, lalu menghapusnya. Website tidak bisa dibuka sekitar 30 detik. Project Docker lain (misalnya `kali-compose-lab`) tidak disentuh. Jangan menjalankan `down -v`, `docker volume prune`, atau menghapus volume secara manual.

## 5. Daftar screenshot untuk laporan dan slide

| No. | Isi screenshot | Cara | Dipakai di |
|---|---|---|---|
| 1 | `docker compose ps`: tiga service, database dan backend *healthy* | `./scripts/uji.sh docker` (bagian atas) | Laporan 3, slide arsitektur |
| 2 | Port: hanya frontend dibuka, backend/database tidak | `./scripts/uji.sh docker` (bagian "port") | Laporan 5, slide arsitektur |
| 3 | Network `app_network` dan DNS `database` | `./scripts/uji.sh docker` | Laporan 5 |
| 4 | `SELECT` isi tabel `books` | `./scripts/uji.sh docker` (bagian SQL) | Laporan 5 |
| 5 | Beranda di Firefox (alamat `localhost:8081` terlihat) | Screenshot jendela penuh | Laporan 2, slide 1 |
| 6 | Katalog dengan daftar buku dan filter | Scroll ke Katalog | Laporan 2, slide demo |
| 7 | Create: formulir terisi, lalu buku muncul di daftar | Dua screenshot | Laporan 6, slide demo |
| 8 | Update: sebelum dan sesudah | Dua screenshot | Laporan 6 |
| 9 | Dialog konfirmasi Delete, lalu daftar setelah dihapus | Dua screenshot | Laporan 6 |
| 10 | `/api/health` dan `/api/books` di Firefox (JSON + address bar) | Bagian 3 | Laporan 4, slide API |
| 11 | Respons POST/PUT/DELETE (method, URL, status, JSON) | Bagian 3 (konsol) atau `bukti/kali/api_*.txt` | Laporan 4, slide API |
| 12 | Bukti data bertahan setelah restart | `./scripts/uji.sh persist` | Laporan 5 |
| 13 | Konflik port 8080 (`docker ps` atau `ss -ltnp`), jika masih bisa direproduksi | `sudo ss -ltnp \| grep :8080` | Laporan 8 |

## 6. Akses dari Windows host (hanya bila dosen meminta)

VM Kali Anda memakai **NAT tanpa port forwarding**, sehingga Windows host tidak bisa membuka `localhost:8081` milik guest. PDF memakai istilah "alamat public" tetapi juga menegaskan *localhost* dan *tanpa cloud*; **tanyakan dulu ke dosen** apa yang dimaksud. Jika cukup akses dari host, dari **PowerShell di Windows** (VM harus dimatikan dulu; port host 18081 dipilih agar tidak bentrok):

```powershell
& 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe' modifyvm "Rafi Priyo Kali Linux" --natpf1 "libraryku,tcp,127.0.0.1,18081,,8081"
```

Setelah VM menyala, buka `http://127.0.0.1:18081` di Windows. Perintah ini **belum dijalankan** oleh siapa pun. Mengekspos database atau Flask langsung ke internet tidak diperlukan dan tidak disarankan.

## 7. Bila ada yang gagal

Kirim teks `[FAIL]`/`[GAGAL]` dari terminal dan keluaran `sudo docker compose logs --tail=60`. Jangan kirim isi file `.env`.
