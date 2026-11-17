#!/usr/bin/env bash
# LibraryKu Unified: kontrol Docker untuk SQL + NoSQL. Dijalankan PENGGUNA (butuh sudo untuk Docker).
# Setiap aksi menyimpan keluarannya ke bukti/unified/ctl_<aksi>_<waktu>.txt (tanpa password).
#
#   ./scripts/ctl.sh up            tarik mongo:7.0.45, bangun backend-nosql, nyalakan mongodb + backend-nosql, muat ulang Nginx
#   ./scripts/ctl.sh status        container, port, resource, jaringan, volume, health kedua API
#   ./scripts/ctl.sh verify        periksa isi MongoDB dan PostgreSQL langsung (baca saja) + uji autentikasi MongoDB
#   ./scripts/ctl.sh security      pengaturan keamanan container dan port (baca saja)
#   ./scripts/ctl.sh stop-nosql    hentikan HANYA mongodb (uji galat), lalu uji API
#   ./scripts/ctl.sh start-nosql   nyalakan lagi mongodb
#   ./scripts/ctl.sh restart-all   down lalu up -d seluruh project (TANPA -v), bandingkan data sebelum dan sesudah
#   ./scripts/ctl.sh reload-nginx   uji sintaks lalu muat ulang Nginx tanpa downtime
#   ./scripts/ctl.sh apply-frontend  terapkan Nginx baru (login untuk tulis, rate limit) dan bind 8081 ke 127.0.0.1
#   ./scripts/ctl.sh logs          log terakhir backend-nosql dan mongodb
#
# Opsi: --yes melewati konfirmasi. Skrip tidak pernah memakai "down -v", prune, atau menyentuh container lain.
set -eu
cd "$(dirname "$0")/.."
case "$(pwd)" in *Unduhan*) echo "Jalankan dari ~/LibraryKu_UIUX/LibraryKu_Project1, bukan salinan di Unduhan." >&2; exit 2 ;; esac
grep -q '^name: libraryku-project1' compose.yaml || { echo "compose.yaml bukan proyek libraryku-project1." >&2; exit 2; }

ACTION="${1:-}"; [ $# -gt 0 ] && shift || true
ASSUME_YES=0
for arg in "$@"; do case "$arg" in --yes|-y) ASSUME_YES=1 ;; *) echo "Argumen tidak dikenal: $arg" >&2; exit 2 ;; esac; done

SUDO=""
docker info >/dev/null 2>&1 || SUDO="sudo"
$SUDO docker info >/dev/null 2>&1 || { echo "Docker tidak bisa diakses. Coba: sudo systemctl start docker" >&2; exit 1; }
DC="$SUDO docker compose"
BASE="${LIBRARYKU_URL:-http://localhost:8081}"
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p bukti/unified
OUT="bukti/unified/ctl_${ACTION:-bantuan}_${STAMP}.txt"

say() { printf '%s\n' "$*"; }
confirm() {
  [ "$ASSUME_YES" = 1 ] && return 0
  printf '%s\nLanjut? [y/N] ' "$1"; read -r reply
  case "$reply" in y|Y|ya|YA|Ya) return 0 ;; *) say "Dibatalkan."; exit 0 ;; esac
}
http() { # http <label> <path> : cetak status dan badan singkat
  local code body
  body="$(curl -s -m 10 -w '\n%{http_code}' "$BASE$2" || true)"
  code="$(printf '%s' "$body" | tail -n1)"; body="$(printf '%s' "$body" | sed '$d' | cut -c1-300)"
  say ">>> $1  GET $2  -> HTTP $code"; say "$body"
}
wait_healthy() { # wait_healthy <service> <detik>
  local svc="$1" limit="$2" i=0 cid st
  while [ "$i" -lt "$limit" ]; do
    cid="$($DC ps -q "$svc" 2>/dev/null || true)"
    if [ -n "$cid" ]; then
      st="$($SUDO docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || echo unknown)"
      [ "$st" = healthy ] && { say "[OK] $svc healthy"; return 0; }
    fi
    sleep 3; i=$((i+3))
  done
  say "[GAGAL] $svc belum healthy setelah ${limit}s. Cek: ./scripts/ctl.sh logs"; return 1
}
mongo_sh() { # mongo_sh <js> : jalankan sebagai pengguna aplikasi (kredensial dibaca di dalam container)
  $DC exec -T mongodb sh -c 'mongosh --quiet --norc -u "$MONGO_APP_USER" -p "$MONGO_APP_PASSWORD" --authenticationDatabase "$MONGO_APP_DB" "$MONGO_APP_DB" --eval "$1"' _ "$1"
}
counts() {
  for m in sql nosql; do
    printf '%s: ' "$m"; curl -s -m 10 "$BASE/api/$m/books" | python3 -c "import json,sys; d=json.load(sys.stdin); print('total', d['total'], 'ids', [b['id'] for b in d['data']])" 2>&1 || echo "(tidak terbaca)"
  done
}

