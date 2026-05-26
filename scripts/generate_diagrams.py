"""Generate 3 diagram untuk laporan:
1. CRISP-DM research flow (Section 3)
2. Deployment architecture (Section 5.1)
3. Multi-layer deployment strategy (Section 5.9)

Output: reports/figures/diagrams/*.png (300 DPI)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "figures" / "diagrams"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Palet warna (konsisten dengan laporan)
NAVY      = "#1F3A5F"
BLUE      = "#3E6BA8"
TEAL      = "#4D9DE0"
GREEN     = "#2E8B57"
ORANGE    = "#E67E22"
RED       = "#C0392B"
GRAY      = "#7F8C8D"
LIGHT_BG  = "#F8F9FA"
WHITE     = "#FFFFFF"


def make_box(ax, x, y, w, h, text, color, text_color=WHITE, fontsize=10,
             fontweight="bold", subtitle=None, subtitle_size=8):
    """Gambar rounded box dengan text."""
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        facecolor=color, edgecolor=NAVY, linewidth=1.2,
    )
    ax.add_patch(box)
    if subtitle:
        ax.text(x, y + 0.12, text, ha="center", va="center",
                color=text_color, fontsize=fontsize, fontweight=fontweight)
        ax.text(x, y - 0.18, subtitle, ha="center", va="center",
                color=text_color, fontsize=subtitle_size, style="italic")
    else:
        ax.text(x, y, text, ha="center", va="center",
                color=text_color, fontsize=fontsize, fontweight=fontweight)


def make_arrow(ax, x1, y1, x2, y2, color=NAVY, lw=2, style="->"):
    arr = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style, mutation_scale=18,
        color=color, lw=lw,
    )
    ax.add_patch(arr)


def make_side_note(ax, x, y, text, color=GRAY, fontsize=8):
    ax.text(x, y, text, ha="left", va="center",
            color=color, fontsize=fontsize, style="italic")


# ============================================================
# DIAGRAM 1 — CRISP-DM Research Flow
# ============================================================
def diagram_research_flow():
    fig, ax = plt.subplots(figsize=(11, 13), dpi=200)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 18)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    # Title
    ax.text(7, 17.2, "Alur Penelitian Data Mining",
            ha="center", fontsize=16, fontweight="bold", color=NAVY)
    ax.text(7, 16.6, "(Adaptasi CRISP-DM untuk Segmentasi Pelanggan)",
            ha="center", fontsize=11, style="italic", color=GRAY)

    # 6 Fase (vertikal)
    phases = [
        {"y": 15.0, "title": "1. BUSINESS UNDERSTANDING",
         "sub": "Identifikasi masalah pemasaran one-size-fits-all",
         "color": NAVY, "note": ""},
        {"y": 13.0, "title": "2. DATA UNDERSTANDING",
         "sub": "Load 9 tabel Olist, EDA, validasi schema",
         "color": BLUE, "note": "notebooks/01_data_collection.ipynb\nnotebooks/02_eda.ipynb"},
        {"y": 11.0, "title": "3. DATA PREPARATION",
         "sub": "Cleaning · Merging · RFM Feature Eng. · Winsorize · Log",
         "color": TEAL, "note": "notebooks/03_data_preprocessing.ipynb\n→ rfm_table.csv (93.357 pelanggan)"},
        {"y": 9.0, "title": "4. MODELING",
         "sub": "StandardScaler + K-Means (k=4, n_init=20)",
         "color": GREEN, "note": "notebooks/04_rfm_kmeans_modeling.ipynb\n→ kmeans_rfm.pkl"},
        {"y": 7.0, "title": "5. EVALUATION",
         "sub": "Silhouette: 0.372 · Davies-Bouldin: 0.763",
         "color": ORANGE, "note": "models/kmeans_metrics.json\n→ rfm_segmented.csv"},
        {"y": 5.0, "title": "6. DEPLOYMENT",
         "sub": "FastAPI + Streamlit + Docker (HF Spaces)",
         "color": RED, "note": "app/api.py · app/streamlit_app.py\nDockerfile · scripts/deploy_hf.sh"},
    ]

    for ph in phases:
        make_box(ax, 4, ph["y"], 6.5, 1.3, ph["title"], ph["color"],
                 subtitle=ph["sub"], fontsize=11, subtitle_size=9)
        if ph["note"]:
            for j, line in enumerate(ph["note"].split("\n")):
                ax.text(8.0, ph["y"] + 0.25 - j * 0.3, "→ " + line,
                        ha="left", va="center", color=GRAY,
                        fontsize=8.5, family="monospace")

    # Arrows
    for i in range(len(phases) - 1):
        make_arrow(ax, 4, phases[i]["y"] - 0.65, 4, phases[i + 1]["y"] + 0.65)

    # Footer box: deliverables
    ax.text(7, 3.5, "OUTPUT AKHIR",
            ha="center", fontsize=11, fontweight="bold", color=NAVY)
    deliverables = [
        "4 Segmen Pelanggan:  Champions  ·  Loyal Customers  ·  At Risk  ·  Hibernating/Lost",
        "REST API + Web UI yang siap diintegrasikan dengan sistem marketing",
        "Rekomendasi strategi pemasaran spesifik per segmen",
    ]
    for i, item in enumerate(deliverables):
        ax.text(7, 2.9 - i * 0.5, "✓ " + item,
                ha="center", fontsize=10, color=NAVY)

    plt.tight_layout()
    out = OUT_DIR / "01_research_flow.png"
    plt.savefig(out, dpi=200, bbox_inches="tight", facecolor=WHITE)
    plt.close()
    return out


# ============================================================
# DIAGRAM 2 — Deployment Architecture
# ============================================================
def diagram_deployment_architecture():
    fig, ax = plt.subplots(figsize=(11, 13), dpi=200)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 18)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    ax.text(7, 17.2, "Arsitektur Deployment",
            ha="center", fontsize=16, fontweight="bold", color=NAVY)
    ax.text(7, 16.6, "FastAPI (Backend) + Streamlit (Frontend) + RFMPredictor (Pipeline)",
            ha="center", fontsize=11, style="italic", color=GRAY)

    # User
    make_box(ax, 7, 15.0, 4, 1.0, "User / Visitor (Browser)", GRAY,
             fontsize=11)
    make_arrow(ax, 7, 14.5, 7, 13.8)
    ax.text(7.3, 14.15, "HTTPS", ha="left", color=GRAY, fontsize=8, style="italic")

    # Public layer
    make_box(ax, 7, 13.2, 8, 1.1, "PUBLIC LAYER", NAVY,
             subtitle="Cloudflare Tunnel  |  Hugging Face Spaces",
             fontsize=11, subtitle_size=9)
    make_arrow(ax, 7, 12.65, 7, 11.85)

    # Streamlit UI
    make_box(ax, 7, 11.2, 8, 1.4, "Streamlit Web UI  (port 8501)", BLUE,
             subtitle="• Single Prediction   • Batch CSV Upload   • Cluster Overview",
             fontsize=11, subtitle_size=9)
    make_arrow(ax, 7, 10.50, 7, 9.75)
    ax.text(7.3, 10.10, "HTTP (internal)", ha="left",
            color=GRAY, fontsize=8, style="italic")

    # FastAPI
    make_box(ax, 7, 9.1, 8, 1.4, "FastAPI REST API  (port 8000)", TEAL,
             subtitle="POST /predict   POST /predict/batch   GET /clusters   GET /health",
             fontsize=11, subtitle_size=8.5)
    make_arrow(ax, 7, 8.4, 7, 7.7)

    # Predictor
    make_box(ax, 7, 7.0, 8, 1.3, "RFMPredictor  (app/predictor.py)", GREEN,
             subtitle="Transform Pipeline + Inference",
             fontsize=11, subtitle_size=9)
    make_arrow(ax, 7, 6.35, 7, 5.5)

    # Pipeline transform (horizontal)
    pipeline_y = 4.9
    steps = [
        ("Raw RFM\nInput", "#5DADE2"),
        ("Winsorize", "#48C9B0"),
        ("log1p\n(F, M)", "#52BE80"),
        ("Standard\nScaler", "#F4D03F"),
        ("KMeans\n.predict()", "#EB984E"),
        ("Segment +\nStrategi", "#E74C3C"),
    ]
    step_w = 1.7
    start_x = 7 - (len(steps) * step_w + (len(steps) - 1) * 0.3) / 2 + step_w / 2
    for i, (txt, col) in enumerate(steps):
        x = start_x + i * (step_w + 0.3)
        make_box(ax, x, pipeline_y, step_w, 1.2, txt, col,
                 text_color=NAVY, fontsize=8.5)
        if i < len(steps) - 1:
            make_arrow(ax, x + step_w / 2, pipeline_y,
                       x + step_w + 0.3 - step_w / 2, pipeline_y,
                       color=GRAY, lw=1.5)

    # Artifacts (bottom)
    ax.text(7, 3.4, "Model Artifacts",
            ha="center", fontsize=11, fontweight="bold", color=NAVY)
    art_y = 2.7
    artifacts = [
        ("models/\nkmeans_rfm.pkl\n(374 KB)", 4),
        ("models/\nserving_artifacts.json\n(winsorize bounds,\nsegment map)", 7),
        ("params.yaml\n(hyperparameters)", 10),
    ]
    for txt, x in artifacts:
        make_box(ax, x, art_y, 2.3, 1.4, txt, LIGHT_BG,
                 text_color=NAVY, fontsize=8, fontweight="normal")

    plt.tight_layout()
    out = OUT_DIR / "02_deployment_architecture.png"
    plt.savefig(out, dpi=200, bbox_inches="tight", facecolor=WHITE)
    plt.close()
    return out


# ============================================================
# DIAGRAM 3 — Multi-Layer Deployment Strategy
# ============================================================
def diagram_multilayer():
    fig, ax = plt.subplots(figsize=(11, 11), dpi=200)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 15)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    ax.text(7, 14.3, "Strategi Deployment Multi-Layer",
            ha="center", fontsize=16, fontweight="bold", color=NAVY)
    ax.text(7, 13.7, "Dari Development hingga Hosting Permanen — Tanpa Perubahan Kode Aplikasi",
            ha="center", fontsize=10, style="italic", color=GRAY)

    layers = [
        {
            "y": 11.0, "title": "Layer 1 — LOKAL DEVELOPMENT",
            "color": NAVY,
            "items": [
                "./scripts/run_app.sh",
                "FastAPI : http://localhost:8000",
                "Streamlit: http://localhost:8501",
                "Untuk pengembangan & testing internal",
            ],
        },
        {
            "y": 7.5, "title": "Layer 2 — DEMO PUBLIK (Cloudflare Tunnel)",
            "color": GREEN,
            "items": [
                "./scripts/run_demo.sh",
                "Layer 1 + tunnel publik via cloudflared",
                "URL: https://xxx.trycloudflare.com (temporary)",
                "Cocok untuk demo sidang • Gratis • Tanpa signup",
            ],
        },
        {
            "y": 3.9, "title": "Layer 3 — HOSTING PERMANEN (HF Spaces)",
            "color": ORANGE,
            "items": [
                "Dockerfile + ./scripts/deploy_hf.sh",
                "Container Docker (FastAPI + Streamlit)",
                "URL stabil 24/7 di huggingface.co/spaces",
                "Auto-rebuild saat kode di-push  •  Gratis",
            ],
        },
    ]

    for layer in layers:
        # Header bar
        make_box(ax, 7, layer["y"] + 1.0, 11, 0.7, layer["title"],
                 layer["color"], fontsize=12)
        # Box dengan items
        box = FancyBboxPatch(
            (1.5, layer["y"] - 0.9), 11, 1.7,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            facecolor=LIGHT_BG, edgecolor=layer["color"], linewidth=1.5,
        )
        ax.add_patch(box)
        for j, item in enumerate(layer["items"]):
            ax.text(2.2, layer["y"] + 0.45 - j * 0.4, "•  " + item,
                    ha="left", va="center", fontsize=10, color=NAVY,
                    family="monospace")

    # Arrows between layers
    make_arrow(ax, 7, 9.7, 7, 8.6, color=NAVY, lw=2.5)
    ax.text(7.4, 9.15, "saat butuh demo publik", ha="left",
            color=GRAY, fontsize=9, style="italic")

    make_arrow(ax, 7, 6.2, 7, 5.0, color=NAVY, lw=2.5)
    ax.text(7.4, 5.6, "saat butuh hosting permanen", ha="left",
            color=GRAY, fontsize=9, style="italic")

    # Footer
    ax.text(7, 1.5, "Semua layer pakai source code & model yang SAMA — hanya berbeda environment runtime.",
            ha="center", fontsize=10, color=NAVY, fontweight="bold")

    plt.tight_layout()
    out = OUT_DIR / "03_deployment_layers.png"
    plt.savefig(out, dpi=200, bbox_inches="tight", facecolor=WHITE)
    plt.close()
    return out


def main():
    outputs = []
    outputs.append(diagram_research_flow())
    outputs.append(diagram_deployment_architecture())
    outputs.append(diagram_multilayer())

    print("Diagram tersimpan:")
    for f in outputs:
        size_kb = f.stat().st_size / 1024
        print(f"  {f.relative_to(ROOT)}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
