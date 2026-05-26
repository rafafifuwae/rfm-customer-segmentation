"""
src/track_dataset.py
====================
Skrip *backup tracking* dataset (digunakan **bersama** DVC).

Mencatat metadata setiap file CSV di `data/raw/`:
- nama file
- ukuran (bytes)
- jumlah baris/kolom
- SHA-256 hash
- waktu modifikasi

Output: `reports/dataset_manifest.json`

Skrip ini berguna jika DVC belum diinisialisasi atau sebagai *audit trail* tambahan.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            buf = f.read(chunk)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


def manifest_for(path: Path) -> dict:
    n_cols = pd.read_csv(path, nrows=0).shape[1]
    with open(path, "rb") as fh:
        n_rows = sum(1 for _ in fh) - 1
    stat = path.stat()
    return {
        "file": path.name,
        "size_bytes": stat.st_size,
        "size_MB": round(stat.st_size / 1024**2, 2),
        "rows": n_rows,
        "cols": n_cols,
        "sha256": sha256(path),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def main() -> None:
    files = sorted(RAW_DIR.glob("*.csv"))
    if not files:
        raise SystemExit(f"Tidak ada CSV ditemukan di {RAW_DIR}")
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "raw_dir": str(RAW_DIR),
        "n_files": len(files),
        "files": [manifest_for(p) for p in files],
    }
    out_path = REPORTS_DIR / "dataset_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2))
    print(f"Manifest tersimpan -> {out_path}")
    print(f"  - {len(files)} file")
    print(f"  - total {sum(m['size_MB'] for m in manifest['files']):.2f} MB")


if __name__ == "__main__":
    main()
