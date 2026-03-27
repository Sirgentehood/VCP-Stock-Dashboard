from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

st.set_page_config(page_title="VCP Dashboard", layout="wide")

st.markdown(
    '''
<style>
.block-container {padding-top: 0.8rem; padding-bottom: 1.5rem; padding-left: 0.7rem; padding-right: 0.7rem; max-width: 1400px;}
[data-testid="stMetric"] {background: rgba(255,255,255,0.02); border: 1px solid rgba(128,128,128,0.18); padding: 0.45rem 0.65rem; border-radius: 0.75rem;}
[data-testid="stMetricLabel"] {font-size: 0.8rem;}
[data-testid="stMetricValue"] {font-size: 1.2rem;}
.stImage img {border-radius: 0.6rem; filter: saturate(1.22) contrast(1.12) brightness(1.03);}
.element-container, .stDataFrame, .stImage {margin-bottom: 0.5rem;}
@media (max-width: 768px) {
  .block-container {padding-top: 0.45rem; padding-left: 0.35rem; padding-right: 0.35rem;}
  h1 {font-size: 1.45rem !important;}
  h2 {font-size: 1.15rem !important;}
  h3 {font-size: 1rem !important;}
  [data-testid="stMetric"] {padding: 0.35rem 0.5rem;}
  [data-testid="stMetricValue"] {font-size: 1rem;}
}
pre {white-space: pre-wrap !important; word-break: break-word !important;}
</style>
''',
    unsafe_allow_html=True,
)

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
        "daily_score","weekly_score","combined_score","final_daily_score","final_weekly_score",
        "final_combined_score","rs_3m_pct","rs_6m_pct","industry_boost","combined_score_change",
        "daily_score_change","weekly_score_change","rank_change","rs_rank","avg_combined_score",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(1)
    if "avg_turnover_inr" in out.columns:
        out = out.drop(columns=["avg_turnover_inr"])
    return out

def pretty_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "ticker": "Ticker",
        "Company Name": "Company",
        "Industry": "Industry",
        "stage": "Stage",
        "overall_setup_label": "Overall Setup Label",
        "daily_setup_label": "Daily Setup Label",
        "weekly_setup_label": "Weekly Setup Label",
        "final_combined_score": "Final Score",
        "final_daily_score": "Daily Score",
        "final_weekly_score": "Weekly Score",
        "daily_score": "Daily Score",
        "weekly_score": "Weekly Score",
        "rs_3m_pct": "RS 3M",
        "rs_6m_pct": "RS 6M",
        "avg_combined_score": "Avg Final Score",
        "combined_score_change": "Score Change",
        "rank_change": "Rank Change",
        "strong_combined": "Strong Setups",
        "actionable_daily": "Daily Actionable",
        "actionable_weekly": "Weekly Actionable",
        "new_top_10": "New Top 10",
        "new_top_20": "New Top 20",
    }
    return df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

def compact_metric_grid(items):
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.metric(label, value)

def filter_table(df, search_text, industries, stages, min_score, score_col, label_col, labels):
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

def metric_row(combined, daily, weekly, industry, regime, last_updated):
    items = [
        ("Market", regime.iloc[0]["regime_label"] if not regime.empty and "regime_label" in regime.columns else "n/a"),
        ("Overall", len(combined)),
        ("Daily events", int(daily["daily_setup_bucket"].isin(["breakout_today", "near_pivot"]).sum()) if "daily_setup_bucket" in daily.columns else 0),
        ("Weekly events", int(weekly["weekly_setup_bucket"].isin(["weekly_breakout", "weekly_near_pivot"]).sum()) if "weekly_setup_bucket" in weekly.columns else 0),
        ("Industries", len(industry)),
        ("Updated", last_updated),
    ]
    compact_metric_grid(items)

