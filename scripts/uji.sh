#!/usr/bin/env bash
# Uji LibraryKu di Kali Linux. Hasil setiap mode disimpan ke folder bukti/ untuk laporan.
#
#   ./scripts/uji.sh docker          bukti Docker: container, health, port, network, volume, SELECT (hanya baca)
#   ./scripts/uji.sh api [URL]       uji POST > GET > PUT > GET > DELETE > GET dengan SATU buku uji milik skrip ini
#   ./scripts/uji.sh persist         buat buku uji, "compose down" (tanpa -v), "up -d", cek data masih ada, hapus buku uji
#
# Opsi: --yes melewati pertanyaan konfirmasi. URL bawaan dibaca dari port frontend yang sedang berjalan
# (jadi tetap benar bila port Anda 8081), lalu jatuh ke http://localhost:8081.
# Skrip ini tidak pernah memakai "down -v", tidak mengubah .env/compose/port, dan tidak menyentuh buku lain.
set -eu
cd "$(dirname "$0")/.."

MODE="${1:-}"
[ $# -gt 0 ] && shift || true
URL_ARG=""
ASSUME_YES=0
for arg in "$@"; do
  case "$arg" in
    --yes|-y) ASSUME_YES=1 ;;
    http://*|https://*) URL_ARG="${arg%/}" ;;
    *) echo "Argumen tidak dikenal: $arg" >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }
die() { printf '[GAGAL] %s\n' "$*" >&2; exit 1; }

PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import json' >/dev/null 2>&1; then PY="$candidate"; break; fi
done
[ -n "$PY" ] || die "python3 tidak ditemukan (dipakai membaca JSON). Pasang: sudo apt install -y python3"
command -v curl >/dev/null 2>&1 || die "curl tidak ditemukan. Pasang: sudo apt install -y curl"

SUDO=""
DC=""
find_compose() {
  command -v docker >/dev/null 2>&1 || die "docker belum terpasang."
  [ -f compose.yaml ] || die "compose.yaml tidak ada di $(pwd). Jalankan skrip dari folder proyek."
  [ -f .env ] || die "File .env tidak ada di $(pwd). Skrip ini hanya untuk proyek yang sudah pernah dijalankan."
  docker info >/dev/null 2>&1 || SUDO="sudo"
  $SUDO docker info >/dev/null 2>&1 || die "Docker daemon tidak aktif. Coba: sudo systemctl start docker"
  if $SUDO docker compose version >/dev/null 2>&1; then DC="$SUDO docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then DC="$SUDO docker-compose"
  else die "Docker Compose tidak ditemukan."; fi
}

# Port yang dibuka ke host dibaca dari Compose, bukan ditebak.
detect_base() {
  local hostport
  hostport=$($DC port frontend 80 2>/dev/null | head -n 1 | sed 's/.*://') || hostport=""
  echo "http://localhost:${hostport:-8081}"
}

confirm() {
  [ "$ASSUME_YES" = 1 ] && return 0
  printf '%s\nLanjut? [y/N] ' "$1"
  read -r answer || answer=""
  case "$answer" in y|Y|ya|Ya|YA) return 0 ;; esac
  say "Dibatalkan. Tidak ada yang diubah."
  exit 0
}

TMP=""
ID=""
BASE=""
CODE=""
PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); say "[PASS] $1"; }
fail() { FAIL=$((FAIL + 1)); say "[FAIL] $1"; }
expect() { if [ "$CODE" = "$1" ]; then pass "$2 (HTTP $CODE)"; else fail "$2: diharapkan HTTP $1, didapat $CODE"; fi; }
check() { if [ "$1" = "$2" ]; then pass "$3"; else fail "$3: diharapkan '$2', didapat '$1'"; fi; }

