"""Streamlit UI untuk RFM Customer Segmentation.

Jalankan:
    streamlit run app/streamlit_app.py

Konfigurasi API endpoint via env var:
    API_URL=http://localhost:8000 streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import io
import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RFM Customer Segmentation",
    page_icon="🎯",
    layout="wide",
)

SEGMENT_COLORS = {
    "Champions": "#2ecc71",
    "Loyal Customers": "#3498db",
    "Potential Loyalists": "#9b59b6",
    "At Risk": "#f39c12",
    "Hibernating / Lost": "#e74c3c",
}


@st.cache_data(ttl=300)
def fetch_clusters():
    r = requests.get(f"{API_URL}/clusters", timeout=10)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300)
def fetch_health():
    r = requests.get(f"{API_URL}/health", timeout=10)
    r.raise_for_status()
    return r.json()


def predict_single(recency: float, frequency: float, monetary: float):
    r = requests.post(
        f"{API_URL}/predict",
        json={"Recency": recency, "Frequency": frequency, "Monetary": monetary},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def predict_batch_csv(file_bytes: bytes, filename: str):
    files = {"file": (filename, file_bytes, "text/csv")}
    r = requests.post(f"{API_URL}/predict/batch", files=files, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


# ============================================================
# Sidebar
# ============================================================
st.sidebar.title("🎯 RFM Segmentation")
st.sidebar.caption(f"API endpoint: `{API_URL}`")

try:
    health = fetch_health()
    st.sidebar.success(
        f"API connected\n\n"
        f"Training samples: **{health['n_training_samples']:,}**\n\n"
        f"Clusters: **{health['n_clusters']}**"
    )
except Exception as e:
    st.sidebar.error(f"API tidak bisa diakses:\n{e}")
    st.stop()

page = st.sidebar.radio(
    "Navigasi",
    ["🔍 Single Prediction", "📁 Batch Prediction", "📊 Cluster Overview"],
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Model: K-Means (k=4) pada dataset Brazilian E-Commerce Olist. "
    "Fitur: Recency, Frequency (log), Monetary (log)."
)


# ============================================================
# Page 1: Single Prediction
# ============================================================
if page == "🔍 Single Prediction":
    st.title("🔍 Prediksi Segmen Pelanggan")
    st.caption(
        "Masukkan nilai RFM mentah pelanggan untuk menentukan segmen dan "
        "rekomendasi strategi pemasaran."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Input RFM")
        with st.form("rfm_form"):
            recency = st.number_input(
                "Recency (hari sejak transaksi terakhir)",
                min_value=0,
                max_value=2000,
                value=30,
                step=1,
                help="0 = baru transaksi hari ini.",
            )
            frequency = st.number_input(
                "Frequency (jumlah order)",
                min_value=1,
                max_value=50,
                value=2,
                step=1,
                help="Berapa kali pelanggan order.",
            )
            monetary = st.number_input(
                "Monetary (total nilai transaksi, BRL)",
                min_value=0.0,
                max_value=100_000.0,
                value=350.0,
                step=10.0,
                format="%.2f",
                help="Total uang yang dibelanjakan pelanggan.",
            )
            submitted = st.form_submit_button("🚀 Prediksi", type="primary")

    with col2:
        st.subheader("Hasil")
        if not submitted:
            st.info("Isi form di kiri lalu klik **Prediksi**.")
        else:
            try:
                with st.spinner("Memprediksi..."):
                    result = predict_single(recency, frequency, monetary)
            except Exception as e:
                st.error(f"Gagal prediksi: {e}")
                st.stop()

            segment = result["segment"]
            color = SEGMENT_COLORS.get(segment, "#7f8c8d")

            st.markdown(
                f"""
                <div style="
                    background:{color}22;
                    border-left:6px solid {color};
                    padding:1rem 1.2rem;
                    border-radius:8px;
                ">
                  <div style="font-size:0.85rem;color:#666;">Segmen</div>
                  <div style="font-size:1.8rem;font-weight:700;color:{color};">
                    {segment}
                  </div>
                  <div style="font-size:0.85rem;color:#666;margin-top:0.5rem;">
                    Cluster ID: <b>{result['cluster']}</b>
                    &nbsp;·&nbsp;
                    Distance to centroid: <b>{result['distance_to_centroid']}</b>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            strategy = result.get("strategy", {}) or {}
            if strategy:
                st.markdown("##### 📌 Deskripsi segmen")
                st.write(strategy.get("deskripsi", "-"))

                st.markdown("##### 💡 Rekomendasi strategi")
                for item in strategy.get("strategi", []):
                    st.markdown(f"- {item}")

