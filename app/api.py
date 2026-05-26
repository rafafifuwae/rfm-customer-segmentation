"""FastAPI service untuk segmentasi pelanggan RFM K-Means.

Jalankan:
    uvicorn app.api:app --reload --port 8000

Dokumentasi interaktif:
    http://localhost:8000/docs
"""
from __future__ import annotations

import io

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.predictor import get_predictor
from app.schemas import (
    BatchResponse,
    BatchRow,
    ClusterInfo,
    HealthOut,
    PredictionOut,
    RFMInput,
)

app = FastAPI(
    title="RFM Customer Segmentation API",
    description=(
        "Klasifikasi pelanggan ke segmen RFM (Champions, Loyal, At Risk, "
        "Hibernating/Lost) menggunakan K-Means yang dilatih pada dataset "
        "Brazilian E-Commerce Olist."
    ),
    version="1.0.0",
)

# CORS supaya Streamlit (atau frontend lain) bisa akses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "RFM Segmentation API. Lihat /docs untuk endpoint."}


@app.get("/health", response_model=HealthOut, tags=["meta"])
def health():
    p = get_predictor()
    return HealthOut(
        status="ok",
        n_training_samples=sum(c["n_customers"] for c in p.list_clusters()),
        feature_cols=p.feature_cols,
        n_clusters=len(p.cluster_profile),
    )


@app.get("/clusters", response_model=list[ClusterInfo], tags=["meta"])
def clusters():
    """Profil setiap cluster + segmen + rekomendasi strategi."""
    return get_predictor().list_clusters()


@app.post("/predict", response_model=PredictionOut, tags=["predict"])
def predict(payload: RFMInput):
    p = get_predictor()
    pred = p.predict_one(payload.Recency, payload.Frequency, payload.Monetary)
    return PredictionOut(
        cluster=pred.cluster,
        segment=pred.segment,
        distance_to_centroid=round(pred.distance_to_centroid, 4),
        strategy=pred.strategy,
        input=payload,
    )


@app.post("/predict/batch", response_model=BatchResponse, tags=["predict"])
async def predict_batch(file: UploadFile = File(...)):
    """Upload CSV dengan kolom: Recency, Frequency, Monetary.

    Kolom tambahan akan diabaikan tapi tetap dikembalikan di response.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, detail="File harus berupa .csv")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(400, detail=f"Gagal parse CSV: {e}")

    if df.empty:
        raise HTTPException(400, detail="CSV kosong.")
    if len(df) > 100_000:
        raise HTTPException(
            413, detail=f"Maksimal 100.000 baris per request, dapat {len(df):,}."
        )

    p = get_predictor()
    try:
        result = p.predict_batch(df)
    except ValueError as e:
        raise HTTPException(422, detail=str(e))

    rows = [
        BatchRow(
            Recency=float(r["Recency"]),
            Frequency=float(r["Frequency"]),
            Monetary=float(r["Monetary"]),
            Cluster=int(r["Cluster"]),
            Segment=str(r["Segment"]),
            Distance=float(r["Distance"]),
        )
        for r in result[["Recency", "Frequency", "Monetary", "Cluster", "Segment", "Distance"]]
        .to_dict("records")
    ]
    return BatchResponse(n_rows=len(rows), rows=rows)
