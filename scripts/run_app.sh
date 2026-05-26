#!/usr/bin/env bash
# Start FastAPI + Streamlit secara berbarengan.
# - Headless Streamlit (skip prompt email)
# - Pre-check port supaya error jelas, bukan cascading shutdown
# - Salah satu service crash != bunuh service lainnya
set -uo pipefail

cd "$(dirname "$0")/.."

# Aktifkan venv jika ada.
if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-8501}"
export API_URL="${API_URL:-http://localhost:${API_PORT}}"

# Bypass prompt email dari Streamlit (first-run telemetry registration).
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
mkdir -p "${HOME}/.streamlit"
if [ ! -f "${HOME}/.streamlit/credentials.toml" ]; then
  cat > "${HOME}/.streamlit/credentials.toml" <<EOF
[general]
email = ""
EOF
fi

# Cek port konflik sebelum start.
port_in_use() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
if port_in_use "${API_PORT}"; then
  echo "ERROR: port ${API_PORT} sudah dipakai. Set API_PORT=<port> atau matikan proses yang pakai."
  lsof -nP -iTCP:"${API_PORT}" -sTCP:LISTEN
  exit 1
fi
if port_in_use "${UI_PORT}"; then
  echo "ERROR: port ${UI_PORT} sudah dipakai. Set UI_PORT=<port> atau matikan proses yang pakai."
  lsof -nP -iTCP:"${UI_PORT}" -sTCP:LISTEN
  exit 1
fi

# Pastikan artifacts ada.
if [ ! -f models/serving_artifacts.json ]; then
  echo ">> models/serving_artifacts.json tidak ada, generate dulu..."
  python -m app.build_artifacts
fi

echo ">> FastAPI  : http://localhost:${API_PORT}/docs"
echo ">> Streamlit: http://localhost:${UI_PORT}"
echo ">> Tekan Ctrl+C untuk stop keduanya."
echo ""

uvicorn app.api:app --port "${API_PORT}" --host 0.0.0.0 &
API_PID=$!

streamlit run app/streamlit_app.py \
  --server.port "${UI_PORT}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false &
UI_PID=$!

cleanup() {
  echo ""
  echo ">> Shutting down..."
  kill "${API_PID}" "${UI_PID}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup INT TERM

# Polling loop (portable; macOS bash 3.2 tidak punya `wait -n`).
while kill -0 "${API_PID}" 2>/dev/null && kill -0 "${UI_PID}" 2>/dev/null; do
  sleep 1
done

if ! kill -0 "${API_PID}" 2>/dev/null; then
  echo ">> FastAPI (PID ${API_PID}) berhenti tak terduga. Periksa log di atas."
fi
if ! kill -0 "${UI_PID}" 2>/dev/null; then
  echo ">> Streamlit (PID ${UI_PID}) berhenti tak terduga. Periksa log di atas."
fi

cleanup