def ranked_tab(title, df, score_col, label_col, show_search=True):
    st.subheader(title)
    if df.empty:
        st.info("No scan outputs found yet.")
        return
    with st.expander("Filters", expanded=False):
        c1, c2 = st.columns(2)
        if show_search:
            search = c1.text_input("Search by ticker, company, or industry", key=f"{title}_search")
        else:
            search = ""
            c1.caption("Search hidden here to keep this view simpler.")
        min_score = c2.slider(f"Min {score_col}", 0.0, 100.0, 60.0, 0.1, key=f"{title}_min")
        c3, c4, c5 = st.columns(3)
        industries = c3.multiselect("Industry", sorted(df["Industry"].dropna().unique().tolist()) if "Industry" in df.columns else [], key=f"{title}_industry")
        stages = c4.multiselect("Stage", sorted(df["stage"].dropna().unique().tolist()) if "stage" in df.columns else [], key=f"{title}_stage")
        labels = c5.multiselect("Setup", sorted(df[label_col].dropna().unique().tolist()) if label_col in df.columns else [], key=f"{title}_label")
    filtered = filter_table(df, search, industries, stages, min_score, score_col, label_col, labels)
    cols = [c for c in ["ticker", "Company Name", "Industry", "stage", label_col, score_col, "rs_3m_pct", "rs_6m_pct"] if c in filtered.columns]
    st.caption(f"{len(filtered)} results")
    st.dataframe(pretty_columns(filtered[cols]), use_container_width=True, hide_index=True, height=430)

def changes_tab(stock_changes, top_movers):
    st.subheader("What changed")
    if stock_changes.empty:
        st.info("No change data found yet.")
        return
    sections = [
        ("New daily breakouts", stock_changes[stock_changes["new_daily_breakout"]], ["ticker", "Industry", "stage", "final_combined_score", "combined_score_change"]),
        ("New weekly breakouts", stock_changes[stock_changes["new_weekly_breakout"]], ["ticker", "Industry", "stage", "final_combined_score", "combined_score_change"]),
        ("Entered Stage 2", stock_changes[stock_changes["entered_stage_2"]], ["ticker", "Industry", "final_combined_score", "combined_score_change"]),
    ]
    for title, data, cols in sections:
        with st.expander(title, expanded=False):
            present = [c for c in cols if c in data.columns]
            st.dataframe(pretty_columns(data[present]), use_container_width=True, hide_index=True, height=220)
    st.markdown("### Biggest score jumps")
    cols = [c for c in ["ticker", "Industry", "stage", "final_combined_score", "combined_score_change", "rank_change", "new_top_10", "new_top_20"] if c in top_movers.columns]
    movers = top_movers[top_movers["combined_score_change"].fillna(0) >= 5].sort_values(["combined_score_change", "rank_change"], ascending=[False, False]).head(30)
    st.dataframe(pretty_columns(movers[cols]), use_container_width=True, hide_index=True, height=300)

def industry_rotation_tab(industry_changes):
    st.subheader("Industry rotation")
    if industry_changes.empty:
        st.info("No industry rotation data found yet.")
        return
    with st.expander("Rising industries", expanded=True):
        cols = [c for c in ["Industry", "avg_combined_score", "combined_score_change", "rs_rank", "rank_change", "strong_combined"] if c in industry_changes.columns]
        rising = industry_changes.sort_values(["rank_change", "combined_score_change"], ascending=[False, False]).head(20)
        st.dataframe(pretty_columns(rising[cols]), use_container_width=True, hide_index=True, height=220)
    with st.expander("Falling industries", expanded=False):
        cols = [c for c in ["Industry", "avg_combined_score", "combined_score_change", "rs_rank", "rank_change", "strong_combined"] if c in industry_changes.columns]
        falling = industry_changes.sort_values(["rank_change", "combined_score_change"], ascending=[True, True]).head(20)
        st.dataframe(pretty_columns(falling[cols]), use_container_width=True, hide_index=True, height=220)

def industry_tab(industry):
    st.subheader("Industry strength")
    if industry.empty:
        st.info("No scan outputs found yet.")
        return
    cols = [c for c in ["Industry", "avg_combined_score", "rs_rank", "strong_combined", "actionable_daily", "actionable_weekly"] if c in industry.columns]
    st.dataframe(pretty_columns(industry[cols]), use_container_width=True, hide_index=True, height=430)

