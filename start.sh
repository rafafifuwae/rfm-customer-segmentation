#!/usr/bin/env bash
# Launcher container: start FastAPI di internal port 8000,
# lalu Streamlit di $PORT (default 7860) sebagai foreground process.
set -e

API_PORT="${API_PORT:-8000}"
UI_PORT="${PORT:-7860}"

echo ">> Starting FastAPI on localhost:${API_PORT}"
uvicorn app.api:app --host 127.0.0.1 --port "${API_PORT}" --log-level warning &
API_PID=$!

# Tunggu sampai API siap (max ~30 detik)
echo ">> Waiting for FastAPI health..."
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1; then
    echo ">> FastAPI ready after ${i}s"
    break
  fi
  if ! kill -0 "${API_PID}" 2>/dev/null; then
    echo ">> ERROR: FastAPI crashed during startup"
    exit 1
  fi
  sleep 1
done

echo ">> Starting Streamlit on 0.0.0.0:${UI_PORT}"
exec streamlit run app/streamlit_app.py \
  --server.port "${UI_PORT}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableXsrfProtection false \
  --server.enableCORS false \
  --browser.gatherUsageStats false
