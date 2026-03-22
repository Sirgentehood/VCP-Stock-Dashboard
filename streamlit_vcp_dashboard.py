import os
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from vcp_daily_weekly_with_charts import build_outputs


st.set_page_config(page_title="VCP Dashboard", layout="wide")


@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def safe_read(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.exists():
        return load_csv(str(p))
    return pd.DataFrame()


def resolve_chart_path(charts_dir: str, ticker: str, suffix: str) -> Optional[Path]:
    filename = ticker.replace(".", "_") + suffix
    path = Path(charts_dir) / filename
    return path if path.exists() else None


def filter_table(df: pd.DataFrame, search_text: str, industries: list[str], stages: list[str], min_score: float, bucket_col: str, buckets: list[str], score_col: str) -> pd.DataFrame:
    out = df.copy()
    if search_text:
        s = search_text.strip().lower()
        mask = pd.Series(False, index=out.index)
        for col in [c for c in ["ticker", "Company Name", "Industry", "notes"] if c in out.columns]:
            mask = mask | out[col].astype(str).str.lower().str.contains(s, na=False)
        out = out[mask]
    if industries and "Industry" in out.columns:
        out = out[out["Industry"].isin(industries)]
    if stages and "stage" in out.columns:
        out = out[out["stage"].isin(stages)]
    if buckets and bucket_col in out.columns:
        out = out[out[bucket_col].isin(buckets)]
    if score_col in out.columns:
        out = out[out[score_col].fillna(0) >= min_score]
    return out.reset_index(drop=True)


def metric_row(combined: pd.DataFrame, daily: pd.DataFrame, weekly: pd.DataFrame, industry: pd.DataFrame, regime: pd.DataFrame) -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    risk = regime.iloc[0]["regime_label"] if not regime.empty and "regime_label" in regime.columns else "n/a"
    c1.metric("Market regime", risk)
    c2.metric("Combined candidates", len(combined))
    c3.metric("Daily actionable", int(daily["daily_setup_bucket"].isin(["breakout_today", "near_pivot"]).sum()) if "daily_setup_bucket" in daily.columns else 0)
    c4.metric("Weekly actionable", int(weekly["weekly_setup_bucket"].isin(["weekly_breakout", "weekly_near_pivot"]).sum()) if "weekly_setup_bucket" in weekly.columns else 0)
    c5.metric("Industries tracked", len(industry))


def stock_detail_tab(combined: pd.DataFrame, daily_charts_dir: str, weekly_charts_dir: str) -> None:
    st.subheader("Stock detail")
    if combined.empty:
        st.info("Run the scan first.")
        return

    choices = combined["ticker"].dropna().tolist() if "ticker" in combined.columns else []
    ticker = st.selectbox("Select ticker", choices)
    if not ticker:
        return

    row = combined[combined["ticker"] == ticker].head(1)
    if row.empty:
        st.info("Ticker not found in combined table.")
        return

    row = row.iloc[0]
    info_cols = [
        "ticker", "Company Name", "Industry", "stage", "daily_setup_bucket", "weekly_setup_bucket",
        "combined_bucket", "daily_score", "weekly_score", "combined_score", "industry_boost",
        "final_combined_score", "rs_3m_pct", "rs_6m_pct", "avg_turnover_inr", "notes"
    ]
    info = {k: row[k] for k in info_cols if k in row.index}
    st.json(info)

    c1, c2 = st.columns(2)
    dpath = resolve_chart_path(daily_charts_dir, ticker, "_daily.png")
    wpath = resolve_chart_path(weekly_charts_dir, ticker, "_weekly.png")

    with c1:
        st.markdown("**Daily chart**")
        if dpath:
            st.image(str(dpath), use_container_width=True)
        else:
            st.info("No daily chart exported for this ticker in current top set.")
    with c2:
        st.markdown("**Weekly chart**")
        if wpath:
            st.image(str(wpath), use_container_width=True)
        else:
            st.info("No weekly chart exported for this ticker in current top set.")


def ranked_tab(title: str, df: pd.DataFrame, bucket_col: str, score_col: str) -> None:
    st.subheader(title)
    if df.empty:
        st.info("Run the scan first.")
        return

    key_prefix = title.lower().replace(" ", "_")

    c1, c2, c3, c4 = st.columns(4)
    search = c1.text_input(f"Search in {title}", key=f"{key_prefix}_search")
    industries = c2.multiselect(
        "Industry",
        sorted(df["Industry"].dropna().unique().tolist()) if "Industry" in df.columns else [],
        key=f"{key_prefix}_industry",
    )
    stages = c3.multiselect(
        "Stage",
        sorted(df["stage"].dropna().unique().tolist()) if "stage" in df.columns else [],
        key=f"{key_prefix}_stage",
    )
    buckets = c4.multiselect(
        "Bucket",
        sorted(df[bucket_col].dropna().unique().tolist()) if bucket_col in df.columns else [],
        key=f"{key_prefix}_bucket",
    )
    min_score = st.slider(
        f"Min {score_col}",
        0.0,
        100.0,
        60.0,
        1.0,
        key=f"{key_prefix}_min_score",
    )

    filtered = filter_table(df, search, industries, stages, min_score, bucket_col, buckets, score_col)
    st.dataframe(filtered, use_container_width=True, height=520)


def industry_tab(industry: pd.DataFrame) -> None:
    st.subheader("Industry strength")
    if industry.empty:
        st.info("Run the scan first.")
        return
    st.dataframe(industry, use_container_width=True, height=520)


def dashboard_tab(combined: pd.DataFrame, daily: pd.DataFrame, weekly: pd.DataFrame, industry: pd.DataFrame, regime: pd.DataFrame) -> None:
    metric_row(combined, daily, weekly, industry, regime)
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Top combined")
        cols = [c for c in ["ticker", "Company Name", "Industry", "stage", "combined_bucket", "final_combined_score"] if c in combined.columns]
        st.dataframe(combined[cols].head(15), use_container_width=True, height=420)
    with c2:
        st.markdown("### Top industries")
        cols = [c for c in ["Industry", "avg_combined_score", "rs_rank", "strong_combined", "actionable_daily", "actionable_weekly"] if c in industry.columns]
        st.dataframe(industry[cols].head(15), use_container_width=True, height=420)


st.title("VCP Screener Dashboard")

with st.sidebar:
    st.header("Run scan")
    universe_path = "nifty500.csv"
    outdir = st.text_input("Output folder", value="outputs")
    top_charts = st.number_input("Top charts to export", min_value=3, max_value=50, value=10, step=1)
    run_scan = st.button("Run / Refresh scan", use_container_width=True)
    st.caption("Place this app file and the engine file in the same folder.")

if run_scan:
    with st.spinner("Running screener and exporting charts..."):
        try:
            outputs = build_outputs(universe_path=universe_path, outdir=outdir, top_n_charts=int(top_charts))
            st.session_state["outputs"] = outputs
            st.success("Scan complete")
        except Exception as e:
            st.error(f"Scan failed: {e}")

outputs = st.session_state.get("outputs", {
    "daily": str(Path(outdir) / "vcp_daily_ranked.csv"),
    "weekly": str(Path(outdir) / "vcp_weekly_ranked.csv"),
    "combined": str(Path(outdir) / "vcp_combined_ranked.csv"),
    "industry": str(Path(outdir) / "industry_strength.csv"),
    "regime": str(Path(outdir) / "market_regime.csv"),
    "daily_charts_dir": str(Path(outdir) / "charts" / "daily"),
    "weekly_charts_dir": str(Path(outdir) / "charts" / "weekly"),
})

daily_df = safe_read(outputs["daily"])
weekly_df = safe_read(outputs["weekly"])
combined_df = safe_read(outputs["combined"])
industry_df = safe_read(outputs["industry"])
regime_df = safe_read(outputs["regime"])

tabs = st.tabs(["Dashboard", "Combined", "Daily", "Weekly", "Industries", "Stock detail"])
with tabs[0]:
    dashboard_tab(combined_df, daily_df, weekly_df, industry_df, regime_df)
with tabs[1]:
    ranked_tab("Combined candidates", combined_df, "combined_bucket", "final_combined_score")
with tabs[2]:
    ranked_tab("Daily candidates", daily_df, "daily_setup_bucket", "final_daily_score")
with tabs[3]:
    ranked_tab("Weekly candidates", weekly_df, "weekly_setup_bucket", "final_weekly_score")
with tabs[4]:
    industry_tab(industry_df)
with tabs[5]:
    stock_detail_tab(combined_df, outputs["daily_charts_dir"], outputs["weekly_charts_dir"])
