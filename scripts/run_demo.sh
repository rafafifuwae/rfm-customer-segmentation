#!/usr/bin/env bash
# Demo deployment via Cloudflare Tunnel.
# - Start FastAPI + Streamlit lokal
# - Buka tunnel publik untuk Streamlit (port 8501)
# - Print URL publik yang bisa dishare ke dosen
#
# Catatan:
# - Komputer & koneksi internet HARUS tetap nyala selama demo.
# - URL berubah setiap kali script dijalankan ulang.
# - Tekan Ctrl+C untuk stop semua service.
set -uo pipefail

cd "$(dirname "$0")/.."

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "ERROR: cloudflared belum terinstal."
  echo "Install dulu: brew install cloudflared"
  exit 1
fi

API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-8501}"
export API_URL="${API_URL:-http://localhost:${API_PORT}}"

# Skip prompt email Streamlit
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
mkdir -p "${HOME}/.streamlit"
if [ ! -f "${HOME}/.streamlit/credentials.toml" ]; then
  printf '[general]\nemail = ""\n' > "${HOME}/.streamlit/credentials.toml"
fi

# Cek port konflik
port_in_use() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
if port_in_use "${API_PORT}"; then
  echo "ERROR: port ${API_PORT} sudah dipakai. Stop dulu prosesnya."
  lsof -nP -iTCP:"${API_PORT}" -sTCP:LISTEN
  exit 1
fi
if port_in_use "${UI_PORT}"; then
  echo "ERROR: port ${UI_PORT} sudah dipakai. Stop dulu prosesnya."
  lsof -nP -iTCP:"${UI_PORT}" -sTCP:LISTEN
  exit 1
fi

# Pastikan serving artifacts ada
if [ ! -f models/serving_artifacts.json ]; then
  echo ">> Generate serving artifacts dulu..."
  python -m app.build_artifacts
fi

LOG_DIR=$(mktemp -d)
echo ">> Log dir: ${LOG_DIR}"

# Start FastAPI
echo ">> Starting FastAPI di port ${API_PORT}..."
uvicorn app.api:app --port "${API_PORT}" --host 127.0.0.1 \
  > "${LOG_DIR}/api.log" 2>&1 &
API_PID=$!

# Start Streamlit
echo ">> Starting Streamlit di port ${UI_PORT}..."
streamlit run app/streamlit_app.py \
  --server.port "${UI_PORT}" \
  --server.address 127.0.0.1 \
  --server.headless true \
  --browser.gatherUsageStats false \
  > "${LOG_DIR}/ui.log" 2>&1 &
UI_PID=$!

# Tunggu Streamlit ready
echo ">> Tunggu Streamlit ready..."
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${UI_PORT}/_stcore/health" >/dev/null 2>&1; then
    echo ">> Streamlit ready setelah ${i}s"
    break
  fi
  sleep 1
done

# Start Cloudflare Tunnel
echo ">> Starting Cloudflare Tunnel..."
cloudflared tunnel --url "http://localhost:${UI_PORT}" \
  > "${LOG_DIR}/tunnel.log" 2>&1 &
TUNNEL_PID=$!

cleanup() {
  echo ""
  echo ">> Shutting down..."
  kill "${API_PID}" "${UI_PID}" "${TUNNEL_PID}" 2>/dev/null || true
  wait 2>/dev/null || true
  echo ">> Logs masih di: ${LOG_DIR}"
}
trap cleanup INT TERM

# Tunggu URL publik muncul di log cloudflared (biasanya 5-15 detik)
echo ">> Tunggu URL publik dari Cloudflare..."
PUBLIC_URL=""
for i in $(seq 1 60); do
  PUBLIC_URL=$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' \
               "${LOG_DIR}/tunnel.log" 2>/dev/null | head -1)
  if [ -n "${PUBLIC_URL}" ]; then
    break
  fi
  sleep 1
done

clear
echo "============================================================"
echo "  🚀 DEMO READY"
echo "============================================================"
echo ""
if [ -n "${PUBLIC_URL}" ]; then
  echo "  🌐 URL PUBLIK (share ke dosen):"
  echo ""
  echo "     ${PUBLIC_URL}"
  echo ""
  # Copy ke clipboard kalau ada pbcopy (macOS)
  if command -v pbcopy >/dev/null 2>&1; then
    echo -n "${PUBLIC_URL}" | pbcopy
    echo "     (sudah di-copy ke clipboard)"
  fi
else
  echo "  ⚠️  URL publik belum keluar setelah 60 detik."
  echo "     Cek log: cat ${LOG_DIR}/tunnel.log"
fi
echo ""
echo "  💻 Akses lokal:"
echo "     UI       : http://localhost:${UI_PORT}"
echo "     API docs : http://localhost:${API_PORT}/docs"
echo ""
echo "  📁 Logs: ${LOG_DIR}/"
echo ""
echo "  Tekan Ctrl+C untuk stop demo."
echo "============================================================"

# Tunggu salah satu mati
while kill -0 "${API_PID}" 2>/dev/null \
   && kill -0 "${UI_PID}" 2>/dev/null \
   && kill -0 "${TUNNEL_PID}" 2>/dev/null; do
  sleep 2
done

echo ">> Salah satu service berhenti. Periksa log."
cleanup
