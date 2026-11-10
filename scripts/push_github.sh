#!/usr/bin/env bash
# Mengunggah commit lokal ke repo GitHub muhrafi-fsdev/libraryku-unified tanpa GitHub CLI.
# Token dibaca lewat prompt tersembunyi (read -s), dipakai lewat GIT_ASKPASS sementara, dan tidak disimpan
# di berkas konfigurasi git, riwayat shell, atau argumen perintah.
# Prasyarat: repo KOSONG dengan nama libraryku-unified sudah dibuat di github.com (Public, tanpa README/.gitignore/license),
# dan token fine-grained dengan izin "Contents: Read and write" untuk repo itu.
set -eu
cd "$(dirname "$0")/.."
case "$(pwd)" in *Unduhan*) echo "Jalankan dari ~/LibraryKu_UIUX/LibraryKu_Project1." >&2; exit 2 ;; esac
USERNAME="muhrafi-fsdev"; REPO="libraryku-unified"; URL="https://github.com/$USERNAME/$REPO.git"
git rev-parse --is-inside-work-tree >/dev/null
[ -z "$(git status --porcelain)" ] || { echo "Ada perubahan belum di-commit; commit dulu." >&2; exit 1; }
git ls-files | grep -qE '(^|/)\.env$|htpasswd|credentials' && { echo "BERHENTI: berkas rahasia ikut ter-track." >&2; exit 1; } || true
echo "Akan mendorong $(git rev-list --count HEAD) commit ($(git ls-files | wc -l) berkas) ke $URL${PUSH_FORCE:+ (PUSH_FORCE=1: menimpa riwayat lama di GitHub)}"
printf 'Lanjut? [y/N] '; read -r a; case "$a" in y|Y|ya|YA|Ya) ;; *) echo "Dibatalkan."; exit 0 ;; esac
printf 'Tempel TOKEN GitHub (tidak terlihat), lalu Enter: '; read -rs RAW; echo
# Ambil hanya token yang valid dari teks yang ditempel (membuang spasi, baris baru, dan sisa urutan escape terminal).
TOKEN="$(printf '%s' "$RAW" | grep -oE '(github_pat_[A-Za-z0-9_]+|gh[pousr]_[A-Za-z0-9]+)' | head -1 || true)"
unset RAW
[ -n "$TOKEN" ] || { echo "Teks yang ditempel bukan token GitHub (harus diawali github_pat_ atau ghp_). Salin ulang token dan tempel dengan Ctrl+Shift+V." >&2; exit 1; }
echo "Token terbaca: ${#TOKEN} karakter, awalan ${TOKEN%%_*}_ (isi tidak ditampilkan)"
# Uji token ke GitHub sebelum push (hanya status HTTP yang dicetak).
U="$(printf 'Authorization: Bearer %s\n' "$TOKEN" | curl -s -m 20 -o /dev/null -w '%{http_code}' -H @- https://api.github.com/user || true)"
R="$(printf 'Authorization: Bearer %s\n' "$TOKEN" | curl -s -m 20 -o /dev/null -w '%{http_code}' -H @- "https://api.github.com/repos/$USERNAME/$REPO" || true)"
echo "Uji token: akun (/user) -> HTTP $U ; repo $REPO -> HTTP $R"
[ "$U" = "200" ] || { echo "Token ditolak GitHub (kedaluwarsa/salah/dihapus). Buat token baru, lalu ulangi." >&2; exit 1; }
[ "$R" = "200" ] || { echo "Token tidak punya akses ke repo $REPO. Pastikan Repository access = Only select repositories -> $REPO." >&2; exit 1; }
ASK="$(mktemp)"; chmod 700 "$ASK"
printf '#!/bin/sh\ncase "$1" in *sername*) echo "%s" ;; *) printf "%%s" "$GH_PUSH_TOKEN" ;; esac\n' "$USERNAME" > "$ASK"
git remote get-url origin >/dev/null 2>&1 && git remote set-url origin "$URL" || git remote add origin "$URL"
# PUSH_FORCE=1 menimpa riwayat di GitHub (dipakai setelah riwayat lokal ditulis ulang). Bawaan: push biasa.
FORCE=""; [ "${PUSH_FORCE:-0}" = "1" ] && FORCE="--force"
GH_PUSH_TOKEN="$TOKEN" GIT_ASKPASS="$ASK" GIT_TERMINAL_PROMPT=0 git push $FORCE -u origin main
rm -f "$ASK"; unset TOKEN
echo "Selesai. Buka: https://github.com/$USERNAME/$REPO"
