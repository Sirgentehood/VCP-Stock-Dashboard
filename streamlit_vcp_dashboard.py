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

    numeric_cols = [
        "daily_score",
        "weekly_score",
        "combined_score",
        "final_daily_score",
        "final_weekly_score",
        "final_combined_score",
        "rs_3m_pct",
        "rs_6m_pct",
        "industry_boost",
        "combined_score_change",
        "daily_score_change",
        "weekly_score_change",
        "rank_change",
        "rs_rank",
        "avg_combined_score",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(1)

    if "avg_turnover_inr" in out.columns:
        out = out.drop(columns=["avg_turnover_inr"])

    return out


def filter_table(
    df: pd.DataFrame,
    search_text: str,
    industries: list[str],
    stages: list[str],
    min_score: float,
    score_col: str,
    label_col: str,
    labels: list[str],
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

    if labels and label_col in out.columns:
        out = out[out[label_col].isin(labels)]

    if score_col in out.columns:
        out = out[out[score_col].fillna(0) >= min_score]

    return out.reset_index(drop=True)


def metric_row(
    combined: pd.DataFrame,
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
    industry: pd.DataFrame,
    regime: pd.DataFrame,
    last_updated: str,
) -> None:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
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
    c6.metric("Last updated", last_updated)


def ranked_tab(title: str, df: pd.DataFrame, score_col: str, label_col: str) -> None:
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
    labels = c4.multiselect(
        "Setup label",
        sorted(df[label_col].dropna().unique().tolist()) if label_col in df.columns else [],
        key=f"{key_prefix}_label",
    )
    min_score = c1.slider(
        f"Min {score_col}",
        0.0,
        100.0,
        60.0,
        0.1,
        key=f"{key_prefix}_min_score",
    )

    filtered = filter_table(df, search, industries, stages, min_score, score_col, label_col, labels)
    cols = [c for c in ["ticker", "Company Name", "Industry", "stage", label_col, score_col, "rs_3m_pct", "rs_6m_pct", "notes"] if c in filtered.columns]
    st.dataframe(filtered[cols], use_container_width=True, hide_index=True, height=520)


def changes_tab(stock_changes: pd.DataFrame, top_movers: pd.DataFrame) -> None:
    st.subheader("What changed")

    if stock_changes.empty:
        st.info("No change data found yet.")
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### New daily breakout setups")
        cols = [c for c in ["ticker", "Company Name", "Industry", "stage", "final_combined_score", "combined_score_change"] if c in stock_changes.columns]
        st.dataframe(
            stock_changes[stock_changes["new_daily_breakout"]][cols].sort_values("final_combined_score", ascending=False),
            use_container_width=True,
            hide_index=True,
            height=260,
        )

    with c2:
        st.markdown("### New weekly breakout structures")
        cols = [c for c in ["ticker", "Company Name", "Industry", "stage", "final_combined_score", "combined_score_change"] if c in stock_changes.columns]
        st.dataframe(
            stock_changes[stock_changes["new_weekly_breakout"]][cols].sort_values("final_combined_score", ascending=False),
            use_container_width=True,
            hide_index=True,
            height=260,
        )

    with c3:
        st.markdown("### Entered Stage 2")
        cols = [c for c in ["ticker", "Company Name", "Industry", "final_combined_score", "combined_score_change"] if c in stock_changes.columns]
        st.dataframe(
            stock_changes[stock_changes["entered_stage_2"]][cols].sort_values("final_combined_score", ascending=False),
            use_container_width=True,
            hide_index=True,
            height=260,
        )

    st.markdown("### Biggest score jumps")
    cols = [c for c in ["ticker", "Company Name", "Industry", "stage", "final_combined_score", "combined_score_change", "rank_change", "new_top_10", "new_top_20"] if c in top_movers.columns]
    movers = top_movers[top_movers["combined_score_change"].fillna(0) >= 5].sort_values(["combined_score_change", "rank_change"], ascending=[False, False]).head(30)
    st.dataframe(movers[cols], use_container_width=True, hide_index=True, height=360)


def industry_rotation_tab(industry_changes: pd.DataFrame) -> None:
    st.subheader("Industry rotation")

    if industry_changes.empty:
        st.info("No industry rotation data found yet.")
        return

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Rising industries")
        cols = [c for c in ["Industry", "avg_combined_score", "combined_score_change", "rs_rank", "rank_change", "strong_combined", "new_cluster"] if c in industry_changes.columns]
        rising = industry_changes.sort_values(["rank_change", "combined_score_change"], ascending=[False, False]).head(20)
        st.dataframe(rising[cols], use_container_width=True, hide_index=True, height=360)

    with c2:
        st.markdown("### Falling industries")
        cols = [c for c in ["Industry", "avg_combined_score", "combined_score_change", "rs_rank", "rank_change", "strong_combined", "new_cluster"] if c in industry_changes.columns]
        falling = industry_changes.sort_values(["rank_change", "combined_score_change"], ascending=[True, True]).head(20)
        st.dataframe(falling[cols], use_container_width=True, hide_index=True, height=360)

    st.markdown("### New clusters")
    clusters = industry_changes[industry_changes["new_cluster"] == True]
    cols = [c for c in ["Industry", "avg_combined_score", "combined_score_change", "rs_rank", "rank_change", "strong_combined", "actionable_daily", "actionable_weekly"] if c in clusters.columns]
    st.dataframe(clusters[cols], use_container_width=True, hide_index=True, height=260)


def industry_tab(industry: pd.DataFrame) -> None:
    st.subheader("Industry strength")

    if industry.empty:
        st.info("No scan outputs found yet.")
        return

    cols = [c for c in ["Industry", "avg_combined_score", "rs_rank", "strong_combined", "actionable_daily", "actionable_weekly"] if c in industry.columns]
    st.dataframe(industry[cols], use_container_width=True, hide_index=True, height=520)


def stage_by_industry_tab(combined: pd.DataFrame) -> None:
    st.subheader("Stage count by industry")

    if combined.empty or "Industry" not in combined.columns or "stage" not in combined.columns:
        st.info("No stage data found yet.")
        return

    pivot = combined.pivot_table(index="Industry", columns="stage", values="ticker", aggfunc="count", fill_value=0).reset_index()
    stage_cols = [c for c in pivot.columns if c != "Industry"]
    pivot["Total"] = pivot[stage_cols].sum(axis=1)
    pivot = pivot.sort_values(["Total", "Industry"], ascending=[False, True]).reset_index(drop=True)
    st.dataframe(pivot, use_container_width=True, hide_index=True, height=540)


def stock_detail_tab(combined: pd.DataFrame, daily_charts_dir: str, weekly_charts_dir: str) -> None:
    st.subheader("Stock Detail")

    if combined.empty:
        st.info("No scan outputs found yet.")
        return

    st.markdown("### Filters")
    c1, c2 = st.columns(2)

    stage_options = ["All", "Stage 1", "Stage 2", "Stage 3", "Stage 4"]
    available_stages = combined["stage"].dropna().unique().tolist() if "stage" in combined.columns else []
    stage_options = [s for s in stage_options if s == "All" or s in available_stages]
    selected_stage = c1.selectbox("Stage", stage_options, key="stock_detail_stage_filter")

    industry_options = ["All"] + sorted(combined["Industry"].dropna().unique().tolist()) if "Industry" in combined.columns else ["All"]
    selected_industry = c2.selectbox("Industry", industry_options, key="stock_detail_industry_filter")

    filtered_df = combined.copy()
    if selected_stage != "All":
        filtered_df = filtered_df[filtered_df["stage"] == selected_stage]
    if selected_industry != "All":
        filtered_df = filtered_df[filtered_df["Industry"] == selected_industry]

    if filtered_df.empty:
        st.warning("No stocks match selected filters")
        return

    st.markdown("### Top Stocks")
    preview_cols = [c for c in ["ticker", "stage", "final_combined_score"] if c in filtered_df.columns]
    preview_df = filtered_df.sort_values("final_combined_score", ascending=False)[preview_cols].head(10).reset_index(drop=True)

    event = st.dataframe(
        preview_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="stock_detail_preview_table",
    )

    selected_rows = event.selection.rows if event and hasattr(event, "selection") else []
    if selected_rows:
        st.session_state["selected_ticker"] = preview_df.iloc[selected_rows[0]]["ticker"]

    st.markdown("### Select Stock")
    ticker_list = filtered_df["ticker"].dropna().tolist()
    default_ticker = st.session_state.get("selected_ticker")
    default_index = ticker_list.index(default_ticker) if default_ticker in ticker_list else 0

    ticker = st.selectbox(
        "Ticker",
        ticker_list,
        index=default_index,
        key="stock_detail_ticker",
    )

    row = filtered_df[filtered_df["ticker"] == ticker].iloc[0]

    st.markdown("### Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Stage", row.get("stage"))
    c2.metric("Overall Score", row.get("final_combined_score"))
    c3.metric("Industry", row.get("Industry"))

    st.divider()

    st.markdown("### Analytical View")
    summary = {
        "Daily setup": row.get("daily_setup_label", row.get("daily_setup_bucket")),
        "Weekly setup": row.get("weekly_setup_label", row.get("weekly_setup_bucket")),
        "Overall setup": row.get("overall_setup_label", row.get("combined_bucket")),
        "Daily score": row.get("daily_score"),
        "Weekly score": row.get("weekly_score"),
        "3M RS": row.get("rs_3m_pct"),
        "6M RS": row.get("rs_6m_pct"),
        "Notes": row.get("notes"),
    }
    st.json(summary)
    st.caption("All values are rule-based analytical outputs (not recommendations).")

    st.markdown("### Charts")
    c1, c2 = st.columns(2)
    dpath = resolve_chart_path(daily_charts_dir, ticker, "_daily.png")
    wpath = resolve_chart_path(weekly_charts_dir, ticker, "_weekly.png")

    with c1:
        st.markdown("**Daily Chart**")
        if dpath:
            st.image(str(dpath), use_container_width=True)
        else:
            st.info("Daily chart not available")

    with c2:
        st.markdown("**Weekly Chart**")
        if wpath:
            st.image(str(wpath), use_container_width=True)
        else:
            st.info("Weekly chart not available")


def help_tab() -> None:
    st.subheader("How to interpret the dashboard")
    st.markdown("""
**Important**  
This dashboard is for informational and educational use. It presents rule-based screening outputs and does not provide investment advice, research recommendations, target prices, or buy/sell calls.

**What changed**  
Shows new breakout events, Stage 2 entries, score jumps, and rank movement compared with the prior run.

**Industry rotation**  
Shows rising/falling industries and newly formed clusters based on comparative rank and score movement.
""")


def dashboard_tab(
    combined: pd.DataFrame,
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
    industry: pd.DataFrame,
    regime: pd.DataFrame,
    last_updated: str,
) -> None:
    metric_row(combined, daily, weekly, industry, regime, last_updated)
    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Top overall analytical setups")
        cols = [c for c in ["ticker", "Company Name", "Industry", "stage", "overall_setup_label", "final_combined_score"] if c in combined.columns]
        st.dataframe(combined[cols].head(15), use_container_width=True, hide_index=True, height=420)

    with c2:
        st.markdown("### Top industries")
        cols = [c for c in ["Industry", "avg_combined_score", "rs_rank", "strong_combined", "actionable_daily", "actionable_weekly"] if c in industry.columns]
        st.dataframe(industry[cols].head(15), use_container_width=True, hide_index=True, height=420)


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
    "stock_changes": str(Path(outdir) / "stock_changes.csv"),
    "industry_changes": str(Path(outdir) / "industry_changes.csv"),
    "top_movers": str(Path(outdir) / "top_movers.csv"),
    "daily_charts_dir": str(Path(outdir) / "charts" / "daily"),
    "weekly_charts_dir": str(Path(outdir) / "charts" / "weekly"),
}

daily_df = add_safe_labels(safe_read(outputs["daily"]))
weekly_df = add_safe_labels(safe_read(outputs["weekly"]))
combined_df = add_safe_labels(safe_read(outputs["combined"]))
industry_df = add_safe_labels(safe_read(outputs["industry"]))
regime_df = safe_read(outputs["regime"])
stock_changes_df = add_safe_labels(safe_read(outputs["stock_changes"]))
industry_changes_df = add_safe_labels(safe_read(outputs["industry_changes"]))
top_movers_df = add_safe_labels(safe_read(outputs["top_movers"]))
last_updated = get_last_updated(outputs["combined"])

if combined_df.empty and daily_df.empty and weekly_df.empty:
    st.warning("No output files found yet. Wait for the scheduled GitHub Action to generate the latest scan.")

tabs = st.tabs([
    "Dashboard",
    "Overall",
    "Daily",
    "Weekly",
    "What changed",
    "Industry rotation",
    "Industries",
    "Stage by Industry",
    "Stock detail",
    "Help",
])

with tabs[0]:
    dashboard_tab(combined_df, daily_df, weekly_df, industry_df, regime_df, last_updated)
with tabs[1]:
    ranked_tab("Overall candidates", combined_df, "final_combined_score", "overall_setup_label")
with tabs[2]:
    ranked_tab("Daily candidates", daily_df, "final_daily_score", "daily_setup_label")
with tabs[3]:
    ranked_tab("Weekly candidates", weekly_df, "final_weekly_score", "weekly_setup_label")
with tabs[4]:
    changes_tab(stock_changes_df, top_movers_df)
with tabs[5]:
    industry_rotation_tab(industry_changes_df)
with tabs[6]:
    industry_tab(industry_df)
with tabs[7]:
    stage_by_industry_tab(combined_df)
with tabs[8]:
    stock_detail_tab(combined_df, outputs["daily_charts_dir"], outputs["weekly_charts_dir"])
with tabs[9]:
    help_tab()
