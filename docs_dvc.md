# Dataset Tracking dengan DVC

Proyek ini menggunakan **DVC (Data Version Control)** untuk melacak versi dataset dan pipeline. DVC bekerja berdampingan dengan Git: file besar disimpan di **storage eksternal** (lokal/cloud) sementara *pointer*-nya (`*.dvc`) di-commit ke Git.

## 1. Instalasi

```bash
pip install dvc
# (opsional, untuk Google Drive remote)
pip install "dvc[gdrive]"
```

## 2. Inisialisasi (sudah dilakukan, dokumentasi referensi)

```bash
cd customer_segmentation_rfm_kmeans
git init                # jika belum
dvc init
git add .dvc .dvcignore
git commit -m "chore: init DVC"
```

## 3. Tracking Dataset Mentah

Setiap file CSV di `data/raw/` di-track:

```bash
dvc add data/raw/olist_orders_dataset.csv
dvc add data/raw/olist_customers_dataset.csv
dvc add data/raw/olist_order_payments_dataset.csv
dvc add data/raw/olist_order_items_dataset.csv
dvc add data/raw/olist_order_reviews_dataset.csv
dvc add data/raw/olist_products_dataset.csv
dvc add data/raw/olist_sellers_dataset.csv
dvc add data/raw/olist_geolocation_dataset.csv
dvc add data/raw/product_category_name_translation.csv

git add data/raw/*.dvc data/raw/.gitignore
git commit -m "data: track Olist raw dataset with DVC"
```

Atau menggunakan **wildcard satu perintah**:

```bash
dvc add data/raw
```

## 4. Setup Remote Storage

Pilih salah satu:

```bash
# A) Lokal (folder di komputer/USB lain)
dvc remote add -d localremote /path/to/dvc_storage

# B) Google Drive
dvc remote add -d gdrive gdrive://<folder-id>

# C) Amazon S3
dvc remote add -d s3remote s3://my-bucket/dvc-store

git add .dvc/config
git commit -m "chore: configure DVC remote"
```

Push ke remote:

```bash
dvc push
```

## 5. Pipeline DVC (`dvc.yaml`)

Pipeline didefinisikan di `dvc.yaml` dengan stages:

| Stage | Input | Output |
|---|---|---|
| `preprocess` | raw CSV + notebook 03 | `data/processed/rfm_table.csv` |
| `modeling`   | tabel RFM + notebook 04 | `models/kmeans_rfm.pkl`, `rfm_segmented.csv` |

Jalankan seluruh pipeline dengan:

```bash
dvc repro
```

DVC akan **otomatis men-skip stage** yang inputnya tidak berubah (caching).

## 6. Eksperimen & Metrics

Setiap perubahan parameter di `params.yaml` akan dianggap eksperimen baru:

```bash
# Ubah params.yaml (mis. kmeans.k_optimal: 5)
dvc repro
dvc metrics show
dvc params diff
```

Membandingkan dua eksperimen:

```bash
dvc exp run -S kmeans.k_optimal=5
dvc exp show          # tabel komparasi
dvc exp diff HEAD     # bandingkan dengan commit terakhir
```

## 7. Reproduce di Mesin Baru

```bash
git clone <repo-url>
cd customer_segmentation_rfm_kmeans
pip install -r requirements.txt
dvc pull              # tarik dataset dari remote
dvc repro             # jalankan pipeline
```

## 8. Audit Trail Tambahan (Manual Manifest)

Selain DVC, skrip `src/track_dataset.py` membuat **manifest JSON** berisi nama file, ukuran, hash SHA-256, dan jumlah baris/kolom \u2014 berguna sebagai audit trail manual:

```bash
python src/track_dataset.py
# -> reports/dataset_manifest.json
```

## 9. File yang Di-track

```
.dvc/                # konfigurasi DVC
.dvc/config          # remote settings
data/raw/*.dvc       # pointer file dataset
dvc.yaml             # definisi pipeline
dvc.lock             # snapshot run terakhir (auto-generated)
params.yaml          # parameter eksperimen
```

Semua file di atas **harus di-commit ke Git**, sedangkan dataset asli **tidak**.
