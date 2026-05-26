#!/usr/bin/env bash
# Upload semua file deployment ke Hugging Face Space.
# Pakai HF CLI (`hf upload`). Pastikan sudah login: `hf auth login`.
#
# Cara pakai:
#   ./scripts/deploy_hf.sh <username>/<space-name>
#
# Contoh:
#   ./scripts/deploy_hf.sh rafa-fawwaz/rfm-segmentation
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <username>/<space-name>"
  echo "Contoh: $0 rafa-fawwaz/rfm-segmentation"
  exit 1
fi

SPACE_ID="$1"

# Cek apakah sudah login
if ! hf auth whoami >/dev/null 2>&1; then
  echo "ERROR: Belum login ke Hugging Face."
  echo "  Run: hf auth login"
  exit 1
fi

# Cek artifacts wajib ada
for f in models/kmeans_rfm.pkl models/serving_artifacts.json; do
  if [ ! -f "$f" ]; then
    echo "ERROR: $f tidak ada. Jalankan dulu training + build_artifacts."
    exit 1
  fi
done

echo ">> Upload ke Space: ${SPACE_ID}"
echo "   File yang akan di-upload:"
echo "     - Dockerfile, start.sh, .dockerignore, README.md"
echo "     - requirements-deploy.txt, params.yaml"
echo "     - app/, src/, models/kmeans_rfm.pkl, models/serving_artifacts.json"
echo ""

# Upload satu per satu dengan target path yang jelas
hf upload "${SPACE_ID}" Dockerfile               --repo-type space
hf upload "${SPACE_ID}" start.sh                 --repo-type space
hf upload "${SPACE_ID}" .dockerignore            --repo-type space
hf upload "${SPACE_ID}" README.md                --repo-type space
hf upload "${SPACE_ID}" requirements-deploy.txt  --repo-type space
hf upload "${SPACE_ID}" params.yaml              --repo-type space

# Folder uploads (recursive)
hf upload "${SPACE_ID}" app/ app/                --repo-type space
hf upload "${SPACE_ID}" src/ src/                --repo-type space

# Hanya 2 file model yang dibutuhkan (skip metrics & kmeans_metrics.json optional)
hf upload "${SPACE_ID}" models/kmeans_rfm.pkl         models/kmeans_rfm.pkl         --repo-type space
hf upload "${SPACE_ID}" models/serving_artifacts.json models/serving_artifacts.json --repo-type space

echo ""
echo "✅ Upload selesai!"
echo "   Build akan otomatis trigger di HF."
echo "   Cek progress: https://huggingface.co/spaces/${SPACE_ID}"
echo ""
echo "   Setelah build selesai (~5-10 menit pertama kali),"
echo "   URL publik: https://${SPACE_ID/\//-}.hf.space"
