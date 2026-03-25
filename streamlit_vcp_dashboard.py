import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Optional

st.set_page_config(page_title="VCP Dashboard", layout="wide")


@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def safe_read(path: str) -> pd.DataFrame:
    p = Path(path)
    return load_csv(str(p)) if p.exists() else pd.DataFrame()


def resolve_chart_path(charts_dir: str, ticker: str, suffix: str) -> Optional[Path]:
    filename = ticker.replace(".", "_") + suffix
    path = Path(charts_dir) / filename
    return path if path.exists() else None


def get_last_updated(file_path: str) -> str:
    p = Path(file_path)
    if not p.exists():
        return "Not available"
    ts = pd.Timestamp(p.stat().st_mtime, unit="s").tz_localize("UTC").tz_convert("Asia/Kolkata")
    return ts.strftime("%d %b %Y, %I:%M %p IST")


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

    for col in ["daily_score", "weekly_score", "combined_score", "final_daily_score", "final_weekly_score", "final_combined_score", "rs_3m_pct", "rs_6m_pct", "industry_boost"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(1)
    if "avg_turnover_inr" in out.columns:
        out = out.drop(columns=["avg_turnover_inr"])
    return out


def filter_table(df: pd.DataFrame, search_text: str, industries: list[str], stages: list[str], min_score: float, score_col: str, label_col: str, labels: list[str]) -> pd.DataFrame:
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
    if labels and label_col in out.columns:
        out = out[out[label_col].isin(labels)]
    if score_col in out.columns:
        out = out[out[score_col].fillna(0) >= min_score]
    return out.reset_index(drop=True)


def metric_row(combined: pd.DataFrame, daily: pd.DataFrame, weekly: pd.DataFrame, industry: pd.DataFrame, regime: pd.DataFrame, last_updated: str) -> None:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    risk = regime.iloc[0]["regime_label"] if not regime.empty and "regime_label" in regime.columns else "n/a"
    c1.metric("Market regime", risk)
    c2.metric("Overall candidates", len(combined))
    c3.metric("Daily analytical events", int(daily["daily_setup_bucket"].isin(["breakout_today", "near_pivot"]).sum()) if "daily_setup_bucket" in daily.columns else 0)
    c4.metric("Weekly analytical events", int(weekly["weekly_setup_bucket"].isin(["weekly_breakout", "weekly_near_pivot"]).sum()) if "weekly_setup_bucket" in weekly.columns else 0)
    c5.metric("Industries tracked", len(industry))
    c6.metric("Last updated", last_updated)


def ranked_tab(title: str, df: pd.DataFrame, score_col: str, label_col: str) -> None:
    st.subheader(title)
    if df.empty:
        st.info("No scan outputs found yet.")
        return

    key_prefix = title.lower().replace(" ", "_")
    c1, c2, c3, c4 = st.columns(4)
    search = c1.text_input(f"Search in {title}", key=f"{key_prefix}_search")
    industries = c2.multiselect("Industry", sorted(df["Industry"].dropna().unique().tolist()) if "Industry" in df.columns else [], key=f"{key_prefix}_industry")
    stages = c3.multiselect("Stage", sorted(df["stage"].dropna().unique().tolist()) if "stage" in df.columns else [], key=f"{key_prefix}_stage")
    labels = c4.multiselect("Setup label", sorted(df[label_col].dropna().unique().tolist()) if label_col in df.columns else [], key=f"{key_prefix}_label")
    min_score = st.slider(f"Min {score_col}", 0.0, 100.0, 60.0, 0.1, key=f"{key_prefix}_min_score")

    filtered = filter_table(df, search, industries, stages, min_score, score_col, label_col, labels)
    cols = ["ticker", "Company Name", "Industry", "stage", label_col, score_col, "rs_3m_pct", "rs_6m_pct", "notes"]
    cols = [c for c in cols if c in filtered.columns]
    st.dataframe(filtered[cols], use_container_width=True, height=520)


def industry_tab(industry: pd.DataFrame) -> None:
    st.subheader("Industry strength")
    if industry.empty:
        st.info("No scan outputs found yet.")
        return
    cols = [c for c in ["Industry", "avg_combined_score", "rs_rank", "strong_combined", "actionable_daily", "actionable_weekly"] if c in industry.columns]
    temp = industry.copy()
    for col in ["avg_combined_score", "rs_rank"]:
        if col in temp.columns:
            temp[col] = pd.to_numeric(temp[col], errors="coerce").round(1)
    st.dataframe(temp[cols], use_container_width=True, height=520)


def stage_by_industry_tab(combined: pd.DataFrame) -> None:
    st.subheader("Stage count by industry")
    if combined.empty or "Industry" not in combined.columns or "stage" not in combined.columns:
        st.info("No stage data found yet.")
        return
    pivot = combined.pivot_table(index="Industry", columns="stage", values="ticker", aggfunc="count", fill_value=0).reset_index()
    stage_cols = [c for c in pivot.columns if c != "Industry"]
    pivot["Total"] = pivot[stage_cols].sum(axis=1)
    pivot = pivot.sort_values(["Total", "Industry"], ascending=[False, True]).reset_index(drop=True)
    st.dataframe(pivot, use_container_width=True, height=540)


def stock_detail_tab(combined: pd.DataFrame, daily_charts_dir: str, weekly_charts_dir: str) -> None:
    st.subheader("Stock detail")
    if combined.empty:
        st.info("No scan outputs found yet.")
        return

    ticker = st.selectbox("Select ticker", combined["ticker"].dropna().tolist(), key="stock_detail_ticker")
    row = combined[combined["ticker"] == ticker].head(1)
    if row.empty:
        st.info("Ticker not found.")
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
        "Interpretation": row.get("notes"),
    }
    st.json(summary)
    st.caption("Scores are rule-based analytical outputs shown to one decimal place.")

    c1, c2 = st.columns(2)
    dpath = resolve_chart_path(daily_charts_dir, ticker, "_daily.png")
    wpath = resolve_chart_path(weekly_charts_dir, ticker, "_weekly.png")
    with c1:
        st.markdown("**Daily chart**")
        st.image(str(dpath), use_container_width=True) if dpath else st.info("Daily chart not available yet for this ticker.")
    with c2:
        st.markdown("**Weekly chart**")
        st.image(str(wpath), use_container_width=True) if wpath else st.info("Weekly chart not available yet for this ticker.")


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