run() {
case "$ACTION" in
up)
  say "=== UP: tambah MongoDB dan backend NoSQL (service SQL tidak disentuh) | $(date '+%F %T %Z') ==="
  confirm "Aksi: tarik image mongo:7.0.45 (sekitar 300 MB), bangun image backend-nosql, nyalakan mongodb dan backend-nosql, lalu muat ulang konfigurasi Nginx (tanpa downtime). Container database/backend/frontend TIDAK dibuat ulang; volume postgres_data tidak disentuh."
  $DC config -q && say "[OK] compose.yaml valid"
  $DC pull mongodb
  $DC build backend-nosql
  $DC up -d mongodb backend-nosql
  wait_healthy mongodb 180
  wait_healthy backend-nosql 120
  say "--- uji sintaks lalu muat ulang Nginx ---"
  $DC exec -T frontend nginx -t
  $DC exec -T frontend nginx -s reload && say "[OK] Nginx dimuat ulang"
  sleep 2
  $DC ps
  say "--- digest image mongo ---"; $SUDO docker image inspect mongo:7.0.45 --format '{{index .RepoDigests 0}}' 2>/dev/null || true
  http "SQL health (alamat baru)" /api/sql/health
  http "SQL health (alamat lama)" /api/health
  http "NoSQL health" /api/nosql/health
  counts ;;
status)
  say "=== STATUS | $(date '+%F %T %Z') ==="
  $DC ps
  say "--- resource (sekali ambil) ---"
  $SUDO docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' $($DC ps -q) 2>/dev/null || true
  say "--- port yang dipublikasikan ke host ---"
  for c in $($DC ps -q); do $SUDO docker inspect -f '{{.Name}} -> {{if .NetworkSettings.Ports}}{{range $p,$b := .NetworkSettings.Ports}}{{$p}}={{if $b}}{{range $b}}{{.HostIp}}:{{.HostPort}} {{end}}{{else}}(tidak dipublikasikan){{end}} {{end}}{{else}}(tanpa port){{end}}' "$c"; done
  say "--- jaringan project ---"
  for n in $($SUDO docker network ls --filter label=com.docker.compose.project=libraryku-project1 --format '{{.Name}}'); do
    $SUDO docker network inspect -f '{{.Name}} driver={{.Driver}} internal={{.Internal}} anggota:{{range .Containers}} {{.Name}}{{end}}' "$n"; done
  say "--- volume project ---"
  $SUDO docker volume ls --filter label=com.docker.compose.project=libraryku-project1
  http "SQL health" /api/sql/health; http "NoSQL health" /api/nosql/health; counts ;;
