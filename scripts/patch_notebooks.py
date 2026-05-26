"""One-off patch script: applies fixes to notebooks 03 & 04.

Run once to apply the fixes identified in the project review. Idempotent.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"


def cell(source: str) -> dict:
    lines = source.splitlines(keepends=True)
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines,
    }


SETUP_03 = '''import warnings
from pathlib import Path
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Scope warnings: only suppress noisy known-safe ones, keep the rest.
warnings.filterwarnings("default")
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="seaborn")

sns.set_theme(style="whitegrid")

def _find_project_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "params.yaml").is_file():
            return p
    raise FileNotFoundError("params.yaml not found in any parent directory")

PROJECT_ROOT  = _find_project_root(Path.cwd())
RAW_DIR       = PROJECT_ROOT / "data" / "raw"
INTERIM_DIR   = PROJECT_ROOT / "data" / "interim"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIG_DIR       = PROJECT_ROOT / "reports" / "figures"
for d in [INTERIM_DIR, PROCESSED_DIR, FIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

with open(PROJECT_ROOT / "params.yaml") as f:
    PARAMS = yaml.safe_load(f)

RANDOM_STATE  = PARAMS["random_state"]
PRE_PARAMS    = PARAMS["preprocessing"]
RFM_PARAMS    = PARAMS["rfm"]

print("PROJECT_ROOT :", PROJECT_ROOT)
print("Params       :", list(PARAMS.keys()))

# Load tabel mentah yang dibutuhkan tahap preprocessing.
import sys
sys.path.insert(0, str(PROJECT_ROOT))
from src.data_loader import load_olist

_data = load_olist(RAW_DIR)
orders    = _data["orders"]
customers = _data["customers"]
payments  = _data["order_payments"]
print("Loaded :", {k: v.shape for k, v in [("orders", orders), ("customers", customers), ("payments", payments)]})
'''

FILTER_03 = '''before = len(orders)
status_filter = PRE_PARAMS["status_filter"]
orders_d = orders[orders["order_status"] == status_filter].copy()
# Hanya drop NA pada purchase_timestamp (konsisten dengan src/data_loader.build_rfm).
orders_d = orders_d.dropna(subset=["order_purchase_timestamp"])
print(f"Order awal             : {before:,}")
print(f"Order status={status_filter!r}: {len(orders_d):,}  (dibuang {before-len(orders_d):,})")

orders_d = orders_d.drop_duplicates(subset="order_id")
print("Setelah drop duplicates :", len(orders_d))
'''

WINSORIZE_03 = '''def winsorize(s, upper=0.99, lower=0.0):
    lo = s.quantile(lower)
    hi = s.quantile(upper)
    return s.clip(lower=lo, upper=hi)

w_upper = PRE_PARAMS["winsorize_upper"]
w_lower = PRE_PARAMS["winsorize_lower"]

rfm["Monetary_w"]  = winsorize(rfm["Monetary"],  upper=w_upper, lower=w_lower)
rfm["Recency_w"]   = winsorize(rfm["Recency"],   upper=w_upper, lower=w_lower)
rfm["Frequency_w"] = winsorize(rfm["Frequency"], upper=w_upper, lower=w_lower)

# Log transform berdasarkan params.
if PRE_PARAMS["use_log_transform"].get("monetary", True):
    rfm["Monetary_log"] = np.log1p(rfm["Monetary_w"])
else:
    rfm["Monetary_log"] = rfm["Monetary_w"]

if PRE_PARAMS["use_log_transform"].get("frequency", True):
    rfm["Frequency_log"] = np.log1p(rfm["Frequency_w"])
else:
    rfm["Frequency_log"] = rfm["Frequency_w"]

rfm[["Recency", "Recency_w", "Frequency", "Frequency_w", "Frequency_log",
     "Monetary", "Monetary_w", "Monetary_log"]].describe().round(2)
'''

QCUT_03 = '''q = RFM_PARAMS["scoring_quintiles"]

# rank(method="first") + duplicates="drop" agar aman terhadap nilai duplikat.
rfm["R_score"] = pd.qcut(rfm["Recency_w"].rank(method="first"), q,
                          labels=list(range(q, 0, -1))).astype(int)
rfm["F_score"] = pd.qcut(rfm["Frequency_w"].rank(method="first"), q,
                          labels=list(range(1, q + 1))).astype(int)
rfm["M_score"] = pd.qcut(rfm["Monetary_w"].rank(method="first"), q,
                          labels=list(range(1, q + 1))).astype(int)
rfm["RFM_score"] = rfm["R_score"] * 100 + rfm["F_score"] * 10 + rfm["M_score"]
rfm.head()
'''

SETUP_04 = '''import warnings, json
from pathlib import Path
import yaml
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.decomposition import PCA

warnings.filterwarnings("default")
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="seaborn")

sns.set_theme(style="whitegrid", palette="Set2")
plt.rcParams["figure.figsize"] = (10, 5)

def _find_project_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "params.yaml").is_file():
            return p
    raise FileNotFoundError("params.yaml not found in any parent directory")

PROJECT_ROOT  = _find_project_root(Path.cwd())
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR    = PROJECT_ROOT / "models"
FIG_DIR       = PROJECT_ROOT / "reports" / "figures"
for d in [MODELS_DIR, FIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

with open(PROJECT_ROOT / "params.yaml") as f:
    PARAMS = yaml.safe_load(f)

RANDOM_STATE = PARAMS["random_state"]
KM_PARAMS    = PARAMS["kmeans"]
RFM_FEATURES = PARAMS["rfm"]["features"]

print("PROJECT_ROOT :", PROJECT_ROOT)
print("Features     :", RFM_FEATURES)
print("k_range      :", KM_PARAMS["k_range"])
print("k_optimal    :", KM_PARAMS["k_optimal"])
'''

SCALE_04 = '''feature_cols = RFM_FEATURES
X = rfm[feature_cols].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("X_scaled shape :", X_scaled.shape)
print("Mean (~0)      :", X_scaled.mean(axis=0).round(3))
print("Std (~1)       :", X_scaled.std(axis=0).round(3))
'''

KSCAN_04 = '''ks = list(KM_PARAMS["k_range"])
n_init_scan = max(10, KM_PARAMS["n_init"] // 2)  # lebih cepat untuk scan
inertias, sil_scores, db_scores = [], [], []
for k in ks:
    km = KMeans(n_clusters=k, n_init=n_init_scan, random_state=RANDOM_STATE)
    labels = km.fit_predict(X_scaled)
    inertias.append(km.inertia_)
    sil_scores.append(silhouette_score(X_scaled, labels, sample_size=10000,
                                       random_state=RANDOM_STATE))
    db_scores.append(davies_bouldin_score(X_scaled, labels))
    print(f"k={k:>2d} | inertia={km.inertia_:>10.0f} | silhouette={sil_scores[-1]:.4f} | DB={db_scores[-1]:.4f}")
'''

KOPT_04 = '''K_OPT = KM_PARAMS["k_optimal"]
print("k optimal yang dipakai :", K_OPT)
'''

FIT_04 = '''kmeans = KMeans(n_clusters=K_OPT, n_init=KM_PARAMS["n_init"],
                max_iter=KM_PARAMS["max_iter"], random_state=RANDOM_STATE)
rfm["Cluster"] = kmeans.fit_predict(X_scaled)

# Simpan model + scaler via joblib (lebih ringan & idiomatic untuk sklearn).
joblib.dump(
    {"scaler": scaler, "kmeans": kmeans, "feature_cols": feature_cols},
    MODELS_DIR / "kmeans_rfm.pkl",
)

metrics = {
    "k"             : int(K_OPT),
    "inertia"       : float(kmeans.inertia_),
    "silhouette"    : float(silhouette_score(X_scaled, rfm["Cluster"],
                                              sample_size=10000, random_state=RANDOM_STATE)),
    "davies_bouldin": float(davies_bouldin_score(X_scaled, rfm["Cluster"])),
    "n_samples"     : int(len(rfm)),
    "features"      : feature_cols,
}
with open(MODELS_DIR / "kmeans_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
metrics
'''

LABEL_04 = '''# Label segment data-driven berdasarkan posisi relatif tiap cluster.
# Tidak memakai threshold absolut yang membuat 'At Risk' tidak pernah tercapai.
_med_recency  = profile["Recency_mean"].median()
_med_monetary = profile["Monetary_mean"].median()
_med_freq     = profile["Frequency_mean"].median()

def label_segment(row):
    recent = row["Recency_mean"] <= _med_recency
    high_value = row["Monetary_mean"] >= _med_monetary
    high_freq = row["Frequency_mean"] >= _med_freq
    if recent and high_value and high_freq:
        return "Champions"
    if recent and high_freq:
        return "Loyal Customers"
    if recent:
        return "Potential Loyalists"
    if high_value:
        return "At Risk"          # lama tidak transaksi tapi nilainya besar
    return "Hibernating / Lost"

profile["Segment"] = profile.apply(label_segment, axis=1)
segment_map = profile["Segment"].to_dict()
rfm["Segment"] = rfm["Cluster"].map(segment_map)
profile
'''


def patch_notebook(path: Path, replacements: dict[int, str]) -> None:
    nb = json.loads(path.read_text())
    for idx, new_source in replacements.items():
        if nb["cells"][idx]["cell_type"] != "code":
            raise RuntimeError(f"{path.name} cell {idx} is not a code cell")
        nb["cells"][idx]["source"] = new_source.splitlines(keepends=True)
        nb["cells"][idx]["outputs"] = []
        nb["cells"][idx]["execution_count"] = None
    path.write_text(json.dumps(nb, indent=1))
    print(f"patched: {path.name}")


def main() -> None:
    patch_notebook(NB_DIR / "03_data_preprocessing.ipynb", {
        2:  SETUP_03,
        6:  FILTER_03,
        20: WINSORIZE_03,
        24: QCUT_03,
    })
    patch_notebook(NB_DIR / "04_rfm_kmeans_modeling.ipynb", {
        2:  SETUP_04,
        6:  SCALE_04,
        8:  KSCAN_04,
        11: KOPT_04,
        13: FIT_04,
        23: LABEL_04,
    })


if __name__ == "__main__":
    main()