pretty() {
  "$PY" -c 'import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))' < "$TMP" 2>/dev/null \
    || { cat "$TMP"; echo; }
}
jget() {
  "$PY" -c 'import sys, json
o = json.load(sys.stdin)
for k in sys.argv[1].split("."):
    o = o[int(k)] if k.isdigit() else o[k]
print(o)' "$1" < "$TMP" 2>/dev/null || true
}
has_id() {
  "$PY" -c 'import sys, json; sys.exit(0 if any(b["id"] == int(sys.argv[1]) for b in json.load(sys.stdin)["data"]) else 1)' "$1" < "$TMP" 2>/dev/null
}

# req METHOD PATH [JSON]: menampilkan permintaan + respons asli, mengisi CODE dan $TMP.
req() {
  local method="$1" path="$2" data="${3-}"
  say ""
  say ">>> $method $BASE$path"
  if [ -n "$data" ]; then
    say ">>> body: $data"
    CODE=$(curl -sS -m 15 -o "$TMP" -w '%{http_code}' -X "$method" -H 'Content-Type: application/json' -d "$data" "$BASE$path") || CODE=000
  else
    CODE=$(curl -sS -m 15 -o "$TMP" -w '%{http_code}' -X "$method" "$BASE$path") || CODE=000
  fi
  say "<<< HTTP $CODE"
  if [ "$CODE" = 000 ]; then : > "$TMP"; say "(tidak ada respons dari server)"; else pretty; fi
}

cleanup() {
  if [ -n "$ID" ] && [ -n "$BASE" ]; then
    curl -sS -m 10 -o /dev/null -X DELETE "$BASE/api/books/$ID" && say "[CLEANUP] buku uji ID $ID dihapus" || say "[CLEANUP] gagal menghapus buku uji ID $ID, hapus manual lewat website"
  fi
  [ -z "$TMP" ] || rm -f "$TMP"
}

header() {
  say "=== LibraryKu uji '$1' | $(date '+%Y-%m-%d %H:%M:%S %z') | $(uname -sr) | host: $(hostname) ==="
  say "Alamat yang diuji: $BASE"
}

summary() {
  say ""
  say "=== RINGKASAN: $PASS PASS, $FAIL FAIL ==="
  [ "$FAIL" = 0 ]
}

new_book_json() { printf '{"title":"Buku Uji API %s","author":"Skrip Uji Otomatis","category":"Uji","year":2024,"stock":%s}' "$1" "$2"; }

# ---------------------------------------------------------------- mode: docker (hanya baca)
run_docker() {
  header docker
  say ""; say "=== versi ==="
  docker --version
  $DC version 2>&1 | head -n 2
  say ""; say "=== $DC ps ==="
  $DC ps
  say ""; say "=== status dan health tiap container (variabel lingkungan sengaja tidak ditampilkan) ==="
  for id in $($DC ps -q); do
    $SUDO docker inspect -f '{{.Name}}  status={{.State.Status}}  health={{if .State.Health}}{{.State.Health.Status}}{{else}}-{{end}}  restart={{.HostConfig.RestartPolicy.Name}}' "$id"
  done
  say ""; say "=== port yang dibuka ke host ==="
  for pair in "frontend 80" "backend 5000" "database 5432"; do
    set -- $pair
    published=$($DC port "$1" "$2" 2>/dev/null | head -n 1) || published=""
    if [ -n "$published" ]; then say "$1:$2 -> host $published"; else say "$1:$2 -> TIDAK dibuka ke host (hanya terjangkau di jaringan Docker)"; fi
  done
  say ""; say "=== listener TCP 8080/8081 di Kali ==="
  ss -ltn 2>/dev/null | awk 'NR == 1 || /:(8080|8081)[[:space:]]/' || true
  say ""; say "=== network Compose ==="
  for net in $($SUDO docker network ls --filter label=com.docker.compose.project=libraryku-project1 --format '{{.Name}}'); do
    say "network: $net (driver: $($SUDO docker network inspect -f '{{.Driver}}' "$net"))"
    $SUDO docker network inspect -f '{{range .Containers}}  - {{.Name}}  {{.IPv4Address}}{{"\n"}}{{end}}' "$net"
  done
  say "=== volume Compose ==="
  $SUDO docker volume ls --filter label=com.docker.compose.project=libraryku-project1
  say ""; say "=== DNS di dalam jaringan: backend mencari 'database' ==="
  $DC exec -T backend python -c "import socket; print('database ->', socket.gethostbyname('database'))" || say "(perintah gagal)"
  say ""; say "=== jalur Nginx -> Flask di dalam jaringan ==="
  $DC exec -T frontend wget -qO- http://backend:5000/api/health || say "(perintah gagal)"
  say ""
  say ""; say "=== SQL (hanya baca): struktur dan isi tabel books ==="
  $DC exec -T database psql -U libraryku_user -d libraryku -c '\d books' || say "(perintah gagal)"
  $DC exec -T database psql -U libraryku_user -d libraryku -c 'SELECT id, title, author, category, year, stock FROM books ORDER BY id;' || say "(perintah gagal)"
  say ""; say "=== HTTP dari host ==="
  say ">>> GET $BASE/api/health"
  curl -sS -i -m 10 "$BASE/api/health" || say "(tidak ada respons)"
  say ""
  say "Catatan: ini bukti keadaan runtime saat $(date '+%H:%M:%S'). Tidak ada data yang diubah."
}

