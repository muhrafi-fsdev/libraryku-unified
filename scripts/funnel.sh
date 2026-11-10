#!/usr/bin/env bash
# LibraryKu: akses publik HTTPS lewat Tailscale Funnel. Dijalankan PENGGUNA (butuh sudo untuk beberapa aksi).
# Funnel meneruskan https://<nama>.<tailnet>.ts.net ke Nginx LibraryKu di 127.0.0.1:8081. TLS dikelola Tailscale.
# Tidak ada token/kunci yang disimpan di repository. Keluaran disimpan ke bukti/publik/ (tanpa rahasia).
#
#   ./scripts/funnel.sh install       pasang Tailscale (skrip instalasi resmi tailscale.com, diunduh dulu ke berkas)
#   ./scripts/funnel.sh login         masuk ke akun Tailscale (membuka URL persetujuan perangkat)
#   ./scripts/funnel.sh enable        aktifkan Funnel ke 127.0.0.1:8081 (menolak bila perlindungan CSRF belum aktif)
#   ./scripts/funnel.sh status        status Tailscale, Funnel, URL publik, aktif saat boot
#   ./scripts/funnel.sh check         uji dari Kali lewat URL publik: sertifikat TLS, baca, tulis tanpa header aplikasi ditolak
#   ./scripts/funnel.sh logs          log tailscaled
#   ./scripts/funnel.sh off           matikan Funnel (akses publik putus; website lokal tetap jalan)
#
# Opsi: --yes melewati konfirmasi. Skrip tidak menyentuh Docker, database, atau proyek lain.
set -eu
cd "$(dirname "$0")/.."
ACTION="${1:-}"; [ $# -gt 0 ] && shift || true
ASSUME_YES=0
for a in "$@"; do case "$a" in --yes|-y) ASSUME_YES=1 ;; *) echo "Argumen tidak dikenal: $a" >&2; exit 2 ;; esac; done
mkdir -p bukti/publik
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="bukti/publik/funnel_${ACTION:-bantuan}_${STAMP}.txt"
LOCAL="http://127.0.0.1:8081"
say() { printf '%s\n' "$*"; }
confirm() { [ "$ASSUME_YES" = 1 ] && return 0; printf '%s\nLanjut? [y/N] ' "$1"; read -r r; case "$r" in y|Y|ya|YA|Ya) return 0 ;; *) say "Dibatalkan."; exit 0 ;; esac; }
need_ts() { command -v tailscale >/dev/null || { say "Tailscale belum terpasang. Jalankan: ./scripts/funnel.sh install"; exit 1; }; }
dns_name() { sudo tailscale status --json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print((d.get('Self') or {}).get('DNSName','').rstrip('.'))" 2>/dev/null || true; }

run() {
case "$ACTION" in
install)
  say "=== INSTALL Tailscale | $(date '+%F %T %Z') ==="
  confirm "Aksi: mengunduh skrip instalasi resmi dari tailscale.com ke berkas sementara, lalu menjalankannya (menambah repositori apt Tailscale dan memasang paket tailscale, service tailscaled aktif saat boot). Belum ada akun yang dihubungkan dan belum ada yang dipublikasikan."
  TMP="$(mktemp /tmp/tailscale-install.XXXXXX.sh)"
  curl -fsSL https://tailscale.com/install.sh -o "$TMP"
  say "sha256 skrip: $(sha256sum "$TMP" | cut -c1-64)"
  sh "$TMP"; rm -f "$TMP"
  tailscale version | head -1
  say "tailscaled: aktif=$(systemctl is-active tailscaled) boot=$(systemctl is-enabled tailscaled)" ;;
login)
  need_ts
  say "=== LOGIN | $(date '+%F %T %Z') ==="
  confirm "Aksi: menghubungkan Kali ke akun Tailscale Anda sebagai perangkat bernama 'libraryku-kali'. Skrip akan mencetak URL; buka di browser dan setujui perangkat. Tidak ada kunci yang disimpan di repository."
  sudo tailscale up --hostname=libraryku-kali
  say "terhubung sebagai: $(dns_name)" ;;
