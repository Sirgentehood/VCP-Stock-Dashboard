from pathlib import Path
from typing import Optional, Dict, List, Tuple

import pandas as pd
import streamlit as st

st.set_page_config(page_title="VCP Market Analytics", layout="wide")

st.markdown(
    """
<style>
:root {
  --card-bg: rgba(255,255,255,0.03);
  --card-border: rgba(128,128,128,0.16);
  --muted: rgba(255,255,255,0.72);
  --strong: #1ec977;
  --developing: #f0b429;
  --weak: #ff6b6b;
  --neutral: #77a8ff;
}
.block-container {padding-top: 0.7rem; padding-bottom: 1.4rem; padding-left: 0.7rem; padding-right: 0.7rem; max-width: 1400px;}
.stImage img {border-radius: 0.9rem; border: 1px solid rgba(255,255,255,0.08);}
[data-testid="stMetric"] {background: var(--card-bg); border: 1px solid var(--card-border); padding: 0.45rem 0.6rem; border-radius: 0.85rem;}
[data-testid="stMetricLabel"] {font-size: 0.78rem;}
[data-testid="stMetricValue"] {font-size: 1.08rem;}
pre {white-space: pre-wrap !important; word-break: break-word !important;}
.card, .hero-card, .stock-card, .mini-card, .info-card, .learn-card, .list-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 0.85rem 0.95rem;
}
.hero-card {padding: 1rem 1rem;}
.kicker {font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted);}
.big-number {font-size: 1.38rem; font-weight: 800; margin-top: 0.08rem; margin-bottom: 0.1rem;}
.muted {color: var(--muted);}
.row-wrap {display:flex; flex-wrap:wrap; gap:0.38rem; margin-top:0.35rem;}
.chip {
  display:inline-block;
  border: 1px solid var(--card-border);
  background: rgba(255,255,255,0.04);
  padding: 0.18rem 0.48rem;
  border-radius: 999px;
  font-size: 0.73rem;
}
.strong-chip {border-color: rgba(30,201,119,0.35); color: var(--strong);}
.developing-chip {border-color: rgba(240,180,41,0.35); color: var(--developing);}
.weak-chip {border-color: rgba(255,107,107,0.35); color: var(--weak);}
.neutral-chip {border-color: rgba(119,168,255,0.35); color: var(--neutral);}
.status-pill {
  display:inline-block;
  font-size:0.75rem;
  font-weight:700;
  padding:0.18rem 0.52rem;
  border-radius:999px;
  margin-bottom:0.45rem;
}
.status-strong {background: rgba(30,201,119,0.14); color: var(--strong); border:1px solid rgba(30,201,119,0.35);}
.status-developing {background: rgba(240,180,41,0.14); color: var(--developing); border:1px solid rgba(240,180,41,0.35);}
.status-weak {background: rgba(255,107,107,0.14); color: var(--weak); border:1px solid rgba(255,107,107,0.35);}
.stock-title {font-size: 1.14rem; font-weight: 700; margin-bottom: 0.08rem;}
.stock-subtitle {font-size: 0.92rem; color: var(--muted); margin-bottom: 0.4rem;}
.stock-card {margin-bottom: 0.65rem;}
.small-label {font-size: 0.75rem; color: var(--muted);}
.disclosure {
  border-left: 4px solid rgba(240,180,41,0.55);
  background: rgba(240,180,41,0.08);
  border-radius: 12px;
  padding: 0.7rem 0.85rem;
  font-size: 0.86rem;
  margin-bottom: 0.8rem;
}
.section-note {font-size: 0.82rem; color: var(--muted); margin-bottom: 0.45rem;}
.list-tight {margin: 0.2rem 0 0 1rem; padding: 0;}
.list-tight li {margin: 0.18rem 0;}
.simple-list-item {
  border-bottom: 1px solid rgba(255,255,255,0.06);
  padding: 0.55rem 0;
}
.simple-list-item:last-child {border-bottom:none;}
.learn-card {margin-bottom: 0.55rem;}
@media (max-width: 768px) {
  .block-container {padding-top: 0.45rem; padding-left: 0.35rem; padding-right: 0.35rem;}
  h1 {font-size: 1.35rem !important;}
  h2 {font-size: 1.06rem !important;}
  h3 {font-size: 0.96rem !important;}
  .card, .hero-card, .stock-card, .mini-card, .info-card, .learn-card, .list-card {padding: 0.72rem 0.75rem;}
}
</style>
""",
    unsafe_allow_html=True,
)

