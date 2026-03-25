import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Optional

st.set_page_config(page_title="VCP Pro Dashboard", layout="wide")

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

def prep(df):
    for col in ["final_combined_score","daily_score","weekly_score","combined_score_change","rank_change"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(1)
    return df

def changes_section(stock_changes):
    st.markdown("## 🔥 What Changed")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### New Breakouts")
        df = stock_changes[stock_changes["new_daily_breakout"]]
        st.dataframe(df[["ticker","final_combined_score","combined_score_change"]], use_container_width=True)

    with c2:
        st.markdown("### Entered Stage 2")
        df = stock_changes[stock_changes["entered_stage_2"]]
        st.dataframe(df[["ticker","final_combined_score"]], use_container_width=True)

    with c3:
        st.markdown("### Big Movers")
        df = stock_changes.sort_values("combined_score_change", ascending=False).head(10)
        st.dataframe(df[["ticker","combined_score_change","rank_change"]], use_container_width=True)

def stock_view(df, daily_dir, weekly_dir):
    st.markdown("## 📊 Chart View")

    ticker = st.selectbox("Select Stock", df["ticker"].tolist())

    row = df[df["ticker"] == ticker].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Stage", row["stage"])
    c2.metric("Score", row["final_combined_score"])
    c3.metric("RS", row.get("rs_3m_pct"))

    d = resolve_chart_path(daily_dir, ticker, "_daily.png")
    w = resolve_chart_path(weekly_dir, ticker, "_weekly.png")

    if d:
        st.image(str(d), use_container_width=True)
    if w:
        st.image(str(w), use_container_width=True)

def main():
    st.title("🚀 VCP Pro Dashboard")

    st.warning("For educational purposes only. Not investment advice.")

    outdir = st.sidebar.text_input("Output folder", "outputs")

    combined = prep(safe_read(f"{outdir}/vcp_combined_ranked.csv"))
    changes = prep(safe_read(f"{outdir}/stock_changes.csv"))

    st.caption(f"Last updated: {get_last_updated(f'{outdir}/vcp_combined_ranked.csv')}")

    if combined.empty:
        st.error("No data yet")
        return

    # filters
    c1, c2 = st.columns(2)

    stage = c1.selectbox("Stage", ["All"] + sorted(combined["stage"].unique()))
    industry = c2.selectbox("Industry", ["All"] + sorted(combined["Industry"].unique()))

    df = combined.copy()
    if stage != "All":
        df = df[df["stage"] == stage]
    if industry != "All":
        df = df[df["Industry"] == industry]

    # top table
    st.markdown("## 🔝 Top Stocks")

    top = df.sort_values("final_combined_score", ascending=False).head(15)

    event = st.dataframe(top[["ticker","stage","final_combined_score"]],
                         use_container_width=True,
                         on_select="rerun",
                         selection_mode="single-row")

    if event.selection.rows:
        selected = top.iloc[event.selection.rows[0]]["ticker"]
        st.session_state["ticker"] = selected

    # chart view
    stock_view(df, f"{outdir}/charts/daily", f"{outdir}/charts/weekly")

    # changes
    if not changes.empty:
        changes_section(changes)

if __name__ == "__main__":
    main()