# ============================================================
# Page 2: Batch Prediction
# ============================================================
elif page == "📁 Batch Prediction":
    st.title("📁 Batch Prediction via CSV")
    st.caption(
        "Upload CSV dengan kolom **Recency, Frequency, Monetary** "
        "untuk klasifikasi banyak pelanggan sekaligus."
    )

    with st.expander("📋 Format CSV yang diharapkan", expanded=False):
        sample = pd.DataFrame(
            {
                "Recency": [10, 200, 500],
                "Frequency": [3, 1, 1],
                "Monetary": [5000.0, 100.0, 50.0],
            }
        )
        st.dataframe(sample, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download contoh CSV",
            sample.to_csv(index=False).encode(),
            file_name="rfm_sample.csv",
            mime="text/csv",
        )

    uploaded = st.file_uploader("Pilih file CSV", type=["csv"])
    if uploaded is None:
        st.info("Belum ada file. Upload CSV di atas.")
    else:
        try:
            with st.spinner(f"Memprediksi {uploaded.name}..."):
                response = predict_batch_csv(uploaded.getvalue(), uploaded.name)
        except Exception as e:
            st.error(f"Gagal: {e}")
            st.stop()

        df = pd.DataFrame(response["rows"])
        st.success(f"Berhasil memprediksi **{response['n_rows']:,} baris**.")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Hasil prediksi")
            st.dataframe(df, use_container_width=True, hide_index=True)
            buf = io.BytesIO()
            df.to_csv(buf, index=False)
            st.download_button(
                "⬇️ Download hasil CSV",
                buf.getvalue(),
                file_name="predictions.csv",
                mime="text/csv",
            )

        with col2:
            st.subheader("Distribusi segmen")
            seg_counts = df["Segment"].value_counts()
            st.bar_chart(seg_counts)
            st.dataframe(
                seg_counts.rename("count").reset_index(names="Segment"),
                use_container_width=True,
                hide_index=True,
            )

# ============================================================
# Page 3: Cluster Overview
# ============================================================
else:
    st.title("📊 Cluster Overview")
    st.caption("Profil setiap cluster yang dihasilkan dari training.")

    try:
        clusters = fetch_clusters()
    except Exception as e:
        st.error(f"Gagal load clusters: {e}")
        st.stop()

    df_cl = pd.DataFrame(clusters)

    st.subheader("Ringkasan numerik")
    st.dataframe(
        df_cl[
            [
                "cluster",
                "segment",
                "n_customers",
                "pct_customers",
                "Recency_mean",
                "Frequency_mean",
                "Monetary_mean",
                "Monetary_total",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Jumlah pelanggan per cluster")
        st.bar_chart(df_cl.set_index("segment")["n_customers"])
    with col2:
        st.subheader("Total monetary per cluster")
        st.bar_chart(df_cl.set_index("segment")["Monetary_total"])

    st.subheader("Detail strategi per segmen")
    for cl in clusters:
        seg = cl["segment"]
        color = SEGMENT_COLORS.get(seg, "#7f8c8d")
        with st.expander(
            f"Cluster {cl['cluster']} — {seg}  "
            f"({cl['n_customers']:,} pelanggan, {cl['pct_customers']}%)"
        ):
            mcol1, mcol2, mcol3 = st.columns(3)
            mcol1.metric("Recency (avg)", f"{cl['Recency_mean']:.0f} hari")
            mcol2.metric("Frequency (avg)", f"{cl['Frequency_mean']:.2f}")
            mcol3.metric("Monetary (avg)", f"R$ {cl['Monetary_mean']:,.2f}")

            strategy = cl.get("strategy", {}) or {}
            if strategy.get("deskripsi"):
                st.markdown(f"**Deskripsi:** {strategy['deskripsi']}")
            if strategy.get("strategi"):
                st.markdown("**Rekomendasi strategi:**")
                for s in strategy["strategi"]:
                    st.markdown(f"- {s}")