LABELS = {
    "Strong": {"css": "status-strong", "chip": "strong-chip"},
    "Developing": {"css": "status-developing", "chip": "developing-chip"},
    "Weak": {"css": "status-weak", "chip": "weak-chip"},
}

@st.cache_data(show_spinner=False)
def load_csv(path: str, mtime_ns: int) -> pd.DataFrame:
    return pd.read_csv(path)

def safe_read(path: str) -> pd.DataFrame:
    p = Path(path)
    return load_csv(str(p), p.stat().st_mtime_ns) if p.exists() else pd.DataFrame()

def resolve_chart_path(charts_dir: str, ticker: str, suffix: str) -> Optional[Path]:
    filename = ticker.replace(".", "_") + suffix
    path = Path(charts_dir) / filename
    return path if path.exists() else None

@st.cache_data(show_spinner=False)
def load_image_bytes(path: str, mtime_ns: int) -> bytes:
    return Path(path).read_bytes()

def safe_image_bytes(path: Optional[Path]) -> Optional[bytes]:
    if not path or not path.exists():
        return None
    return load_image_bytes(str(path), path.stat().st_mtime_ns)

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "Company Name" not in out.columns:
        for col in ["Company Name_x", "Company Name_y"]:
            if col in out.columns:
                out["Company Name"] = out[col]
                break
    if "Industry" not in out.columns:
        for col in ["Industry_x", "Industry_y"]:
            if col in out.columns:
                out["Industry"] = out[col]
                break
    drop_cols = [c for c in ["Company Name_x", "Company Name_y", "Industry_x", "Industry_y", "Ticker"] if c in out.columns]
    if drop_cols:
        out = out.drop(columns=drop_cols)
    return out