def stage_by_industry_tab(combined):
    st.subheader("Stage count by industry")
    if combined.empty or "Industry" not in combined.columns or "stage" not in combined.columns:
        st.info("No stage data found yet.")
        return
    pivot = combined.pivot_table(index="Industry", columns="stage", values="ticker", aggfunc="count", fill_value=0)
    totals = pivot.sum(axis=1)
    display = pivot.copy()
    for stage_col in display.columns:
        display[stage_col] = [f"{int(v)} ({(v / t * 100):.1f}%)" if t > 0 else "0 (0.0%)" for v, t in zip(display[stage_col], totals)]
    display["Total"] = totals.astype(int)
    display = display.reset_index().sort_values(["Total", "Industry"], ascending=[False, True]).reset_index(drop=True)
    st.dataframe(display, use_container_width=True, hide_index=True, height=430)

def stock_detail_tab(combined, daily_charts_dir, weekly_charts_dir):
    st.subheader("Stock Detail")
    if combined.empty:
        st.info("No scan outputs found yet.")
        return

    if "stock_nav_version" not in st.session_state:
        st.session_state["stock_nav_version"] = 0

    with st.expander("Filters", expanded=True):
        f1, f2, f3 = st.columns([1, 1, 2])
        stage_options = ["All", "Stage 1", "Stage 2", "Stage 3", "Stage 4"]
        available_stages = combined["stage"].dropna().unique().tolist() if "stage" in combined.columns else []
        stage_options = [s for s in stage_options if s == "All" or s in available_stages]
        selected_stage = f1.selectbox("Stage", stage_options, key="stock_detail_stage_filter")
        industry_options = ["All"] + sorted(combined["Industry"].dropna().unique().tolist()) if "Industry" in combined.columns else ["All"]
        selected_industry = f2.selectbox("Industry", industry_options, key="stock_detail_industry_filter")

        filtered_df = combined.copy()
        if selected_stage != "All":
            filtered_df = filtered_df[filtered_df["stage"] == selected_stage]
        if selected_industry != "All":
            filtered_df = filtered_df[filtered_df["Industry"] == selected_industry]
        if filtered_df.empty:
            st.warning("No stocks match selected filters.")
            return

        ticker_list = filtered_df["ticker"].dropna().tolist()
        if "selected_ticker" not in st.session_state or st.session_state["selected_ticker"] not in ticker_list:
            st.session_state["selected_ticker"] = ticker_list[0]

        current_idx = ticker_list.index(st.session_state["selected_ticker"])
        manual_ticker = f3.selectbox(
            "Stock",
            ticker_list,
            index=current_idx,
            key=f"stock_detail_ticker_selectbox_{st.session_state['stock_nav_version']}",
        )
        if manual_ticker != st.session_state["selected_ticker"]:
            st.session_state["selected_ticker"] = manual_ticker
            st.rerun()

    current_idx = ticker_list.index(st.session_state["selected_ticker"])

    nav1, nav2, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.button("⬅ Previous", use_container_width=True, disabled=(current_idx == 0), key="stock_prev_btn"):
            st.session_state["selected_ticker"] = ticker_list[current_idx - 1]
            st.session_state["stock_nav_version"] += 1
            st.rerun()
    with nav2:
        st.caption(f"{st.session_state['selected_ticker']} • {current_idx + 1} of {len(ticker_list)}")
    with nav3:
        if st.button("Next ➡", use_container_width=True, disabled=(current_idx == len(ticker_list) - 1), key="stock_next_btn"):
            st.session_state["selected_ticker"] = ticker_list[current_idx + 1]
            st.session_state["stock_nav_version"] += 1
            st.rerun()

    ticker = st.session_state["selected_ticker"]
    row = filtered_df[filtered_df["ticker"] == ticker].iloc[0]

    st.markdown("### Snapshot")
    compact_metric_grid([
        ("Stage", row.get("stage", "n/a")),
        ("Final Score", row.get("final_combined_score", row.get("combined_score", "n/a"))),
        ("Daily", row.get("daily_score", "n/a")),
        ("Weekly", row.get("weekly_score", "n/a")),
    ])

    company = row.get("Company Name", ticker)
    industry = row.get("Industry", "n/a")
    overall_setup = row.get("overall_setup_label", row.get("combined_bucket", "n/a"))
    st.caption(f"{company} • {industry} • {overall_setup}")

    st.markdown("### Charts")
    c1, c2 = st.columns(2)
    dpath = resolve_chart_path(daily_charts_dir, ticker, "_daily.png")
    wpath = resolve_chart_path(weekly_charts_dir, ticker, "_weekly.png")
    with c1:
        st.markdown("**Daily Chart**")
        if dpath:
            st.image(str(dpath), use_container_width=True)
        else:
            st.info("Daily chart not available.")
    with c2:
        st.markdown("**Weekly Chart**")
        if wpath:
            st.image(str(wpath), use_container_width=True)
        else:
            st.info("Weekly chart not available.")

    with st.expander("Interpretation", expanded=True):
        i1, i2 = st.columns(2)
        with i1:
            st.json({
                "Daily setup": row.get("daily_setup_label", row.get("daily_setup_bucket")),
                "Weekly setup": row.get("weekly_setup_label", row.get("weekly_setup_bucket")),
                "Overall setup": row.get("overall_setup_label", row.get("combined_bucket")),
                "Notes": row.get("notes"),
            })
        with i2:
            st.json({
                "RS 3M": row.get("rs_3m_pct"),
                "RS 6M": row.get("rs_6m_pct"),
            })
    st.caption("This view highlights technical structure, relative strength, and recent setup status. It is an informational analytics view and not a recommendation.")


