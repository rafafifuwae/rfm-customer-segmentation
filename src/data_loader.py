"""
src/data_loader.py
==================
Modul loader dataset Olist untuk proyek Segmentasi Pelanggan RFM + K-Means.

Penggunaan:
    from src.data_loader import load_olist
    data = load_olist()
    orders = data['orders']
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict
import pandas as pd

# default ke folder data/raw relatif terhadap root proyek
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"

PARSE_DATES: dict[str, list[str]] = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
}

FILE_MAP: dict[str, str] = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_trans": "product_category_name_translation.csv",
}


def load_olist(raw_dir: Path | str = DEFAULT_RAW_DIR) -> Dict[str, pd.DataFrame]:
    """Memuat seluruh tabel Olist sebagai dict of DataFrame.

    Parameters
    ----------
    raw_dir : Path | str
        Direktori berisi file CSV mentah.

    Returns
    -------
    dict[str, pd.DataFrame]
        Kunci: nama tabel logis, value: DataFrame.
    """
    raw_dir = Path(raw_dir)
    out: Dict[str, pd.DataFrame] = {}
    for key, fname in FILE_MAP.items():
        kwargs = {}
        if key in PARSE_DATES:
            kwargs["parse_dates"] = PARSE_DATES[key]
        out[key] = pd.read_csv(raw_dir / fname, **kwargs)
    return out


def build_rfm(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    payments: pd.DataFrame,
    snapshot_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Membangun tabel RFM (Recency, Frequency, Monetary) per `customer_unique_id`."""
    od = orders[orders["order_status"] == "delivered"].copy()
    od = od.dropna(subset=["order_purchase_timestamp"])
    pay = (
        payments.groupby("order_id", as_index=False)["payment_value"].sum()
    )
    df = (
        od.merge(customers[["customer_id", "customer_unique_id"]], on="customer_id", how="left")
        .merge(pay, on="order_id", how="left")
        .dropna(subset=["payment_value", "customer_unique_id"])
    )
    if snapshot_date is None:
        snapshot_date = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    rfm = (
        df.groupby("customer_unique_id")
        .agg(
            Recency=("order_purchase_timestamp", lambda x: (snapshot_date - x.max()).days),
            Frequency=("order_id", "nunique"),
            Monetary=("payment_value", "sum"),
        )
        .reset_index()
    )
    return rfm
