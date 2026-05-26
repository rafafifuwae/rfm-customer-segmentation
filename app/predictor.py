"""Wrapper untuk model K-Means RFM yang men-encapsulate seluruh transform pipeline.

Transform: raw RFM -> winsorize -> log1p (F, M) -> StandardScaler -> KMeans.predict
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "kmeans_rfm.pkl"
ARTIFACTS_PATH = ROOT / "models" / "serving_artifacts.json"


@dataclass
class Prediction:
    cluster: int
    segment: str
    distance_to_centroid: float
    strategy: dict


class RFMPredictor:
    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        artifacts_path: Path = ARTIFACTS_PATH,
    ):
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model tidak ditemukan: {model_path}. Jalankan notebook 04 dulu."
            )
        if not artifacts_path.exists():
            raise FileNotFoundError(
                f"Artifacts tidak ditemukan: {artifacts_path}. "
                "Jalankan `python -m app.build_artifacts` dulu."
            )

        bundle = joblib.load(model_path)
        self.scaler = bundle["scaler"]
        self.kmeans = bundle["kmeans"]
        self.feature_cols = bundle["feature_cols"]

        artifacts = json.loads(artifacts_path.read_text())
        self.bounds = artifacts["winsorize_bounds"]
        self.use_log = artifacts["use_log_transform"]
        # JSON object keys are strings -> convert ke int
        self.segment_map = {int(k): v for k, v in artifacts["segment_map"].items()}
        self.cluster_profile = {
            int(k): v for k, v in artifacts["cluster_profile"].items()
        }
        self.segment_strategy = artifacts["segment_strategy"]

    def _transform(self, df: pd.DataFrame) -> np.ndarray:
        """Raw RFM -> matriks fitur scaled, siap untuk kmeans.predict."""
        out = pd.DataFrame(index=df.index)

        recency_b = self.bounds["Recency"]
        out["Recency_w"] = df["Recency"].clip(
            lower=recency_b["lower"], upper=recency_b["upper"]
        )

        freq_b = self.bounds["Frequency"]
        freq_w = df["Frequency"].clip(lower=freq_b["lower"], upper=freq_b["upper"])
        out["Frequency_log"] = np.log1p(freq_w) if self.use_log.get("frequency", True) else freq_w

        mon_b = self.bounds["Monetary"]
        mon_w = df["Monetary"].clip(lower=mon_b["lower"], upper=mon_b["upper"])
        out["Monetary_log"] = np.log1p(mon_w) if self.use_log.get("monetary", True) else mon_w

        X = out[self.feature_cols].values
        return self.scaler.transform(X)

    def predict_one(self, recency: float, frequency: float, monetary: float) -> Prediction:
        df = pd.DataFrame(
            [{"Recency": recency, "Frequency": frequency, "Monetary": monetary}]
        )
        X_scaled = self._transform(df)
        cluster_id = int(self.kmeans.predict(X_scaled)[0])
        centroid = self.kmeans.cluster_centers_[cluster_id]
        distance = float(np.linalg.norm(X_scaled[0] - centroid))
        segment = self.segment_map.get(cluster_id, "Unknown")
        strategy = self.segment_strategy.get(segment, {})
        return Prediction(
            cluster=cluster_id,
            segment=segment,
            distance_to_centroid=distance,
            strategy=strategy,
        )

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        required = {"Recency", "Frequency", "Monetary"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Kolom wajib hilang: {sorted(missing)}. "
                f"Butuh: Recency, Frequency, Monetary."
            )

        X_scaled = self._transform(df)
        labels = self.kmeans.predict(X_scaled)
        centroids = self.kmeans.cluster_centers_[labels]
        distances = np.linalg.norm(X_scaled - centroids, axis=1)

        result = df.copy()
        result["Cluster"] = labels.astype(int)
        result["Segment"] = pd.Series(labels).map(self.segment_map).values
        result["Distance"] = distances.round(4)
        return result

    def list_clusters(self) -> list[dict]:
        out = []
        for cluster_id, prof in sorted(self.cluster_profile.items()):
            segment = self.segment_map.get(cluster_id, "Unknown")
            out.append(
                {
                    "cluster": cluster_id,
                    "segment": segment,
                    "n_customers": int(prof["n_customers"]),
                    "pct_customers": float(prof["pct_customers"]),
                    "Recency_mean": float(prof["Recency_mean"]),
                    "Frequency_mean": float(prof["Frequency_mean"]),
                    "Monetary_mean": float(prof["Monetary_mean"]),
                    "Monetary_total": float(prof["Monetary_total"]),
                    "strategy": self.segment_strategy.get(segment, {}),
                }
            )
        return out


# Singleton untuk reuse di FastAPI / Streamlit
_PREDICTOR: RFMPredictor | None = None


def get_predictor() -> RFMPredictor:
    global _PREDICTOR
    if _PREDICTOR is None:
        _PREDICTOR = RFMPredictor()
    return _PREDICTOR