verify)
  say "=== VERIFY (baca saja) | $(date '+%F %T %Z') ==="
  say "--- MongoDB: database, koleksi, jumlah dokumen, daftar judul (pengguna aplikasi) ---"
  mongo_sh 'printjson({db: db.getName(), koleksi: db.getCollectionNames(), jumlah: db.books.countDocuments()}); db.books.find({}, {title:1, author:1, category:1, year:1, stock:1}).sort({_id:-1}).limit(20).forEach(d => printjson(d));'
  say "--- MongoDB: pengguna aplikasi dan hak aksesnya ---"
  mongo_sh 'printjson(db.getUser(process.env.MONGO_APP_USER, {showPrivileges:false}) && {user: db.getUser(process.env.MONGO_APP_USER).user, roles: db.getUser(process.env.MONGO_APP_USER).roles})'
  say "--- MongoDB: akses TANPA kredensial harus ditolak ---"
  $DC exec -T mongodb mongosh --quiet --norc libraryku_nosql --eval 'try { print(db.books.countDocuments()); } catch (e) { print("DITOLAK: " + e.codeName); }' || true
  say "--- MongoDB: pengguna aplikasi tidak boleh membaca database admin ---"
  mongo_sh 'try { db.getSiblingDB("admin").system.users.countDocuments(); print("TIDAK DITOLAK (perlu diperbaiki)"); } catch (e) { print("DITOLAK: " + e.codeName); }' || true
  say "--- PostgreSQL: tabel books ---"
  $DC exec -T database psql -U libraryku_user -d libraryku -c "SELECT id, title, author, category, year, stock FROM books ORDER BY id DESC;" ;;
security)
  say "=== SECURITY (baca saja, tanpa menampilkan variabel lingkungan) | $(date '+%F %T %Z') ==="
  for c in $($DC ps -q); do
    $SUDO docker inspect -f '{{.Name}}: user="{{.Config.User}}" readonlyRootfs={{.HostConfig.ReadonlyRootfs}} capDrop={{.HostConfig.CapDrop}} secOpt={{.HostConfig.SecurityOpt}} memLimit={{.HostConfig.Memory}} nanoCpus={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}} privileged={{.HostConfig.Privileged}} restart={{.HostConfig.RestartPolicy.Name}} image={{.Config.Image}}' "$c"
  done
  say "--- pengguna proses di backend-nosql ---"; $DC exec -T backend-nosql id || true
  say "--- pengguna proses mongod (PID 1) di container mongodb ---"; $DC exec -T mongodb sh -c 'grep -E "^(Name|Uid)" /proc/1/status' || true
  say "--- versi pip di backend-nosql ---"; $DC exec -T backend-nosql pip --version 2>/dev/null || true
  say "--- port 27017 di host harus TIDAK ada ---"; (ss -ltn | grep -E ':27017 ' || echo "tidak ada listener 27017 (benar)")
  say "--- pustaka Python backend-nosql (untuk pemeriksaan kerentanan) ---"; $DC exec -T backend-nosql pip list --format=freeze || true
  say "--- pustaka Python backend SQL ---"; $DC exec -T backend pip list --format=freeze || true
  say "--- konfigurasi Nginx aktif (header dan router) ---"; $DC exec -T frontend nginx -T 2>/dev/null | grep -E 'server_tokens|add_header|client_max_body_size|location|proxy_pass|resolver|rewrite|error_page' ;;
stop-nosql)
  say "=== STOP-NOSQL | $(date '+%F %T %Z') ==="
  confirm "Aksi: menghentikan HANYA container mongodb untuk menguji penanganan galat. PostgreSQL dan website tetap hidup; mode NoSQL akan menampilkan galat sampai Anda menjalankan start-nosql."
  counts
  $DC stop mongodb
  sleep 4
  http "NoSQL health (Mongo mati)" /api/nosql/health
  http "NoSQL daftar (Mongo mati)" /api/nosql/books
  http "SQL health (harus tetap ok)" /api/sql/health
  http "SQL daftar (harus tetap ok)" /api/sql/books
  say "Mongo sekarang MATI. Setelah pengujian UI selesai jalankan: ./scripts/ctl.sh start-nosql" ;;
start-nosql)
  say "=== START-NOSQL | $(date '+%F %T %Z') ==="
  $DC start mongodb
  wait_healthy mongodb 180
  sleep 5
  http "NoSQL health" /api/nosql/health
  counts ;;