def add_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = normalize_columns(df)
    numeric_cols = [
        "daily_score", "weekly_score", "combined_score", "final_daily_score", "final_weekly_score",
        "final_combined_score", "rs_3m_pct", "rs_6m_pct", "combined_score_change",
        "rank_change", "avg_combined_score", "current_rank", "prev_rank",
        "change_1d_pct", "change_1w_pct", "change_1m_pct", "change_ytd_pct"
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(2)
    if not out.empty and "classification" not in out.columns:
        out["classification"] = out.apply(classify_stock, axis=1)
    return out

def classify_stock(row: pd.Series) -> str:
    stage = str(row.get("stage", ""))
    score = pd.to_numeric(row.get("final_combined_score", row.get("combined_score")), errors="coerce")
    rs3 = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs6 = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")
    if stage == "Stage 2" and pd.notna(score) and score >= 60:
        return "Strong"
    if pd.notna(score) and score >= 45 and stage in {"Stage 1", "Stage 2", "Stage 3"}:
        return "Developing"
    if stage in {"Stage 3", "Stage 4"}:
        return "Weak"
    if pd.notna(rs3) and pd.notna(rs6) and rs3 < 0 and rs6 < 0:
        return "Weak"
    return "Developing"

def format_num(x) -> str:
    v = pd.to_numeric(x, errors="coerce")
    return "n/a" if pd.isna(v) else f"{float(v):.1f}"

def stage_display(stage: str) -> str:
    mapping = {
        "Stage 1": "Accumulation",
        "Stage 2": "Uptrend",
        "Stage 3": "Distribution",
        "Stage 4": "Downtrend",
    }
    return mapping.get(stage, stage or "Unknown")

def stage_description(stage: str) -> str:
    mapping = {
        "Stage 1": "Price is stabilizing or recovering after a weaker phase.",
        "Stage 2": "Price is in the strongest trend phase within this framework.",
        "Stage 3": "Price is losing trend quality and moving into a topping phase.",
        "Stage 4": "Price is in a weaker downward phase.",
    }
    return mapping.get(stage, "Description not available.")


def stage_help_text(stage: str) -> str:
    mapping = {
        "Stage 1": "Stage 1 means the stock is stabilizing or recovering after a weaker phase.",
        "Stage 2": "Stage 2 means the stock is in the strongest uptrend phase within this framework.",
        "Stage 3": "Stage 3 means the stock is losing trend quality and moving into a topping phase.",
        "Stage 4": "Stage 4 means the stock is in a weaker downward phase.",
    }
    return mapping.get(stage, "Stage meaning not available.")

def trend_text(row: pd.Series) -> str:
    label = str(row.get("classification", "Developing"))
    if label == "Strong":
        return "Strong trend"
    if label == "Weak":
        return "Weak trend"
    return "Developing trend"

def stage2_count_by_industry(combined_df: pd.DataFrame) -> pd.DataFrame:
    if combined_df.empty or "Industry" not in combined_df.columns or "stage" not in combined_df.columns:
        return pd.DataFrame(columns=["Industry", "Current Rank", "Stage 2 Stocks"])
    grp = combined_df.groupby("Industry", dropna=True)["stage"].apply(lambda s: int((s == "Stage 2").sum())).reset_index(name="Stage 2 Stocks")
    return grp

def market_tone(regime_df: pd.DataFrame, combined_df: pd.DataFrame) -> str:
    if not regime_df.empty and "regime_label" in regime_df.columns:
        label = str(regime_df.iloc[0]["regime_label"])
        return {"risk_on": "Constructive", "mixed": "Mixed", "risk_off": "Defensive"}.get(label, "Mixed")
    strong_count = int((combined_df["classification"] == "Strong").sum()) if "classification" in combined_df.columns else 0
    if strong_count >= 15:
        return "Constructive"
    if strong_count >= 6:
        return "Mixed"
    return "Defensive"

def top_industry_text(industry_df: pd.DataFrame, n: int = 3) -> str:
    if industry_df.empty or "Industry" not in industry_df.columns:
        return "Not available"
    return ", ".join(industry_df.head(n)["Industry"].astype(str).tolist())

def company_choices(df: pd.DataFrame) -> Dict[str, str]:
    if df.empty:
        return {}
    tmp = df.dropna(subset=["Company Name", "ticker"]).copy()
    tmp["Company Name"] = tmp["Company Name"].astype(str).str.strip()
    tmp = tmp.sort_values(["Company Name", "ticker"]).drop_duplicates(subset=["Company Name"], keep="first")
    return dict(zip(tmp["Company Name"], tmp["ticker"]))

def stock_reason(row: pd.Series) -> str:
    return f"{stage_display(str(row.get('stage', '')))} • {row.get('Industry', 'Unknown')}"

def render_disclosure():
    st.markdown(
        """
<div class="disclosure">
This dashboard is an informational analytics tool. It shows rule-based classifications and market summaries. It does not provide personalized investment advice, suitability analysis, buy calls, sell calls, or allocation recommendations.
</div>
""",
        unsafe_allow_html=True,
    )

def render_summary_card(title: str, value: str, subtitle: str):
    st.markdown(
        f"""
<div class="hero-card">
  <div class="kicker">{title}</div>
  <div class="big-number">{value}</div>
  <div class="muted">{subtitle}</div>
</div>
""",
        unsafe_allow_html=True,
    )

def render_stock_card(row: pd.Series, show_scores: bool = False, show_change_pct: str = ""):
    label = row.get("classification", "Developing")
    style = LABELS.get(label, LABELS["Developing"])
    company = row.get("Company Name", row.get("ticker", "Stock"))
    ticker = str(row.get("ticker", "")).replace(".NS", "")
    stage_raw = str(row.get("stage", ""))
    stage = stage_display(stage_raw)
    industry = row.get("Industry", "Unknown")
    trend = trend_text(row)
    pct_html = f"<div style='font-size:1.0rem;font-weight:800;margin-top:0.2rem;'>{show_change_pct}</div>" if show_change_pct else ""
    st.markdown(
        f"""
<div class="stock-card">
  <div class="stock-title">{company}</div>
  <div class="stock-subtitle">{ticker}</div>
  <div class="status-pill {style["css"]}">{label}</div>
  <div style="font-size:0.98rem; margin-top:0.15rem;"><b>{stage}</b></div>
  <div style="font-size:0.95rem; margin-top:0.1rem;">{trend}</div>
  <div style="font-size:0.95rem; margin-top:0.1rem;">{industry}</div>
  {pct_html}
</div>
""",
        unsafe_allow_html=True,
    )

def render_simple_list(rows: pd.DataFrame, message_col: str = "message"):
    st.markdown("<div class='list-card'>", unsafe_allow_html=True)
    for _, row in rows.iterrows():
        st.markdown(
            f"""
<div class="simple-list-item">
  <div><b>{row.get('title','')}</b></div>
  <div class="muted">{row.get(message_col,'')}</div>
</div>
""",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

def home_tab(combined_df: pd.DataFrame, industry_df: pd.DataFrame, regime_df: pd.DataFrame, changes_df: pd.DataFrame):
    tone = market_tone(regime_df, combined_df)
    top_industries = top_industry_text(industry_df)
    setup_count = int((combined_df["classification"] == "Strong").sum()) if not combined_df.empty else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        render_summary_card("Market tone", tone, "Simple summary of the latest saved scan")
    with c2:
        render_summary_card("Top industries", top_industries, "Industries leading the current scan")
    with c3:
        render_summary_card("Setups", str(setup_count), "Stocks currently in the top classification")

    st.divider()
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("### Top stocks today")
        st.caption("Highest-ranked names from the latest scan.")
        top = combined_df.sort_values("final_combined_score", ascending=False).head(5)
        for _, row in top.iterrows():
            render_stock_card(row, show_scores=False)
    with right:
        st.markdown("### What changed today")
        items = []
        if not changes_df.empty:
            if "new_top_10" in changes_df.columns:
                items.append({"title": f"{int(changes_df['new_top_10'].fillna(False).sum())} names entered Top 10", "message": "These names moved into the top-ranked group in the latest saved run."})
            if "new_daily_breakout" in changes_df.columns:
                items.append({"title": f"{int(changes_df['new_daily_breakout'].fillna(False).sum())} new daily breakout conditions", "message": "These names newly met the daily breakout rule in the latest run."})
            if "entered_stage_2" in changes_df.columns:
                items.append({"title": f"{int(changes_df['entered_stage_2'].fillna(False).sum())} names entered Stage 2", "message": "These names moved into the uptrend phase in the latest run."})
        if not items:
            items = [{"title": "No major changes found", "message": "The latest saved run did not show large classification changes."}]
        render_simple_list(pd.DataFrame(items))

def stocks_tab(combined_df: pd.DataFrame, company_map: Dict[str, str], daily_dir: str, weekly_dir: str):
    st.markdown("### Stocks")
    st.caption("Browse stocks by company name, ordered from higher rank to lower rank.")
    ranked = combined_df.sort_values("final_combined_score", ascending=False).reset_index(drop=True).copy()
    names = ranked["Company Name"].dropna().astype(str).tolist()
    if "selected_stock_name" not in st.session_state or st.session_state["selected_stock_name"] not in names:
        st.session_state["selected_stock_name"] = names[0]

    current_idx = names.index(st.session_state["selected_stock_name"])
    csel, cprev, cnext = st.columns([4,1,1])
    selected_name = csel.selectbox("Select stock", names, index=current_idx, key="stocks_select_name_ordered")
    if selected_name != st.session_state["selected_stock_name"]:
        st.session_state["selected_stock_name"] = selected_name
        st.rerun()

    with cprev:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("Previous", use_container_width=True, disabled=(current_idx == 0), key="stocks_prev_btn"):
            st.session_state["selected_stock_name"] = names[current_idx - 1]
            st.rerun()
    with cnext:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("Next", use_container_width=True, disabled=(current_idx == len(names) - 1), key="stocks_next_btn"):
            st.session_state["selected_stock_name"] = names[current_idx + 1]
            st.rerun()

    row = ranked[ranked["Company Name"] == st.session_state["selected_stock_name"]].iloc[0]
    left, right = st.columns([0.95, 1.05])
    with left:
        render_stock_card(row, show_scores=False)
        stage_raw = str(row.get("stage", ""))
        with st.expander(f"What does {stage_raw} mean?", expanded=False):
            st.write(stage_help_text(stage_raw))
    with right:
        dpath = resolve_chart_path(daily_dir, row["ticker"], "_daily.png")
        wpath = resolve_chart_path(weekly_dir, row["ticker"], "_weekly.png")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Daily")
            if dpath:
                st.image(safe_image_bytes(dpath), use_container_width=True)
            else:
                st.info("Daily chart not available.")
        with c2:
            st.markdown("#### Weekly")
            if wpath:
                st.image(safe_image_bytes(wpath), use_container_width=True)
            else:
                st.info("Weekly chart not available.")

    st.divider()
    st.markdown("### Browse more stocks")
    browse = ranked.head(20)
    for _, r in browse.iterrows():
        render_stock_card(r, show_scores=False)

def market_tab(industry_df: pd.DataFrame, regime_df: pd.DataFrame, combined_df: pd.DataFrame, industry_changes_df: pd.DataFrame):
    st.markdown("### Market")
    st.caption("Industry strength with current rank and number of Stage 2 stocks.")
    view = industry_df.copy()
    if view.empty:
        st.info("Industry data not available.")
        return
    stage2 = stage2_count_by_industry(combined_df)
    if "Industry" in view.columns:
        view = view.merge(stage2, on="Industry", how="left")
    rank_col = "current_rank" if "current_rank" in view.columns else ("rs_rank" if "rs_rank" in view.columns else None)
    cols = []
    if "Industry" in view.columns:
        cols.append("Industry")
    if rank_col:
        cols.append(rank_col)
        view = view.rename(columns={rank_col: "Current Rank"})
        cols[-1] = "Current Rank"
    if "Stage 2 Stocks" in view.columns:
        cols.append("Stage 2 Stocks")
    st.dataframe(view[cols].sort_values("Current Rank", ascending=True), use_container_width=True, hide_index=True, height=520)

def movers_tab(price_moves_df: pd.DataFrame):
    st.markdown("### Movers")
    st.caption("This view shows which names moved most over the selected time window.")
    if price_moves_df.empty:
        st.info("Price move data not found yet.")
        return
    window_map = {
        "1 Day": "change_1d_pct",
        "1 Week": "change_1w_pct",
        "1 Month": "change_1m_pct",
        "YTD": "change_ytd_pct",
    }
    selected = st.radio("Move window", list(window_map.keys()), horizontal=True, index=0)
    col = window_map[selected]
    df = price_moves_df.copy()
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[col]).copy()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### Fastest upward moves • {selected}")
        leaders = df.sort_values([col, "final_combined_score"], ascending=[False, False]).head(10)
        for _, row in leaders.iterrows():
            render_stock_card(row, show_scores=False, show_change_pct=f"{float(row[col]):+.2f}%")
    with c2:
        st.markdown(f"#### Fastest downward moves • {selected}")
        laggards = df.sort_values([col, "final_combined_score"], ascending=[True, False]).head(10)
        for _, row in laggards.iterrows():
            render_stock_card(row, show_scores=False, show_change_pct=f"{float(row[col]):+.2f}%")

def portfolio_tab(combined_df: pd.DataFrame, company_map: Dict[str, str]):
    st.markdown("### Portfolio")
    st.caption("Add stocks by company name and view their latest classifications.")
    if "portfolio_names" not in st.session_state:
        st.session_state["portfolio_names"] = []

    names = sorted(company_map.keys())
    available = [n for n in names if n not in st.session_state["portfolio_names"]]
    selected_to_add = st.selectbox("Add stock", [""] + available, key="portfolio_add_name")
    if st.button("Add to portfolio", use_container_width=True, key="portfolio_add_btn") and selected_to_add:
        st.session_state["portfolio_names"].append(selected_to_add)
        st.rerun()

    if not st.session_state["portfolio_names"]:
        st.info("No stocks added yet.")
        return

    current = combined_df[combined_df["Company Name"].isin(st.session_state["portfolio_names"])].copy()
    c1, c2, c3 = st.columns(3)
    with c1:
        render_summary_card("Total stocks", str(len(current)), "Stocks currently added to this list")
    with c2:
        render_summary_card("Strong", str(int((current["classification"] == "Strong").sum())), "Current Strong classifications")
    with c3:
        render_summary_card("Developing", str(int((current["classification"] == "Developing").sum())), "Current Developing classifications")

    st.divider()
    for _, row in current.sort_values(["classification", "final_combined_score"], ascending=[True, False]).iterrows():
        render_stock_card(row, show_scores=False)

    removable = [""] + sorted(st.session_state["portfolio_names"])
    selected_remove = st.selectbox("Remove stock", removable, key="portfolio_remove_name")
    if st.button("Remove from portfolio", use_container_width=True, key="portfolio_remove_btn") and selected_remove:
        st.session_state["portfolio_names"] = [x for x in st.session_state["portfolio_names"] if x != selected_remove]
        st.rerun()

def learn_tab(help_image_path: str):
    st.markdown("### Learn")
    st.caption("Simple explanations for beginners.")
    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown(
            """
<div class="learn-card">
  <div class="stock-title">What this site is trying to show</div>
  <ul class="list-tight">
    <li>Which stocks currently look technically stronger or weaker inside this model.</li>
    <li>Which industries are improving or weakening relative to others.</li>
    <li>How daily and weekly structure compare for the same stock.</li>
  </ul>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
<div class="learn-card">
  <div class="stock-title">Simple labels</div>
  <ul class="list-tight">
    <li><b>Strong</b>: the model sees stronger structure right now.</li>
    <li><b>Developing</b>: the model sees mixed or still-building structure.</li>
    <li><b>Weak</b>: the model sees weaker structure right now.</li>
  </ul>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
<div class="learn-card">
  <div class="stock-title">Stages</div>
  <ul class="list-tight">
    <li><b>Stage 1</b>: Accumulation</li>
    <li><b>Stage 2</b>: Uptrend</li>
    <li><b>Stage 3</b>: Distribution</li>
    <li><b>Stage 4</b>: Downtrend</li>
  </ul>
</div>
""",
            unsafe_allow_html=True,
        )
    with right:
        img = Path(help_image_path)
        if img.exists():
            st.image(str(img), caption="Reference image for the four market phases", use_container_width=True)
        else:
            st.info("Stage image not found.")

def advanced_tab(daily_df: pd.DataFrame, weekly_df: pd.DataFrame, combined_df: pd.DataFrame, changes_df: pd.DataFrame, industry_changes_df: pd.DataFrame):
    st.markdown("### Advanced")
    st.caption("Simplified tables without raw score columns.")
    def keep_simple(df: pd.DataFrame) -> pd.DataFrame:
        wanted = [c for c in ["Company Name", "ticker", "classification", "stage", "Industry"] if c in df.columns]
        out = df[wanted].copy() if wanted else df.copy()
        if "ticker" in out.columns:
            out = out.rename(columns={"ticker": "Ticker"})
            out["Ticker"] = out["Ticker"].astype(str).str.replace(".NS", "", regex=False)
        return out

    with st.expander("Overall ranked", expanded=True):
        st.dataframe(keep_simple(combined_df), use_container_width=True, hide_index=True, height=360)
    with st.expander("Daily ranked", expanded=False):
        st.dataframe(keep_simple(daily_df), use_container_width=True, hide_index=True, height=320)
    with st.expander("Weekly ranked", expanded=False):
        st.dataframe(keep_simple(weekly_df), use_container_width=True, hide_index=True, height=320)
    with st.expander("Stock changes", expanded=False):
        st.dataframe(keep_simple(changes_df), use_container_width=True, hide_index=True, height=320)
    with st.expander("Industry changes", expanded=False):
        keep = [c for c in ["Industry"] if c in industry_changes_df.columns]
        st.dataframe(industry_changes_df[keep] if keep else industry_changes_df, use_container_width=True, hide_index=True, height=320)

