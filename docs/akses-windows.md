# Akses LibraryKu dari host Windows

Disusun 2026-11-05 dari audit read-only di VM Kali (`bukti/pengujian/audit_jaringan_host.txt`). **Belum ada pengaturan yang diubah.**

## Temuan

| Hal | Hasil |
|---|---|
| Mode jaringan VM | NAT (eth0 10.0.2.15/24, gateway 10.0.2.2) |
| Binding Docker port 8081 | `0.0.0.0` dan `[::]` (semua antarmuka guest), jadi bisa dijangkau lewat NAT port forwarding |
| Backend (5000) dan database (5432) | Tidak dipublikasikan ke host, hanya di jaringan Docker |
| Firewall guest | ufw tidak ada; ruleset nft/iptables belum terbaca (butuh sudo): NOT TESTED |
| Akses dari Windows | NOT TESTED |

## Pilihan paling aman: forwarding hanya ke loopback Windows

Aplikasi tidak memiliki autentikasi (siapa pun yang menjangkau API dapat membuat, mengubah, dan menghapus buku). Karena itu **jangan** memakai Bridged Adapter dan **jangan** mengosongkan Host IP di aturan forwarding (itu membuka ke jaringan LAN Windows). Pakai Host IP `127.0.0.1`: hanya komputer Windows itu sendiri yang bisa membuka `http://127.0.0.1:8081`.

Jalankan di Windows (PowerShell). Nama VM pada catatan sebelumnya: "Rafi Priyo Kali Linux"; cek dulu namanya.

1. Cek nama VM, mode jaringan, dan aturan yang ada:
   ```powershell
   & "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" list vms
   & "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" showvminfo "Rafi Priyo Kali Linux" --machinereadable | findstr /i "nic1 Forwarding"
   ```
2. Pastikan port 8081 di Windows kosong (tidak ada keluaran berarti kosong):
   ```powershell
   netstat -ano | findstr :8081
   ```
3. Tambah aturan (VM menyala). Alternatif lewat GUI: Settings, Network, Adapter 1, Advanced, Port Forwarding.
   ```powershell
   & "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" controlvm "Rafi Priyo Kali Linux" natpf1 "libraryku,tcp,127.0.0.1,8081,10.0.2.15,8081"
   ```
   Jika perintah ditolak atau aturan hilang saat VM dimatikan, matikan VM lalu pakai `modifyvm "Rafi Priyo Kali Linux" --natpf1 "libraryku,tcp,127.0.0.1,8081,10.0.2.15,8081"`.
4. Uji dari Windows:
   ```powershell
   curl.exe http://127.0.0.1:8081/api/health
   ```
   Lalu buka `http://127.0.0.1:8081` di browser Windows. Jika Docker Desktop Windows memakai port 8081, ganti port host (mis. 8181) pada kedua tempat di aturan dan di alamat.
5. Cabut aturan bila sudah tidak perlu:
   ```powershell
   & "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" controlvm "Rafi Priyo Kali Linux" natpf1 delete libraryku
   ```

Jika langkah 4 gagal padahal website jalan di Kali, cek firewall guest di Kali dan kirim hasilnya:
```bash
sudo nft list ruleset | head -60
```

## "Alamat public" pada PDF: NEEDS CLARIFICATION

Akses di atas adalah akses **lokal** (Windows ke VM di komputer yang sama), bukan alamat publik di internet. Belum ada dasar untuk menyamakan keduanya. Tanyakan ke dosen apakah "alamat public" berarti akses dari host/jaringan lokal atau alamat yang dapat dijangkau dari internet. Jika dosen mewajibkan internet, API harus diberi autentikasi dan HTTPS lebih dulu; jangan diekspos apa adanya.