def normalize_portfolio_ticker(x: str) -> str:
    x = str(x).strip().upper()
    if not x or x == "NAN":
        return ""
    return x if x.endswith(".NS") else f"{x}.NS"


def portfolio_tab(combined):
    st.subheader("My Portfolio")
    st.caption("Add up to 20 tickers. This is an informational analytics view only.")

    if combined.empty:
        st.info("No scan outputs found yet.")
        return

    all_tickers = sorted(combined["ticker"].dropna().unique().tolist())
    base_symbols = [t.replace(".NS", "") for t in all_tickers]

    if "portfolio_tickers" not in st.session_state:
        st.session_state["portfolio_tickers"] = []

    # ===== ADD MULTIPLE TICKERS =====
    st.markdown("### Add Tickers")

    input_text = st.text_input(
        "Enter tickers (comma separated)",
        placeholder="Example: RELIANCE, TCS, INFY"
    )

    col1, col2 = st.columns([4, 1])

    with col2:
        if st.button("Add", use_container_width=True):
            if input_text:
                raw = [x.strip() for x in input_text.split(",")]
                normalized = [normalize_portfolio_ticker(x) for x in raw]

                for t in normalized:
                    if t and t not in st.session_state["portfolio_tickers"]:
                        if len(st.session_state["portfolio_tickers"]) < 20:
                            st.session_state["portfolio_tickers"].append(t)

                st.rerun()

    st.caption(f"{len(st.session_state['portfolio_tickers'])}/20 tickers")

    if not st.session_state["portfolio_tickers"]:
        st.info("Add tickers to see portfolio analytics.")
        return

    # ===== MERGE DATA =====
    portfolio = pd.DataFrame({"ticker": st.session_state["portfolio_tickers"]})
    merged = portfolio.merge(combined, on="ticker", how="left")

    # ===== SNAPSHOT =====
    st.markdown("### Snapshot")

    stage_counts = merged["stage"].value_counts() if "stage" in merged.columns else {}
    avg_score = round(merged["final_combined_score"].mean(), 1) if "final_combined_score" in merged else 0

    compact_metric_grid([
        ("Stage 1", int(stage_counts.get("Stage 1", 0))),
        ("Stage 2", int(stage_counts.get("Stage 2", 0))),
        ("Stage 3", int(stage_counts.get("Stage 3", 0))),
        ("Stage 4", int(stage_counts.get("Stage 4", 0))),
        ("Avg Score", avg_score),
    ])

    # ===== CLEAN TABLE =====
    st.markdown("### Portfolio View")

    display = merged.copy()

    display["Ticker"] = display["ticker"].str.replace(".NS", "", regex=False)

    cols = [
        "Ticker",
        "Industry",
        "stage",
        "final_combined_score",
        "overall_setup_label",
    ]

    display = display.rename(columns={
        "stage": "Stage",
        "final_combined_score": "Final Score",
        "overall_setup_label": "Setup",
    })

    display = display[cols]

    # ===== DELETE BUTTONS INLINE =====
    delete_idx = None

    for i, row in display.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 2, 2, 3, 1])

        c1.markdown(row["Ticker"])
        c2.markdown(row.get("Industry", ""))
        c3.markdown(row.get("Stage", ""))
        c4.markdown(str(row.get("Final Score", "")))
        c5.markdown(row.get("Setup", ""))

        if c6.button("✕", key=f"del_{i}"):
            delete_idx = i

    if delete_idx is not None:
        st.session_state["portfolio_tickers"].pop(delete_idx)
        st.rerun()


