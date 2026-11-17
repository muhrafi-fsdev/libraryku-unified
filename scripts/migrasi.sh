#!/usr/bin/env bash
# Menerapkan database/migrations/002_peminjaman.sql ke PostgreSQL yang SEDANG BERJALAN (menambah tabel loans).
# Aman diulang dan tidak menyentuh tabel books. Hanya dijalankan oleh pengguna; butuh sudo untuk Docker.
#   ./scripts/migrasi.sh          minta konfirmasi dulu
#   ./scripts/migrasi.sh --yes    tanpa konfirmasi
set -eu
cd "$(dirname "$0")/.."
case "$(pwd)" in *Unduhan*) echo "Jalankan dari folder proyek aktif, bukan salinan di Unduhan." >&2; exit 2 ;; esac
grep -q '^name: libraryku-project1' compose.yaml || { echo "compose.yaml bukan proyek libraryku-project1." >&2; exit 2; }
if [ "${1:-}" != "--yes" ]; then
  printf 'Akan menambah tabel loans ke database PostgreSQL yang berjalan (tabel books tidak diubah). Lanjut? [y/N] '
  read -r r; case "$r" in y|Y|ya|Ya) ;; *) echo "Dibatalkan."; exit 0 ;; esac
fi
sudo docker compose exec -T database psql -v ON_ERROR_STOP=1 -U libraryku_user -d libraryku < database/migrations/002_peminjaman.sql
echo "--- struktur tabel loans ---"
sudo docker compose exec -T database psql -U libraryku_user -d libraryku -c '\d loans'
echo "[OK] migrasi selesai. Jalankan juga: sudo docker compose up -d --build backend (agar API peminjaman aktif) lalu ./scripts/ctl.sh reload-nginx"
