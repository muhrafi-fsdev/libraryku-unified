#!/usr/bin/env bash
# Memulihkan .env dari environment container LibraryKu yang SEDANG BERJALAN (kata sandi asli masih tersimpan di sana).
# Dijalankan PENGGUNA (butuh sudo untuk docker inspect). Kata sandi tidak pernah dicetak.
# Setelah berhasil, salinan cadangan .env disimpan di ~/.libraryku_env.backup (izin 600, di luar repository).
set -eu
cd "$(dirname "$0")/.."
case "$(pwd)" in *Unduhan*) echo "Jalankan dari ~/LibraryKu_UIUX/LibraryKu_Project1." >&2; exit 2 ;; esac
get() { sudo docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$1" 2>/dev/null | grep -m1 "^$2=" | cut -d= -f2- || true; }
PG="$(get libraryku-project1-database-1 POSTGRES_PASSWORD)"
BK="$(get libraryku-project1-backend-1 DB_PASSWORD)"
MR="$(get libraryku-project1-mongodb-1 MONGO_INITDB_ROOT_PASSWORD)"
MA="$(get libraryku-project1-mongodb-1 MONGO_APP_PASSWORD)"
NA="$(get libraryku-project1-backend-nosql-1 MONGO_APP_PASSWORD)"
for pair in "PG:$PG" "MR:$MR" "MA:$MA"; do
  name="${pair%%:*}"; val="${pair#*:}"
  [ -n "$val" ] || { echo "Gagal membaca $name dari container (apakah container berjalan?)." >&2; exit 1; }
  case "$val" in ganti*) echo "$name masih berisi placeholder: container dibuat ulang dengan .env yang tertimpa. Hubungi asisten." >&2; exit 1 ;; esac
done
[ "$PG" = "$BK" ] && echo "[OK] kata sandi database cocok dengan backend SQL" || echo "[PERINGATAN] kata sandi PostgreSQL dan backend SQL berbeda"
[ "$MA" = "$NA" ] && echo "[OK] kata sandi aplikasi MongoDB cocok dengan backend NoSQL" || echo "[PERINGATAN] kata sandi MongoDB aplikasi dan backend NoSQL berbeda"
umask 077
{
  echo "# Dipulihkan dari environment container yang berjalan. Jangan di-commit."
  echo "POSTGRES_PASSWORD=$PG"
  echo "MONGO_ROOT_PASSWORD=$MR"
  echo "MONGO_APP_PASSWORD=$MA"
  echo "# FRONTEND_BIND=127.0.0.1"
} > .env.baru
mv .env.baru .env; chmod 600 .env
cp -p .env "$HOME/.libraryku_env.backup"; chmod 600 "$HOME/.libraryku_env.backup"
echo "[OK] .env dipulihkan (3 kata sandi) dan dicadangkan ke ~/.libraryku_env.backup"
# Verifikasi: nilai yang akan dipakai Compose harus sama dengan yang ada di container (tanpa dicetak)
CFG="$(sudo docker compose config 2>/dev/null | grep -m1 'POSTGRES_PASSWORD' | sed 's/.*: //' | tr -d '"')"
[ "$CFG" = "$PG" ] && echo "[OK] docker compose membaca kata sandi yang sama dengan container" || echo "[PERINGATAN] nilai Compose berbeda dari container"
