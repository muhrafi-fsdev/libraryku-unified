#!/usr/bin/env bash
# Menguji fitur Peminjaman pada STACK SEMENTARA, bukan pada database aktif.
#
# Yang dibuat: proyek Compose "libraryku-uji" (database, MongoDB, dua backend, Nginx) dengan volume sendiri, kata sandi
# fiktif acak, dan satu port di 127.0.0.1:55081. Yang TIDAK disentuh: proyek asli libraryku-project1, container, volume,
# dan datanya, serta port 8081. Setelah selesai stack, volume uji, dan image uji dihapus dengan nama eksplisit
# (tidak memakai "down -v"). Hasil disimpan di bukti/peminjaman/ tanpa kata sandi.
#
#   ./scripts/uji_peminjaman.sh
set -eu
cd "$(dirname "$0")/.."
case "$(pwd)" in *Unduhan*) echo "Jalankan dari folder proyek di ~/LibraryKu_UIUX, bukan salinan di Unduhan." >&2; exit 2 ;; esac
[ -f database/migrations/002_peminjaman.sql ] || { echo "Jalankan dari branch yang memuat fitur peminjaman." >&2; exit 2; }

P=libraryku-uji
PORT=55081
BASE="http://127.0.0.1:$PORT"
TMP="$(mktemp -d)"
ENVF="$TMP/env"; AUTHDIR="$TMP/auth"; EMPTYDIR="$TMP/kosong"
mkdir -p "$AUTHDIR" "$EMPTYDIR" bukti/peminjaman
chmod 755 "$TMP" "$AUTHDIR" "$EMPTYDIR"   # worker Nginx (uid non-root) harus bisa membaca berkas login uji
rnd() { openssl rand -hex 12; }
UJI_USER=petugas_uji
UJI_PASS="$(rnd)"
{ echo "POSTGRES_PASSWORD=$(rnd)"; echo "MONGO_ROOT_PASSWORD=$(rnd)"; echo "MONGO_APP_PASSWORD=$(rnd)"; } > "$ENVF"; chmod 600 "$ENVF"
printf '%s:%s\n' "$UJI_USER" "$(openssl passwd -apr1 "$UJI_PASS")" > "$AUTHDIR/htpasswd"; chmod 644 "$AUTHDIR/htpasswd"
UJI_CONF="$PWD/nginx/default.conf"   # konfigurasi Nginx yang diuji (mode terbuka, bawaan repositori)
export UJI_USER UJI_PASS UJI_AUTH_DIR="$AUTHDIR" UJI_CONF

# sudo membuang variabel lingkungan, jadi UJI_AUTH_DIR dan UJI_CONF diteruskan eksplisit lewat "env".
dc() { sudo env UJI_AUTH_DIR="$UJI_AUTH_DIR" UJI_CONF="$UJI_CONF" docker compose -p "$P" --env-file "$ENVF" -f compose.yaml -f scripts/uji-peminjaman.compose.yaml "$@"; }
psqlc() { dc exec -T database psql -v ON_ERROR_STOP=1 -U libraryku_user -d libraryku "$@"; }
hash_books() { psqlc -Atc "SELECT count(*) || ':' || coalesce(md5(string_agg(t::text, ',' ORDER BY id)), '') FROM books t"; }
waitup() { for _ in $(seq 1 60); do curl -sf -m 3 "$BASE/api/sql/health" >/dev/null 2>&1 && return 0; sleep 2; done; echo "Stack uji tidak merespons." >&2; return 1; }

sudo -v   # minta kata sandi sudo sekali di awal
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="bukti/peminjaman/uji_${STAMP}.txt"
exec > >(tee -a "$OUT") 2>&1
echo "=== UJI PEMINJAMAN pada stack sementara '$P' | $(date '+%F %T %Z') ==="

# Pengaman: pastikan perintah benar-benar menarget proyek uji dan hanya membuka port uji.
CFG="$(dc config --format json)"
NAME="$(printf '%s' "$CFG" | python3 -c 'import sys,json; print(json.load(sys.stdin)["name"])')"
PORTS="$(printf '%s' "$CFG" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(sorted({str(p.get("published")) for s in d["services"].values() for p in s.get("ports",[])}))')"
[ "$NAME" = "$P" ] || { echo "BERHENTI: nama proyek '$NAME' bukan '$P'." >&2; rm -rf "$TMP"; exit 2; }
[ "$PORTS" = "['$PORT']" ] || { echo "BERHENTI: port yang dipublikasikan $PORTS bukan hanya $PORT." >&2; rm -rf "$TMP"; exit 2; }
echo "[OK] target proyek '$NAME', port dipublikasikan: $PORTS (proyek asli dan port 8081 tidak disentuh)"

cleanup() {
  set +e
  echo; echo "--- membersihkan stack uji ---"
  dc down --remove-orphans >/dev/null 2>&1
  sudo docker volume rm "${P}_postgres_data" "${P}_mongo_data" >/dev/null 2>&1
  sudo docker image rm "${P}-backend" "${P}-backend-nosql" >/dev/null 2>&1
  rm -rf "$TMP"
  echo "[OK] stack uji, volume uji, dan image uji dihapus. Hasil: $OUT"
}
trap cleanup EXIT