enable)
  need_ts
  say "=== ENABLE FUNNEL | $(date '+%F %T %Z') ==="
  say "--- pemeriksaan keamanan sebelum dipublikasikan ---"
  CODE="$(curl -s -m 10 -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "$LOCAL/api/sql/books" || true)"
  say "POST tanpa header aplikasi ke $LOCAL/api/sql/books -> HTTP $CODE (harus 403)"
  if [ "$CODE" != "403" ]; then
    say "[DITOLAK] Perlindungan CSRF (header X-Requested-With) belum aktif. Jalankan dulu: ./scripts/ctl.sh reload-nginx, lalu ulangi."
    exit 1
  fi
  say "[OK] perlindungan CSRF aktif"
  confirm "Aksi: mempublikasikan Nginx LibraryKu (127.0.0.1:8081) ke INTERNET lewat Tailscale Funnel dengan HTTPS. Siapa pun yang tahu alamatnya dapat MELIHAT koleksi; mengubah data TIDAK memakai login (mode terbuka), hanya dilindungi header aplikasi dan pembatasan laju. Yang dipublikasikan hanya port 8081, bukan database atau port lain."
  sudo tailscale funnel --bg 8081
  sleep 3
  sudo tailscale funnel status
  H="$(dns_name)"; [ -n "$H" ] && say "URL publik: https://$H/" ;;
status)
  need_ts
  say "=== STATUS | $(date '+%F %T %Z') ==="
  tailscale version | head -1
  say "tailscaled: aktif=$(systemctl is-active tailscaled) boot=$(systemctl is-enabled tailscaled)"
  sudo tailscale status 2>&1 | head -6 | sed -E 's/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/<ip-tailnet>/g'
  say "--- Funnel ---"; sudo tailscale funnel status 2>&1
  H="$(dns_name)"; [ -n "$H" ] && say "Nama DNS: $H"
  say "--- port lokal ---"; ss -ltn | grep ':8081' || say "(8081 tidak mendengarkan)" ;;
check)
  need_ts
  H="$(dns_name)"; [ -n "$H" ] || { say "Perangkat belum login ke Tailscale."; exit 1; }
  say "=== CHECK https://$H | $(date '+%F %T %Z') (dari Kali; BUKAN bukti akses dari luar jaringan) ==="
  say "--- 1. HTTPS dan sertifikat TLS ---"
  echo | openssl s_client -connect "$H:443" -servername "$H" 2>/dev/null | openssl x509 -noout -subject -issuer -dates 2>&1 | head -4
  say "--- 2. Halaman dan API baca (terbuka) ---"
  for p in / /api/sql/health /api/nosql/health /api/sql/books; do curl -s -m 20 -o /dev/null -w "GET $p -> HTTP %{http_code}\n" "https://$H$p"; done
  say "--- 3. Tulis dengan header aplikasi tetapi data kosong (harus 400 validasi; tidak membuat data) ---"
  curl -s -m 20 -o /dev/null -w "POST /api/sql/books -> HTTP %{http_code}\n" -X POST -H 'Content-Type: application/json' -H 'X-Requested-With: libraryku' -d '{}' "https://$H/api/sql/books"
  curl -s -m 20 -o /dev/null -w "POST /api/nosql/books -> HTTP %{http_code}\n" -X POST -H 'Content-Type: application/json' -H 'X-Requested-With: libraryku' -d '{}' "https://$H/api/nosql/books"
  curl -s -m 20 -o /dev/null -w "DELETE id yang tidak ada -> HTTP %{http_code}\n" -X DELETE -H 'X-Requested-With: libraryku' "https://$H/api/nosql/books/507f1f77bcf86cd799439011"
  say "--- 4. Tulis tanpa header aplikasi (harus 403) ---"
  curl -s -m 20 -o /dev/null -w "POST tanpa header -> HTTP %{http_code}\n" -X POST -H 'Content-Type: application/json' -d '{}' "https://$H/api/sql/books"
  say "--- 5. Port 80/HTTP tidak dipakai Funnel (hanya 443) ---"
  curl -s -m 8 -o /dev/null -w "http://$H/ -> HTTP %{http_code}\n" "http://$H/" || say "http:// tidak terjangkau (wajar: hanya HTTPS)" ;;
logs)
  sudo journalctl -u tailscaled -n 100 --no-pager 2>&1 | cut -c1-220 ;;
off)
  need_ts
  confirm "Aksi: mematikan Funnel (akses publik berhenti). Website lokal 127.0.0.1:8081 dan Docker tidak terpengaruh. Perangkat tetap login di Tailscale."
  sudo tailscale funnel --https=443 8081 off 2>&1 || sudo tailscale funnel reset
  sudo tailscale funnel status 2>&1 ;;
*) sed -n '2,14p' "$0"; exit 1 ;;
esac
}
run 2>&1 | tee "$OUT"
say ""; say "Hasil disimpan di: $OUT"