# ---------------------------------------------------------------- mode: api
run_api() {
  TMP=$(mktemp)
  trap cleanup EXIT
  header api
  local tag total_before created_id
  tag="$(date +%H%M%S)"

  req GET /api/health
  expect 200 "Health check"
  check "$(jget status)" ok "health.status = ok"
  check "$(jget database)" connected "health.database = connected"

  req GET /api/books
  expect 200 "Read: daftar buku"
  total_before="$(jget total)"
  say "(jumlah buku sebelum uji: $total_before)"

  req POST /api/books '{"title":"","author":"x","category":"y","year":1800,"stock":-1}'
  expect 400 "Create dengan data tidak valid ditolak"
  [ -n "$(jget details.title)" ] && pass "pesan galat judul ada" || fail "pesan galat judul tidak ada"
  [ -n "$(jget details.year)" ] && pass "pesan galat tahun ada" || fail "pesan galat tahun tidak ada"

  req POST /api/books "$(new_book_json "$tag" 3)"
  expect 201 "Create: buku uji ditambahkan"
  created_id="$(jget data.id)"
  if [ -n "$created_id" ]; then ID="$created_id"; pass "id buku uji = $ID"; else fail "id buku uji tidak terbaca"; return 1; fi

  req GET "/api/books/$ID"
  expect 200 "Read: satu buku"
  check "$(jget data.stock)" 3 "stok awal = 3"

  req PUT "/api/books/$ID" "$(new_book_json "$tag (diubah)" 11)"
  expect 200 "Update: buku uji diubah"
  check "$(jget data.stock)" 11 "respons PUT menunjukkan stok = 11"

  req GET "/api/books/$ID"
  expect 200 "Read setelah Update"
  check "$(jget data.stock)" 11 "stok yang dibaca ulang = 11 (tersimpan di database)"

  req GET /api/books
  expect 200 "Read: daftar setelah Create"
  check "$(jget total)" "$((total_before + 1))" "jumlah buku bertambah 1"
  if has_id "$ID"; then pass "buku uji ada di daftar"; else fail "buku uji tidak ada di daftar"; fi

  req DELETE "/api/books/$ID"
  expect 200 "Delete: buku uji dihapus"
  local deleted_id="$ID"
  ID=""

  req GET "/api/books/$deleted_id"
  expect 404 "Read buku yang sudah dihapus = tidak ditemukan"

  req PUT "/api/books/$deleted_id" "$(new_book_json "$tag" 1)"
  expect 404 "Update buku yang sudah dihapus = tidak ditemukan"

  req DELETE "/api/books/$deleted_id"
  expect 404 "Delete buku yang sudah dihapus = tidak ditemukan"

  req GET /api/books
  expect 200 "Read: daftar setelah Delete"
  check "$(jget total)" "$total_before" "jumlah buku kembali seperti semula ($total_before)"

  summary
}

