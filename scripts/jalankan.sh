#!/usr/bin/env bash
# Menjalankan LibraryKu di Kali Linux dengan satu perintah.
#
#   ./scripts/jalankan.sh          siapkan .env (jika belum ada), build, lalu jalankan
#   ./scripts/jalankan.sh stop     hentikan container (data database TETAP tersimpan)
#   ./scripts/jalankan.sh status   lihat status container
#
# Skrip ini tidak pernah memakai "down -v", jadi volume database tidak dihapus.
set -eu

cd "$(dirname "$0")/.."

URL="http://localhost:8081"
VOLUME="libraryku-project1_postgres_data"

say()  { printf '\n==> %s\n' "$*"; }
fail() { printf '\n[GAGAL] %s\n' "$*" >&2; exit 1; }

# 1. Docker harus ada dan bisa dihubungi
command -v docker >/dev/null 2>&1 || fail "Docker belum terpasang.
Jalankan: sudo apt update && sudo apt install -y docker.io docker-compose
Lalu ulangi skrip ini (lihat juga docs/panduan-kali.md)."

SUDO=""
if ! docker info >/dev/null 2>&1; then
  if sudo docker info >/dev/null 2>&1; then
    SUDO="sudo"
  else
    fail "Docker tidak bisa dihubungi. Aktifkan dulu dengan: sudo systemctl enable --now docker"
  fi
fi

# 2. Pilih perintah Compose yang tersedia ("docker compose" atau "docker-compose")
if $SUDO docker compose version >/dev/null 2>&1; then
  COMPOSE="$SUDO docker compose"
elif command -v docker-compose >/dev/null 2>&1 && $SUDO docker-compose version >/dev/null 2>&1; then
  COMPOSE="$SUDO docker-compose"
else
  fail "Docker Compose tidak ditemukan.
Jalankan: sudo apt install -y docker-compose
Catatan: compose.yaml memakai 'depends_on: condition: service_healthy', jadi butuh Compose yang cukup baru."
fi

ACTION="${1:-start}"

# 3. stop / status
case "$ACTION" in
  stop|status)
    # compose.yaml mewajibkan POSTGRES_PASSWORD walau hanya untuk melihat status
    [ -f .env ] || export POSTGRES_PASSWORD="tidak-dipakai"
    if [ "$ACTION" = "stop" ]; then
      say "Menghentikan container (data database tetap tersimpan)"
      $COMPOSE down
    else
      $COMPOSE ps
    fi
    exit 0
    ;;
  start) ;;
  *) fail "Perintah tidak dikenal: $ACTION (pilihan: start | stop | status)" ;;
esac

# 4. Siapkan .env. File yang sudah ada TIDAK akan ditimpa.
if [ ! -f .env ]; then
  if $SUDO docker volume inspect "$VOLUME" >/dev/null 2>&1; then
    fail "Volume database lama ditemukan, tetapi file .env tidak ada.
Password baru tidak akan cocok dengan database lama.
Buat .env dari .env.example dan isi POSTGRES_PASSWORD dengan password yang dulu dipakai:
  cp .env.example .env && nano .env"
  fi
  say "Membuat .env dengan password acak (hanya untuk lokal)"
  SECRET="$(openssl rand -hex 16 2>/dev/null || python3 -c 'import secrets; print(secrets.token_hex(16))' 2>/dev/null || true)"
  [ -n "$SECRET" ] || fail "Tidak bisa membuat password acak (openssl dan python3 tidak ada). Buat manual: cp .env.example .env && nano .env"
  umask 077
  sed "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$SECRET/" .env.example > .env
  grep -q "^POSTGRES_PASSWORD=$SECRET\$" .env || fail "Gagal menulis .env. Buat manual: cp .env.example .env && nano .env"
fi

# 5. Peringatan ringan bila port 8081 sudah dipakai
if command -v ss >/dev/null 2>&1 && ss -ltn 2>/dev/null | grep -q ':8081 '; then
  say "Port 8081 sudah dipakai. Jika itu LibraryKu yang sedang berjalan, tidak apa-apa; jika bukan, hentikan dulu aplikasi tersebut."
fi

# 6. Build dan jalankan
say "Membangun dan menjalankan container (pertama kali bisa beberapa menit)"
$COMPOSE up -d --build || fail "Compose gagal. Lihat penyebabnya dengan: $COMPOSE logs --tail=60"

# 7. Tunggu sampai API menjawab
READY=0
if command -v curl >/dev/null 2>&1; then
  say "Menunggu layanan siap"
  TRY=0
  while [ "$TRY" -lt 45 ]; do
    if curl -fsS "$URL/api/health" >/dev/null 2>&1; then READY=1; break; fi
    TRY=$((TRY + 1))
    sleep 2
  done
fi

$COMPOSE ps

if [ "$READY" -eq 1 ]; then
  printf '\nSiap. Buka %s di browser Kali.\n' "$URL"
  printf 'JSON untuk laporan: %s/api/health  dan  %s/api/books\n' "$URL" "$URL"
  printf 'Berhenti: ./scripts/jalankan.sh stop   (data buku tetap aman)\n'
else
  printf '\nLayanan belum menjawab di %s. Coba buka manual, atau lihat log:\n  %s logs --tail=60\n' "$URL" "$COMPOSE"
fi