**Charts**
- Daily chart: short-term structure
- Weekly chart: higher-timeframe structure

**Last updated**
Shows when the latest output files were last generated.
'''
    )


def dashboard_tab(combined: pd.DataFrame, daily: pd.DataFrame, weekly: pd.DataFrame, industry: pd.DataFrame, regime: pd.DataFrame, last_updated: str) -> None:
    metric_row(combined, daily, weekly, industry, regime, last_updated)
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        cols = [c for c in ["ticker", "Company Name", "Industry", "stage", "overall_setup_label", "final_combined_score"] if c in combined.columns]
        st.markdown("### Top overall analytical setups")
        st.dataframe(combined[cols].head(15), use_container_width=True, height=420)
    with c2:
        cols = [c for c in ["Industry", "avg_combined_score", "rs_rank", "strong_combined", "actionable_daily", "actionable_weekly"] if c in industry.columns]
        st.markdown("### Top industries")
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
last_updated = get_last_updated(outputs["combined"])

if combined_df.empty and daily_df.empty and weekly_df.empty:
    st.warning("No output files found yet. Wait for the scheduled GitHub Action to generate the latest scan.")

tabs = st.tabs(["Dashboard", "Overall", "Daily", "Weekly", "Industries", "Stage by Industry", "Stock detail", "Help"])
with tabs[0]:
    dashboard_tab(combined_df, daily_df, weekly_df, industry_df, regime_df, last_updated)
with tabs[1]:
    ranked_tab("Overall candidates", combined_df, "final_combined_score", "overall_setup_label")
with tabs[2]:
    ranked_tab("Daily candidates", daily_df, "final_daily_score", "daily_setup_label")
with tabs[3]:
    ranked_tab("Weekly candidates", weekly_df, "final_weekly_score", "weekly_setup_label")
with tabs[4]:
    industry_tab(industry_df)
with tabs[5]:
    stage_by_industry_tab(combined_df)
with tabs[6]:
    stock_detail_tab(combined_df, outputs["daily_charts_dir"], outputs["weekly_charts_dir"])
with tabs[7]:
    help_tab()