# ---------------------------------------------------------------- mode: persist
wait_healthy() {
  local i code
  for i in $(seq 1 45); do
    code=$(curl -s -m 3 -o /dev/null -w '%{http_code}' "$BASE/api/health") || code=000
    [ "$code" = 200 ] && return 0
    sleep 2
  done
  return 1
}

run_persist() {
  TMP=$(mktemp)
  trap cleanup EXIT
  header persist
  local tag total_before
  tag="persist-$(date +%H%M%S)"

  req GET /api/health
  expect 200 "Layanan hidup sebelum uji"
  req GET /api/books
  total_before="$(jget total)"

  req POST /api/books "$(new_book_json "$tag" 5)"
  expect 201 "Buku uji dibuat sebelum restart"
  ID="$(jget data.id)"
  [ -n "$ID" ] || { fail "id buku uji tidak terbaca"; return 1; }

  say ""; say "### Menghentikan container: $DC down  (TANPA -v, volume data tidak disentuh)"
  $DC down
  say ""; say "### Volume setelah down (harus masih ada):"
  $SUDO docker volume ls --filter label=com.docker.compose.project=libraryku-project1
  say ""; say "### Menyalakan lagi: $DC up -d"
  $DC up -d
  say ""; say "### Menunggu API siap (maks. 90 detik)..."
  if wait_healthy; then pass "API kembali sehat setelah up -d"; else fail "API belum sehat setelah 90 detik. Data tetap aman di volume; periksa: $DC logs --tail=60"; return 1; fi

  req GET "/api/books/$ID"
  expect 200 "Buku uji masih ada setelah down lalu up"
  check "$(jget data.title)" "Buku Uji API $tag" "isi buku uji utuh"

  req DELETE "/api/books/$ID"
  expect 200 "Buku uji dihapus"
  ID=""

  req GET /api/books
  check "$(jget total)" "$total_before" "jumlah buku kembali seperti semula ($total_before)"

  summary
}

# ---------------------------------------------------------------- pemilih mode
run_logged() {
  mkdir -p bukti/kali
  local out="bukti/kali/${MODE}_$(date +%Y%m%d_%H%M%S).txt" rc
  set +e
  "$1" 2>&1 | tee "$out"
  rc=${PIPESTATUS[0]}
  set -e
  say ""
  say "Hasil disimpan di: $out (tempel isinya atau screenshot-nya ke laporan)"
  exit "$rc"
}

case "$MODE" in
  docker)
    find_compose
    BASE="${URL_ARG:-$(detect_base)}"
    run_logged run_docker
    ;;
  api)
    if [ -n "$URL_ARG" ]; then BASE="$URL_ARG"
    else BASE="$( (find_compose; detect_base) 2>/dev/null )" || BASE=""; BASE="${BASE:-http://localhost:8081}"; fi
    confirm "Skrip akan menambah SATU buku uji ('Buku Uji API ...') ke $BASE, mengubahnya, lalu menghapusnya.
Buku lain tidak disentuh."
    run_logged run_api
    ;;
  persist)
    find_compose
    BASE="${URL_ARG:-$(detect_base)}"
    confirm "Skrip akan: (1) menambah 1 buku uji, (2) MENGHENTIKAN SEMENTARA container proyek ini dengan '$DC down'
(tanpa -v, volume data aman), (3) menyalakannya lagi dengan 'up -d', (4) memeriksa buku uji masih ada,
(5) menghapus buku uji itu. Website tidak bisa dibuka sekitar 30 detik. Project Docker lain tidak disentuh."
    run_logged run_persist
    ;;
  *)
    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac
