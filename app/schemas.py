"""Pydantic schema untuk request/response FastAPI."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RFMInput(BaseModel):
    Recency: float = Field(
        ...,
        ge=0,
        description="Jumlah hari sejak transaksi terakhir pelanggan.",
        examples=[30],
    )
    Frequency: float = Field(
        ...,
        ge=1,
        description="Jumlah order unik yang pernah dilakukan pelanggan.",
        examples=[2],
    )
    Monetary: float = Field(
        ...,
        ge=0,
        description="Total nilai transaksi pelanggan (BRL).",
        examples=[350.5],
    )


class PredictionOut(BaseModel):
    cluster: int
    segment: str
    distance_to_centroid: float
    strategy: dict[str, Any]
    input: RFMInput


class ClusterInfo(BaseModel):
    cluster: int
    segment: str
    n_customers: int
    pct_customers: float
    Recency_mean: float
    Frequency_mean: float
    Monetary_mean: float
    Monetary_total: float
    strategy: dict[str, Any]


class BatchRow(BaseModel):
    Recency: float
    Frequency: float
    Monetary: float
    Cluster: int
    Segment: str
    Distance: float


class BatchResponse(BaseModel):
    n_rows: int
    rows: list[BatchRow]


class HealthOut(BaseModel):
    status: str
    n_training_samples: int
    feature_cols: list[str]
    n_clusters: int