restart-all)
  say "=== RESTART-ALL (down lalu up -d, TANPA -v) | $(date '+%F %T %Z') ==="
  confirm "Aksi: menghentikan lalu menyalakan lagi SELURUH container project libraryku-project1 (website mati sekitar satu menit). Volume postgres_data dan mongo_data tetap ada (tanpa -v)."
  say "--- data SEBELUM ---"; counts
  $DC down
  say "--- volume setelah down (harus masih ada) ---"; $SUDO docker volume ls --filter label=com.docker.compose.project=libraryku-project1
  $DC up -d
  wait_healthy database 120; wait_healthy backend 120; wait_healthy mongodb 180; wait_healthy backend-nosql 120
  sleep 3
  $DC ps
  say "--- data SESUDAH ---"; counts
  http "SQL health" /api/sql/health; http "NoSQL health" /api/nosql/health ;;
reload-nginx)
  say "=== RELOAD-NGINX (tanpa downtime) | $(date '+%F %T %Z') ==="
  confirm "Aksi: menguji sintaks konfigurasi Nginx di container sementara, lalu muat ulang Nginx pada container frontend yang berjalan (tanpa membuat ulang container, tanpa downtime)."
  $SUDO docker run --rm --network none -v "$PWD/nginx/default.conf":/etc/nginx/conf.d/default.conf:ro -v "$PWD/nginx/auth":/etc/nginx/auth:ro nginx:1.28-alpine nginx -t
  $DC exec -T frontend nginx -t
  $DC exec -T frontend nginx -s reload && say "[OK] Nginx dimuat ulang"
  # Bind mount satu-berkas tetap menunjuk ke berkas LAMA bila default.conf diganti sebagai berkas baru (git merge/pull),
  # sehingga reload memuat konfigurasi lama. Bandingkan isi yang berjalan dengan berkas di disk; bila beda, buat ulang
  # hanya container frontend (database dan backend tidak disentuh).
  RUN_SUM="$($DC exec -T frontend cat /etc/nginx/conf.d/default.conf | sha256sum | cut -d' ' -f1)"
  FILE_SUM="$(sha256sum nginx/default.conf | cut -d' ' -f1)"
  if [ "$RUN_SUM" != "$FILE_SUM" ]; then
    say "[PERINGATAN] Nginx masih memakai konfigurasi LAMA (berkas pada disk diganti git). Membuat ulang container frontend saja..."
    $DC up -d --force-recreate --no-deps frontend
    sleep 4
  fi
  say "[OK] konfigurasi Nginx yang berjalan sama dengan nginx/default.conf"
  sleep 2
  http "SQL health" /api/sql/health; http "NoSQL health" /api/nosql/health ;;
apply-frontend)
  say "=== APPLY-FRONTEND: terapkan Nginx baru (login untuk tulis, pembatasan laju) + binding loopback | $(date '+%F %T %Z') ==="
  confirm "Aksi: (1) menguji sintaks konfigurasi Nginx baru di container sementara (tidak menyentuh website), (2) membuat ulang HANYA container frontend (mounting nginx/auth dan port 8081 hanya di 127.0.0.1 Kali). Website mati sekitar 5 detik. Akibat: 8081 tidak lagi terbuka dari NAT/LAN VirtualBox; akses dari luar lewat Cloudflare Tunnel. PostgreSQL, MongoDB, dan backend tidak disentuh."
  say "--- uji sintaks Nginx (container sementara) ---"
  $SUDO docker run --rm --network none -v "$PWD/nginx/default.conf":/etc/nginx/conf.d/default.conf:ro -v "$PWD/nginx/auth":/etc/nginx/auth:ro nginx:1.28-alpine nginx -t
  $DC up -d frontend
  sleep 6
  $DC ps frontend
  say "--- port frontend ---"; ss -ltn | grep ':8081' || say "(tidak ada listener 8081!)"
  http "SQL health" /api/sql/health; http "NoSQL health" /api/nosql/health
  say "--- tulis tanpa login harus 401 ---"
  curl -s -m 10 -o /dev/null -w "POST tanpa login -> HTTP %{http_code}\n" -X POST -H 'Content-Type: application/json' -H 'X-Requested-With: libraryku' -d '{}' "$BASE/api/sql/books"
  counts ;;
logs)
  $DC logs --tail=40 backend-nosql mongodb 2>&1 | grep -viE 'password|pwd' ;;
*)
  sed -n '2,15p' "$0"; exit 1 ;;
esac
}

run 2>&1 | tee "$OUT"
say ""; say "Hasil disimpan di: $OUT"
