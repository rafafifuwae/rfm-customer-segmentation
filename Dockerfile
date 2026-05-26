# RFM Customer Segmentation — FastAPI + Streamlit dalam satu container.
# Cocok untuk Hugging Face Spaces (port 7860 = Streamlit publik).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    API_URL=http://127.0.0.1:8000

WORKDIR /app

# Install dependencies dulu untuk leverage layer cache
COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

# Install curl untuk healthcheck di start.sh
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy file aplikasi (data raw & notebooks di-exclude via .dockerignore)
COPY app/         ./app/
COPY src/         ./src/
COPY models/      ./models/
COPY params.yaml  ./
COPY start.sh     ./

# Pastikan launcher executable & artifact serving sudah ada
RUN chmod +x start.sh && \
    test -f models/kmeans_rfm.pkl || (echo "models/kmeans_rfm.pkl tidak ada" && exit 1) && \
    test -f models/serving_artifacts.json || (echo "models/serving_artifacts.json tidak ada" && exit 1)

# HF Spaces & user lain bisa override port via $PORT
ENV PORT=7860
EXPOSE 7860

CMD ["./start.sh"]
