import os
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

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


def add_safe_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "daily_setup_bucket" in out.columns:
        out["daily_setup_label"] = out["daily_setup_bucket"].map({
            "breakout_today": "Breakout setup detected",
            "near_pivot": "Near pivot zone",
            "forming_vcp": "Setup forming",
            "watchlist": "Watchlist",
        }).fillna(out["daily_setup_bucket"])

    if "weekly_setup_bucket" in out.columns:
        out["weekly_setup_label"] = out["weekly_setup_bucket"].map({
            "weekly_breakout": "Weekly breakout structure",
            "weekly_near_pivot": "Weekly near pivot zone",
            "weekly_forming": "Weekly structure forming",
            "weekly_watchlist": "Weekly watchlist",
        }).fillna(out["weekly_setup_bucket"])

    if "combined_bucket" in out.columns:
        out["overall_setup_label"] = out["combined_bucket"].map({
            "high_conviction_breakout": "Strong daily-weekly alignment",
            "high_conviction_near_pivot": "Strong near-pivot alignment",
            "building_setup": "Structure building",
            "watchlist": "Watchlist",
        }).fillna(out["combined_bucket"])

    return out


def filter_table(
    df: pd.DataFrame,
    search_text: str,
    industries: list[str],
    stages: list[str],
    min_score: float,
    bucket_col: str,
    buckets: list[str],
    score_col: str,
) -> pd.DataFrame:
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


def metric_row(
    combined: pd.DataFrame,
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
    industry: pd.DataFrame,
    regime: pd.DataFrame,
) -> None:
    c1, c2, c3, c4, c5 = st.columns(5)

    risk = regime.iloc[0]["regime_label"] if not regime.empty and "regime_label" in regime.columns else "n/a"
    c1.metric("Market regime", risk)
    c2.metric("Overall candidates", len(combined))
    c3.metric(
        "Daily analytical events",
        int(daily["daily_setup_bucket"].isin(["breakout_today", "near_pivot"]).sum())
        if "daily_setup_bucket" in daily.columns else 0,
    )
    c4.metric(
        "Weekly analytical events",
        int(weekly["weekly_setup_bucket"].isin(["weekly_breakout", "weekly_near_pivot"]).sum())
        if "weekly_setup_bucket" in weekly.columns else 0,
    )
    c5.metric("Industries tracked", len(industry))


def score_badge(val: float) -> str:
    if pd.isna(val):
        return "n/a"
    if val >= 80:
        return "Strong"
    if val >= 65:
        return "Moderate"
    return "Watch"


def stock_detail_tab(combined: pd.DataFrame, daily_charts_dir: str, weekly_charts_dir: str) -> None:
    st.subheader("Stock detail")

    if combined.empty:
        st.info("No scan outputs found yet.")
        return

    choices = combined["ticker"].dropna().tolist() if "ticker" in combined.columns else []
    ticker = st.selectbox("Select ticker", choices, key="stock_detail_ticker")

    if not ticker:
        return

    row = combined[combined["ticker"] == ticker].head(1)
    if row.empty:
        st.info("Ticker not found in overall table.")
        return

    row = row.iloc[0]

    summary = {
        "Ticker": row.get("ticker"),
        "Company": row.get("Company Name"),
        "Industry": row.get("Industry"),
        "Stage": row.get("stage"),
        "Daily setup": row.get("daily_setup_label", row.get("daily_setup_bucket")),
        "Weekly setup": row.get("weekly_setup_label", row.get("weekly_setup_bucket")),
        "Overall setup": row.get("overall_setup_label", row.get("combined_bucket")),
        "Daily score": row.get("daily_score"),
        "Weekly score": row.get("weekly_score"),
        "Overall score": row.get("final_combined_score", row.get("combined_score")),
        "3M relative strength": row.get("rs_3m_pct"),
        "6M relative strength": row.get("rs_6m_pct"),
        "Average turnover": row.get("avg_turnover_inr"),
        "Interpretation": row.get("notes"),
    }
    st.json(summary)

    st.markdown("### Interpretation guide")
    score_value = row.get("final_combined_score", row.get("combined_score"))
    st.write(f"Overall analytical strength: **{score_badge(score_value)}**")
    st.write("This is a rule-based screening output. It is not investment advice, a recommendation, or a buy/sell call.")

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


def ranked_tab(title: str, df: pd.DataFrame, bucket_col: str, score_col: str, label_col: str) -> None:
    st.subheader(title)

    if df.empty:
        st.info("No scan outputs found yet.")
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
        "Setup label",
        sorted(df[label_col].dropna().unique().tolist()) if label_col in df.columns else [],
        key=f"{key_prefix}_bucket",
    )
    min_score = c1.slider(
        f"Min {score_col}",
        0.0,
        100.0,
        60.0,
        1.0,
        key=f"{key_prefix}_min_score",
    )

    working = df.copy()
    if buckets and label_col in working.columns:
        working = working[working[label_col].isin(buckets)]

    filtered = filter_table(working, search, industries, stages, min_score, bucket_col, [], score_col)

    preferred_cols = [
        "ticker", "Company Name", "Industry", "stage", label_col,
        score_col, "rs_3m_pct", "rs_6m_pct", "avg_turnover_inr", "notes"
    ]
    preferred_cols = [c for c in preferred_cols if c in filtered.columns]
    st.dataframe(filtered[preferred_cols], use_container_width=True, height=520)


