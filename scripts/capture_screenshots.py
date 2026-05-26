"""Capture screenshot semua halaman deployment (Streamlit + FastAPI docs).

Asumsi:
  - FastAPI    : http://localhost:8000
  - Streamlit  : http://localhost:8501
  - App sudah dijalankan via scripts/run_app.sh atau scripts/run_demo.sh

Output : reports/figures/deployment/*.png
"""
from __future__ import annotations

import asyncio
import io
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "figures" / "deployment"
OUT_DIR.mkdir(parents=True, exist_ok=True)

UI_URL  = "http://localhost:8501"
API_URL = "http://localhost:8000"

VIEWPORT = {"width": 1440, "height": 900}


async def goto_streamlit_page(page, sidebar_label: str, wait_ms: int = 3000):
    """Klik radio button di sidebar berdasarkan label."""
    await page.goto(UI_URL, wait_until="networkidle")
    # Tunggu sidebar muncul
    await page.wait_for_selector('section[data-testid="stSidebar"]', timeout=15000)
    await asyncio.sleep(2)
    # Klik label radio yang cocok
    try:
        # Streamlit radio menggunakan <label> dengan text di dalamnya
        locator = page.locator('section[data-testid="stSidebar"]').get_by_text(sidebar_label, exact=False).first
        await locator.click(timeout=10000)
        await asyncio.sleep(wait_ms / 1000)
    except Exception as e:
        print(f"  ⚠️  Gagal klik sidebar '{sidebar_label}': {e}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport=VIEWPORT)
        page = await context.new_page()

        # =====================================================
        # 1. Streamlit — Single Prediction (default page)
        # =====================================================
        print("[1/5] Streamlit Single Prediction (empty form)...")
        await page.goto(UI_URL, wait_until="networkidle")
        await page.wait_for_selector('section[data-testid="stSidebar"]', timeout=15000)
        await asyncio.sleep(3)
        await page.screenshot(path=str(OUT_DIR / "01_streamlit_single_empty.png"),
                              full_page=True)

        # =====================================================
        # 2. Streamlit — Single Prediction (after submit)
        # =====================================================
        print("[2/5] Streamlit Single Prediction (with result)...")
        # Klik tombol Prediksi (form akan submit dengan default values)
        try:
            await page.get_by_role("button", name="Prediksi").click(timeout=10000)
            await asyncio.sleep(4)
        except Exception as e:
            print(f"  ⚠️  Gagal klik Prediksi: {e}")
        await page.screenshot(path=str(OUT_DIR / "02_streamlit_single_result.png"),
                              full_page=True)

        # =====================================================
        # 3. Streamlit — Batch Prediction
        # =====================================================
        print("[3/5] Streamlit Batch Prediction...")
        await goto_streamlit_page(page, "Batch Prediction")
        await page.screenshot(path=str(OUT_DIR / "03_streamlit_batch.png"),
                              full_page=True)

        # Upload sample CSV
        try:
            sample_csv = io.BytesIO()
            sample_csv.write(b"Recency,Frequency,Monetary\n")
            sample_csv.write(b"10,3,5000\n")
            sample_csv.write(b"200,1,100\n")
            sample_csv.write(b"500,1,50\n")
            sample_csv.write(b"5,1,80\n")
            sample_csv.write(b"30,2,350\n")

            file_input = page.locator('input[type="file"]').first
            await file_input.set_input_files(files=[{
                "name": "rfm_sample.csv",
                "mimeType": "text/csv",
                "buffer": sample_csv.getvalue(),
            }])
            await asyncio.sleep(5)
            await page.screenshot(path=str(OUT_DIR / "04_streamlit_batch_result.png"),
                                  full_page=True)
        except Exception as e:
            print(f"  ⚠️  Gagal upload CSV: {e}")

        # =====================================================
        # 4. Streamlit — Cluster Overview
        # =====================================================
        print("[4/5] Streamlit Cluster Overview...")
        await goto_streamlit_page(page, "Cluster Overview", wait_ms=4000)
        await page.screenshot(path=str(OUT_DIR / "05_streamlit_cluster_overview.png"),
                              full_page=True)

        # =====================================================
        # 5. FastAPI — Swagger /docs
        # =====================================================
        print("[5/5] FastAPI Swagger /docs...")
        await page.goto(f"{API_URL}/docs", wait_until="networkidle")
        await asyncio.sleep(3)
        await page.screenshot(path=str(OUT_DIR / "06_fastapi_docs.png"),
                              full_page=True)

        await context.close()
        await browser.close()

    print()
    print("Selesai. File tersimpan di:")
    for f in sorted(OUT_DIR.glob("*.png")):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    asyncio.run(main())
