---
title: RFM Customer Segmentation
emoji: 🎯
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Segmentasi pelanggan e-commerce dengan RFM + K-Means
---

# Segmentasi Pelanggan untuk Mengatasi Ketidakefektifan Strategi Pemasaran Menggunakan Metode RFM dan Algoritma K-Means

Proyek riset Data Mining yang melakukan segmentasi pelanggan pada dataset **Brazilian E-Commerce Olist** (2016 – 2018) menggunakan metode **RFM (Recency, Frequency, Monetary)** dan algoritma **K-Means Clustering**.

## Tujuan
1. Mengelompokkan pelanggan berdasarkan perilaku transaksi (RFM).
2. Mengidentifikasi karakteristik tiap segmen pelanggan.
3. Memberikan rekomendasi strategi pemasaran yang lebih efektif untuk setiap segmen.

## Struktur Proyek
```
customer_segmentation_rfm_kmeans/
├── data/
│   ├── raw/            # Dataset mentah (di-track DVC)
│   ├── interim/        # Hasil cleaning & merging
│   └── processed/      # Dataset RFM siap modeling
├── notebooks/
│   ├── 01_data_collection.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_data_preprocessing.ipynb
│   └── 04_rfm_kmeans_modeling.ipynb
├── src/                # Modul Python (loader, util)
├── reports/figures/    # Visualisasi hasil
├── models/             # Model K-Means tersimpan
├── dvc.yaml            # Definisi pipeline DVC
├── params.yaml         # Parameter eksperimen
├── requirements.txt
└── README.md
```

## Sumber Data
- **Brazilian E-Commerce Public Dataset by Olist** (Kaggle, 2018).
- 9 file CSV, ~100k transaksi, 96k pelanggan unik, periode 2016 – 2018.

## Cara Menjalankan
```bash
# 1. Buat virtual env (opsional)
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Opsional) tarik dataset via DVC
#    Catatan: butuh remote DVC yang sudah dikonfigurasi.
#    Jika belum, letakkan CSV mentah Olist langsung di data/raw/.
dvc pull

# 4a. Reproduksi pipeline penuh via DVC (rekomendasi)
dvc repro

# 4b. Atau jalankan notebook manual secara berurutan
jupyter notebook
```

## Pipeline Singkat
1. **Data Collection** – Loading 9 tabel Olist, dokumentasi schema, sampling.
2. **EDA** – Univariate, bivariate, multivariate, korelasi, outlier, time-series.
3. **Preprocessing** – Cleaning, filter `delivered`, merging, feature engineering RFM.
4. **RFM + K-Means** – Skoring RFM, scaling, elbow & silhouette, clustering, interpretasi.

## Dataset Tracking (DVC)
Dataset di-track menggunakan DVC. Lihat `docs_dvc.md` untuk detail penggunaan.