FAILS=0
run() { echo; echo ">>> $*"; "$@" || { FAILS=$((FAILS + 1)); echo "[GAGAL] $*"; }; }

echo; echo "=== 1. Membangun dan menjalankan stack uji (build backend dari kode terbaru) ==="
dc up -d --build --wait --wait-timeout 300
waitup
echo "[OK] stack uji berjalan di $BASE"

echo; echo "=== 2. Database yang sudah berisi buku, SEBELUM migrasi ==="
psqlc -c "INSERT INTO books (title, author, category, year, stock) VALUES ('[UJI-DB] Buku lama 1','Penulis Lama','Umum',2019,4),('[UJI-DB] Buku lama 2','Penulis Lama','Teknologi',2021,0),('[UJI-DB] Buku lama 3','Penulis Lama','Sejarah',2015,9)"
run python3 scripts/test_peminjaman.py "$BASE" sebelum

echo; echo "=== 3. Migrasi pada database berisi data ==="
H1="$(hash_books)"; echo "tabel books sebelum migrasi : $H1"
psqlc -f - < database/migrations/002_peminjaman.sql
echo "--- migrasi kedua kali (harus aman) ---"
psqlc -f - < database/migrations/002_peminjaman.sql
H2="$(hash_books)"; echo "tabel books sesudah migrasi : $H2"
TBL="$(psqlc -Atc "SELECT to_regclass('public.loans')")"
if [ "$H1" = "$H2" ] && [ "$TBL" = "loans" ]; then echo "PASS migrasi: data buku identik (jumlah dan isi) dan tabel loans ada"; else echo "FAIL migrasi: H1=$H1 H2=$H2 tabel=$TBL"; FAILS=$((FAILS + 1)); fi

echo; echo "=== 4. MODE TERBUKA (bawaan): peminjaman tanpa login dan fungsi lengkapnya ==="
run python3 scripts/test_peminjaman.py "$BASE" terbuka
sleep 3
run python3 scripts/test_peminjaman.py "$BASE" fungsional

echo; echo "=== 5. Regresi CRUD katalog SQL dan NoSQL, keamanan, dan akses ==="
sleep 4; run python3 scripts/test_api.py "$BASE"
sleep 4; run python3 scripts/test_keamanan.py "$BASE"
sleep 6; run python3 scripts/test_akses.py "$BASE"

echo; echo "=== 6. Tampilan (Firefox): halaman Peminjaman dan regresi UI katalog ==="
sleep 4; run env LIBRARYKU_BASE="$BASE" python3 scripts/run_ui_peminjaman.py "$TMP/ui_peminjaman.txt"
sleep 3; run env LIBRARYKU_BASE="$BASE" UI_TEST_OUT="$TMP/ui_lama.txt" python3 scripts/run_ui_test.py >"$TMP/ui_lama_stdout.txt" 2>&1
UI_OK="$(grep -c '^PASS' "$TMP/ui_lama.txt" 2>/dev/null || true)"; UI_NO="$(grep -c '^FAIL' "$TMP/ui_lama.txt" 2>/dev/null || true)"
echo "UI katalog (regresi): ${UI_OK:-0} PASS, ${UI_NO:-0} FAIL"
[ "${UI_NO:-0}" = "0" ] && [ "${UI_OK:-0}" != "0" ] || { FAILS=$((FAILS + 1)); echo "[GAGAL] regresi UI katalog"; }
grep '^FAIL' "$TMP/ui_lama.txt" 2>/dev/null || true

echo; echo "=== 7. MODE LOGIN PETUGAS diaktifkan (satu baris LOANS_AUTH diubah): semua endpoint terkunci ==="
LOGIN_CONF="$TMP/default-login.conf"
sed 's/default off;  # LOANS_AUTH/default "LibraryKu Petugas";  # LOANS_AUTH/' nginx/default.conf > "$LOGIN_CONF"; chmod 644 "$LOGIN_CONF"
[ "$(diff nginx/default.conf "$LOGIN_CONF" | grep -c '^>')" = "1" ] || { echo "BERHENTI: konfigurasi login tidak terbentuk tepat satu baris berbeda." >&2; exit 2; }
UJI_CONF="$LOGIN_CONF" dc up -d --force-recreate --no-deps frontend
waitup || true
sleep 4; run python3 scripts/test_peminjaman.py "$BASE" akses

echo; echo "=== 8. Gagal tertutup: login aktif tetapi berkas login petugas tidak ada ==="
UJI_CONF="$LOGIN_CONF" UJI_AUTH_DIR="$EMPTYDIR" dc up -d --force-recreate --no-deps frontend
waitup || true
sleep 4; run python3 scripts/test_peminjaman.py "$BASE" failclosed

echo; echo "=== RINGKASAN: $FAILS tahap gagal ==="
[ "$FAILS" -eq 0 ] && echo "SEMUA TAHAP LULUS" || echo "ADA TAHAP GAGAL (lihat baris FAIL di atas)"
exit "$FAILS"
