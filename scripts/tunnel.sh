#!/usr/bin/env bash
# LibraryKu: kontrol Cloudflare Tunnel (cloudflared) di Kali. Dijalankan PENGGUNA (butuh sudo).
# Token tunnel TIDAK pernah disimpan di repository: dimasukkan lewat prompt tersembunyi (read -s).
# Keluaran disimpan ke bukti/publik/ (tanpa token).
#
#   ./scripts/tunnel.sh install              pasang cloudflared dari repositori resmi Cloudflare (apt)
#   ./scripts/tunnel.sh connect              daftarkan service cloudflared dengan token dari dashboard (prompt tersembunyi)
#   ./scripts/tunnel.sh status               versi, status service, aktif saat boot, log terakhir
#   ./scripts/tunnel.sh logs                 100 baris log cloudflared
#   ./scripts/tunnel.sh restart              restart service cloudflared
#   ./scripts/tunnel.sh check <hostname>     uji dari Kali lewat hostname publik: HTTPS, sertifikat, Access, tulis anonim ditolak
#   ./scripts/tunnel.sh uninstall            hapus service cloudflared (tunnel di dashboard tidak dihapus)
#
# Opsi: --yes melewati konfirmasi. Skrip tidak menyentuh Docker, database, atau konfigurasi proyek lain.
set -eu
cd "$(dirname "$0")/.."
ACTION="${1:-}"; [ $# -gt 0 ] && shift || true
ASSUME_YES=0; ARG=""
for a in "$@"; do case "$a" in --yes|-y) ASSUME_YES=1 ;; *) ARG="$a" ;; esac; done
mkdir -p bukti/publik
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="bukti/publik/tunnel_${ACTION:-bantuan}_${STAMP}.txt"
say() { printf '%s\n' "$*"; }
confirm() { [ "$ASSUME_YES" = 1 ] && return 0; printf '%s\nLanjut? [y/N] ' "$1"; read -r r; case "$r" in y|Y|ya|YA|Ya) return 0 ;; *) say "Dibatalkan."; exit 0 ;; esac; }

run() {
case "$ACTION" in
install)
  say "=== INSTALL cloudflared | $(date '+%F %T %Z') ==="
  confirm "Aksi: menambah repositori apt resmi Cloudflare (pkg.cloudflare.com) dan memasang paket cloudflared. Tidak ada tunnel yang dibuat atau dijalankan."
  sudo mkdir -p --mode=0755 /usr/share/keyrings
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
  echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y cloudflared
  cloudflared --version ;;
connect)
  say "=== CONNECT: daftarkan service cloudflared | $(date '+%F %T %Z') ==="
  command -v cloudflared >/dev/null || { say "cloudflared belum terpasang. Jalankan: ./scripts/tunnel.sh install"; exit 1; }
  say "Sebelum lanjut, pastikan di dashboard Cloudflare: (1) aplikasi Access untuk hostname sudah dibuat dan kebijakannya benar, (2) tunnel sudah dibuat dan token disalin."
  confirm "Aksi: memasang service systemd 'cloudflared' (aktif otomatis saat boot) memakai token Anda. Rute hostname baru ditambahkan di dashboard SETELAH Access siap."
  printf 'Tempel TOKEN tunnel (tidak akan terlihat), lalu Enter: '; read -rs TOKEN; echo
  [ -n "$TOKEN" ] || { say "Token kosong."; exit 1; }
  sudo cloudflared service install "$TOKEN"
  unset TOKEN
  # unit systemd bisa dibaca semua pengguna secara bawaan: batasi karena memuat token
  sudo chmod 600 /etc/systemd/system/cloudflared.service 2>/dev/null || true
  sudo systemctl daemon-reload
  sudo systemctl enable --now cloudflared
  sleep 5
  systemctl is-active cloudflared; systemctl is-enabled cloudflared ;;
status)
  say "=== STATUS | $(date '+%F %T %Z') ==="
  cloudflared --version 2>&1 | head -1 || say "cloudflared belum terpasang"
  say "aktif: $(systemctl is-active cloudflared 2>&1)   saat boot: $(systemctl is-enabled cloudflared 2>&1)"
  say "--- log terakhir (token tidak dicetak) ---"
  sudo journalctl -u cloudflared -n 25 --no-pager 2>&1 | sed -E 's/(eyJ[A-Za-z0-9_-]{20,})/<token-disamarkan>/g' | cut -c1-200
  say "--- port lokal ---"; ss -ltn | grep ':8081' || say "(8081 tidak mendengarkan)" ;;
logs)
  sudo journalctl -u cloudflared -n 100 --no-pager 2>&1 | sed -E 's/(eyJ[A-Za-z0-9_-]{20,})/<token-disamarkan>/g' | cut -c1-220 ;;
restart)
  confirm "Aksi: restart service cloudflared (akses publik putus beberapa detik; website lokal tidak terpengaruh)."
  sudo systemctl restart cloudflared; sleep 4; systemctl is-active cloudflared ;;
check)
  H="${ARG:?Pakai: ./scripts/tunnel.sh check libraryku.contoh.com}"
  say "=== CHECK https://$H | $(date '+%F %T %Z') (dari Kali; bukan bukti akses dari luar jaringan) ==="
  say "--- 1. HTTPS dan sertifikat TLS ---"
  echo | openssl s_client -connect "$H:443" -servername "$H" 2>/dev/null | openssl x509 -noout -subject -issuer -dates 2>&1 | head -4
  say "--- 2. Halaman utama tanpa login Access (harus dialihkan ke login Cloudflare Access) ---"
  curl -s -m 15 -o /dev/null -w "GET / -> HTTP %{http_code}  alihkan ke: %{redirect_url}\n" "https://$H/" | sed -E 's#(https://[^/]+/cdn-cgi/access/login/[^?]*)\?.*#\1?...#'
  say "--- 3. API tanpa login Access (harus ditolak/dialihkan, bukan 200) ---"
  for p in /api/sql/health /api/nosql/books; do curl -s -m 15 -o /dev/null -w "GET $p -> HTTP %{http_code}\n" "https://$H$p"; done
  say "--- 4. Tulis tanpa login (harus ditolak) ---"
  curl -s -m 15 -o /dev/null -w "POST /api/sql/books -> HTTP %{http_code}\n" -X POST -H 'Content-Type: application/json' -H 'X-Requested-With: libraryku' -d '{}' "https://$H/api/sql/books"
  curl -s -m 15 -o /dev/null -w "DELETE /api/nosql/books/507f1f77bcf86cd799439011 -> HTTP %{http_code}\n" -X DELETE -H 'X-Requested-With: libraryku' "https://$H/api/nosql/books/507f1f77bcf86cd799439011"
  say "--- 5. HTTP biasa dialihkan ke HTTPS? ---"
  curl -s -m 15 -o /dev/null -w "http://$H/ -> HTTP %{http_code}  alihkan ke: %{redirect_url}\n" "http://$H/" | sed -E 's#\?.*#?...#' ;;
uninstall)
  confirm "Aksi: menghapus service cloudflared dari Kali (akses publik mati). Tunnel di dashboard Cloudflare tidak dihapus."
  sudo cloudflared service uninstall; say "service dihapus." ;;
*) sed -n '2,15p' "$0"; exit 1 ;;
esac
}
run 2>&1 | tee "$OUT"
say ""; say "Hasil disimpan di: $OUT"