def industry_tab(industry: pd.DataFrame) -> None:
    st.subheader("Industry strength")

    if industry.empty:
        st.info("No scan outputs found yet.")
        return

    st.dataframe(industry, use_container_width=True, height=520)


def help_tab() -> None:
    st.subheader("How to interpret the dashboard")

    st.markdown(
        '''
**Important**  
This dashboard is for informational and educational use. It presents rule-based screening outputs and does not provide investment advice, research recommendations, target prices, or buy/sell calls.

**Daily score**  
Strength of the setup on the daily chart. Useful for timing analysis.

**Weekly score**  
Strength of the setup on the weekly chart. Useful for broader structure analysis.

**Overall score**  
Combined priority score using daily, weekly, and industry-strength inputs.

**Stage**
- Stage 1: rebuilding / bottoming
- Stage 2: established uptrend
- Stage 3: topping / mixed structure
- Stage 4: downtrend

**Daily setup label**
- Breakout setup detected
- Near pivot zone
- Setup forming
- Watchlist

**Weekly setup label**
- Weekly breakout structure
- Weekly near pivot zone
- Weekly structure forming
- Weekly watchlist

**Industry rank / boost**  
Higher means the stock belongs to a relatively stronger industry group in this model.

**Charts**
- Daily chart: short-term structure
- Weekly chart: higher-timeframe structure
'''
    )


def dashboard_tab(
    combined: pd.DataFrame,
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
    industry: pd.DataFrame,
    regime: pd.DataFrame,
) -> None:
    metric_row(combined, daily, weekly, industry, regime)
    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Top overall analytical setups")
        cols = [c for c in ["ticker", "Company Name", "Industry", "stage", "overall_setup_label", "final_combined_score"] if c in combined.columns]
        st.dataframe(combined[cols].head(15), use_container_width=True, height=420)

    with c2:
        st.markdown("### Top industries")
        cols = [c for c in ["Industry", "avg_combined_score", "rs_rank", "strong_combined", "actionable_daily", "actionable_weekly"] if c in industry.columns]
        st.dataframe(industry[cols].head(15), use_container_width=True, height=420)


st.title("VCP Market Analytics Dashboard")

st.warning(
    "This tool is for informational and educational purposes only. "
    "It presents rule-based screening outputs and does not constitute investment advice, "
    "a recommendation, or a buy/sell signal. Users should do their own research and, where needed, "
    "consult a SEBI-registered intermediary."
)

with st.sidebar:
    st.header("Data source")
    outdir = st.text_input("Output folder", value="outputs")
    st.caption("This dashboard reads the latest scheduled scan outputs.")

outputs = {
    "daily": str(Path(outdir) / "vcp_daily_ranked.csv"),
    "weekly": str(Path(outdir) / "vcp_weekly_ranked.csv"),
    "combined": str(Path(outdir) / "vcp_combined_ranked.csv"),
    "industry": str(Path(outdir) / "industry_strength.csv"),
    "regime": str(Path(outdir) / "market_regime.csv"),
    "daily_charts_dir": str(Path(outdir) / "charts" / "daily"),
    "weekly_charts_dir": str(Path(outdir) / "charts" / "weekly"),
}

daily_df = add_safe_labels(safe_read(outputs["daily"]))
weekly_df = add_safe_labels(safe_read(outputs["weekly"]))
combined_df = add_safe_labels(safe_read(outputs["combined"]))
industry_df = safe_read(outputs["industry"])
regime_df = safe_read(outputs["regime"])

if combined_df.empty and daily_df.empty and weekly_df.empty:
    st.warning("No output files found yet. Wait for the scheduled GitHub Action to generate the latest scan.")

tabs = st.tabs(["Dashboard", "Overall", "Daily", "Weekly", "Industries", "Stock detail", "Help"])

with tabs[0]:
    dashboard_tab(combined_df, daily_df, weekly_df, industry_df, regime_df)

with tabs[1]:
    ranked_tab("Overall candidates", combined_df, "combined_bucket", "final_combined_score", "overall_setup_label")

with tabs[2]:
    ranked_tab("Daily candidates", daily_df, "daily_setup_bucket", "final_daily_score", "daily_setup_label")

with tabs[3]:
    ranked_tab("Weekly candidates", weekly_df, "weekly_setup_bucket", "final_weekly_score", "weekly_setup_label")

with tabs[4]:
    industry_tab(industry_df)

with tabs[5]:
    stock_detail_tab(combined_df, outputs["daily_charts_dir"], outputs["weekly_charts_dir"])

with tabs[6]:
    help_tab()