def help_tab():
    st.subheader("How to read the dashboard")
    st.markdown(
        '''
**Purpose**  
This dashboard organizes rule-based market analytics so you can review technical structure, setup quality, relative strength, and industry participation in one place. It is for informational and educational use.

**Main number fields**
- **Final Score**: overall priority score after combining daily structure, weekly structure, and industry influence.
- **Daily Score**: short-term setup strength on the daily chart.
- **Weekly Score**: higher-timeframe setup strength on the weekly chart.
- **RS 3M / RS 6M**: relative strength over 3 and 6 months versus the benchmark. Higher values generally mean stronger relative performance.

**Setup labels**
- **Daily Setup Label**: short-term setup state.
- **Weekly Setup Label**: higher-timeframe setup state.
- **Overall Setup Label**: combined interpretation of daily and weekly structure.

**Changes tab**
Highlights new daily or weekly breakout conditions, new Stage 2 names, and the largest score moves versus the prior saved run.

**Rotation tab**
Shows industries improving or weakening in score/rank terms. This helps identify where leadership is broadening or narrowing.

**Stages tab**
Shows how many stocks in each industry sit in each stage, plus the percentage of that industry total in brackets.

**Portfolio tab**
Lets you track only the tickers you add manually. It summarizes how many of your selected names are in each stage and shows the same dashboard analytics for those holdings.

**Stock tab**
Best used for one-name review after filtering by stage and industry.
Use Daily and Weekly charts together: daily for timing context, weekly for broader structure.

**Careful interpretation**
A higher score does not guarantee future performance.
Use this dashboard as a structured review aid, not as a buy/sell instruction.
'''
    )

def dashboard_tab(combined, daily, weekly, industry, regime, last_updated):
    metric_row(combined, daily, weekly, industry, regime, last_updated)
    st.divider()
    with st.expander("Top overall analytical setups", expanded=True):
        cols = [c for c in ["ticker", "Company Name", "Industry", "stage", "overall_setup_label", "final_combined_score"] if c in combined.columns]
        st.dataframe(pretty_columns(combined[cols].head(15)), use_container_width=True, hide_index=True, height=260)
    with st.expander("Top industries", expanded=False):
        cols = [c for c in ["Industry", "avg_combined_score", "rs_rank", "strong_combined", "actionable_daily", "actionable_weekly"] if c in industry.columns]
        st.dataframe(pretty_columns(industry[cols].head(15)), use_container_width=True, hide_index=True, height=260)

st.title("VCP Market Analytics Dashboard")
st.warning("This tool is for informational and educational purposes only. It presents rule-based screening outputs and does not constitute investment advice, a recommendation, or a buy/sell signal. Users should do their own research and, where needed, consult a SEBI-registered intermediary.")

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

tabs = st.tabs(["Dashboard", "Overall", "Portfolio", "Stock", "Daily", "Weekly", "Changes", "Rotation", "Industries", "Stages", "Help"])
with tabs[0]:
    dashboard_tab(combined_df, daily_df, weekly_df, industry_df, regime_df, last_updated)
with tabs[1]:
    ranked_tab("Overall candidates", combined_df, "final_combined_score", "overall_setup_label", show_search=True)
with tabs[2]:
    portfolio_tab(combined_df)
with tabs[3]:
    stock_detail_tab(combined_df, outputs["daily_charts_dir"], outputs["weekly_charts_dir"])
with tabs[4]:
    ranked_tab("Daily candidates", daily_df, "final_daily_score", "daily_setup_label", show_search=False)
with tabs[5]:
    ranked_tab("Weekly candidates", weekly_df, "final_weekly_score", "weekly_setup_label", show_search=False)
with tabs[6]:
    changes_tab(stock_changes_df, top_movers_df)
with tabs[7]:
    industry_rotation_tab(industry_changes_df)
with tabs[8]:
    industry_tab(industry_df)
with tabs[9]:
    stage_by_industry_tab(combined_df)
with tabs[10]:
    help_tab()
