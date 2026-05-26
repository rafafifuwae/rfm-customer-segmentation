"""Generate serving artifacts dari hasil training.

Jalankan satu kali setelah training selesai:
    python -m app.build_artifacts

Menghasilkan models/serving_artifacts.json yang berisi:
  - winsorize_bounds : batas clip untuk Recency, Frequency, Monetary
  - segment_map      : cluster_id -> nama segmen
  - cluster_profile  : statistik tiap cluster (untuk ditampilkan di UI)
  - segment_strategy : rekomendasi marketing per segmen
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"

SEGMENT_STRATEGY = {
    "Champions": {
        "deskripsi": "Pelanggan paling bernilai: transaksi terbaru, sering, dan bernilai tinggi.",
        "strategi": [
            "Program loyalitas premium / VIP",
            "Akses awal ke produk baru",
            "Personalized thank-you & referral incentive",
        ],
    },
    "Loyal Customers": {
        "deskripsi": "Sering berbelanja, masih aktif, nilai transaksi sedang.",
        "strategi": [
            "Upsell ke produk premium",
            "Bundle / cross-sell kategori terkait",
            "Program poin reward",
        ],
    },
    "Potential Loyalists": {
        "deskripsi": "Transaksi terbaru tapi frekuensi/nilai belum tinggi.",
        "strategi": [
            "Email onboarding & rekomendasi produk",
            "Diskon untuk pembelian kedua",
            "Edukasi kategori produk",
        ],
    },
    "At Risk": {
        "deskripsi": "Dulu bernilai tinggi tapi sudah lama tidak transaksi.",
        "strategi": [
            "Win-back campaign dengan diskon agresif",
            "Survei untuk tahu alasan churn",
            "Personalized re-engagement email",
        ],
    },
    "Hibernating / Lost": {
        "deskripsi": "Sudah lama tidak aktif dan nilainya rendah.",
        "strategi": [
            "Kampanye reaktivasi minimal-cost (email/push)",
            "Pertimbangkan deprioritisasi akuisisi ulang",
            "Gunakan sebagai look-alike negative signal",
        ],
    },
}


def main() -> None:
    rfm_table = pd.read_csv(PROCESSED_DIR / "rfm_table.csv")
    rfm_seg = pd.read_csv(PROCESSED_DIR / "rfm_segmented.csv")
    params = yaml.safe_load((ROOT / "params.yaml").read_text())

    w_upper = params["preprocessing"]["winsorize_upper"]
    w_lower = params["preprocessing"]["winsorize_lower"]

    bounds = {
        col: {
            "lower": float(rfm_table[col].quantile(w_lower)),
            "upper": float(rfm_table[col].quantile(w_upper)),
        }
        for col in ["Recency", "Frequency", "Monetary"]
    }

    # segment_map: cluster -> nama segmen (ambil yang paling sering muncul per cluster)
    segment_map = (
        rfm_seg.groupby("Cluster")["Segment"]
        .agg(lambda s: s.value_counts().idxmax())
        .to_dict()
    )
    segment_map = {int(k): v for k, v in segment_map.items()}

    # cluster_profile: untuk ditampilkan di UI
    profile = (
        rfm_seg.groupby("Cluster")
        .agg(
            n_customers=("customer_unique_id", "count"),
            Recency_mean=("Recency", "mean"),
            Frequency_mean=("Frequency", "mean"),
            Monetary_mean=("Monetary", "mean"),
            Monetary_total=("Monetary", "sum"),
        )
        .round(2)
    )
    profile["pct_customers"] = (
        profile["n_customers"] / profile["n_customers"].sum() * 100
    ).round(2)
    profile["Segment"] = profile.index.map(segment_map)
    cluster_profile = {
        int(idx): {**row.to_dict(), "Cluster": int(idx)}
        for idx, row in profile.iterrows()
    }

    artifacts = {
        "winsorize_bounds": bounds,
        "use_log_transform": params["preprocessing"]["use_log_transform"],
        "segment_map": segment_map,
        "cluster_profile": cluster_profile,
        "segment_strategy": SEGMENT_STRATEGY,
        "feature_cols": params["rfm"]["features"],
        "n_training_samples": int(len(rfm_seg)),
    }

    out_path = MODELS_DIR / "serving_artifacts.json"
    out_path.write_text(json.dumps(artifacts, indent=2))
    print(f"Tersimpan -> {out_path}")
    print(f"  Bounds        : {bounds}")
    print(f"  Segment map   : {segment_map}")
    print(f"  Cluster sizes : {[(c, p['n_customers']) for c, p in cluster_profile.items()]}")


if __name__ == "__main__":
    main()
