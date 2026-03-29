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
.stock-title {font-size: 1rem; font-weight: 700; margin-bottom: 0.08rem;}
.stock-subtitle {font-size: 0.82rem; color: var(--muted); margin-bottom: 0.4rem;}
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

def render_stock_card(row: pd.Series, show_scores: bool = False):
    label = row.get("classification", "Developing")
    style = LABELS.get(label, LABELS["Developing"])
    company = row.get("Company Name", row.get("ticker", "Stock"))
    ticker = str(row.get("ticker", "")).replace(".NS", "")
    reason = stock_reason(row)
    stage = stage_display(str(row.get("stage", "")))
    score = format_num(row.get("final_combined_score"))
    st.markdown(
        f"""
<div class="stock-card">
  <div class="status-pill {style["css"]}">{label}</div>
  <div class="stock-title">{company}</div>
  <div class="stock-subtitle">{ticker}</div>
  <div>{reason}</div>
  <div class="row-wrap">
    <span class="chip {style["chip"]}">{label}</span>
    <span class="chip neutral-chip">{stage}</span>
    <span class="chip neutral-chip">{row.get("Industry", "Unknown")}</span>
    {"<span class='chip neutral-chip'>Score " + score + "</span>" if show_scores else ""}
  </div>
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
    strong_count = int((combined_df["classification"] == "Strong").sum()) if not combined_df.empty else 0
    change_count = 0
    if not changes_df.empty:
        for col in ["new_daily_breakout", "new_weekly_breakout", "entered_stage_2", "new_top_10"]:
            if col in changes_df.columns:
                change_count += int(changes_df[col].fillna(False).sum())

    c1, c2, c3 = st.columns(3)
    with c1:
        render_summary_card("Market tone", tone, "Simple summary of the latest saved scan")
    with c2:
        render_summary_card("Stronger setups", str(strong_count), "Stocks currently classified as Strong")
    with c3:
        render_summary_card("Leading industries", top_industries, "Top industries from the latest saved scan")

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
    st.caption("Use company names to browse the latest classifications and charts.")
    col1, col2, col3 = st.columns([1.4, 1, 1])
    names = sorted(company_map.keys())
    selected_name = col1.selectbox("Select stock", names, key="stocks_select_name")
    label_filter = col2.selectbox("Classification", ["All", "Strong", "Developing", "Weak"], key="stocks_label_filter")
    industry_options = ["All"] + sorted(combined_df["Industry"].dropna().astype(str).unique().tolist()) if "Industry" in combined_df.columns else ["All"]
    industry_filter = col3.selectbox("Industry", industry_options, key="stocks_industry_filter")

    filtered = combined_df.copy()
    if label_filter != "All":
        filtered = filtered[filtered["classification"] == label_filter]
    if industry_filter != "All":
        filtered = filtered[filtered["Industry"] == industry_filter]

    ticker = company_map[selected_name]
    row = combined_df[combined_df["ticker"] == ticker].iloc[0]
    left, right = st.columns([0.95, 1.05])
    with left:
        render_stock_card(row, show_scores=True)
        st.markdown(
            f"""
<div class="info-card">
  <div class="small-label">What this means</div>
  <ul class="list-tight">
    <li>Classification: {row.get("classification")}</li>
    <li>Stage: {stage_display(str(row.get("stage", "")))}</li>
    <li>Industry: {row.get("Industry", "Unknown")}</li>
    <li>Stage meaning: {stage_description(str(row.get("stage", "")))}</li>
  </ul>
</div>
""",
            unsafe_allow_html=True,
        )
    with right:
        dpath = resolve_chart_path(daily_dir, ticker, "_daily.png")
        wpath = resolve_chart_path(weekly_dir, ticker, "_weekly.png")
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
    browse = filtered.sort_values("final_combined_score", ascending=False).head(20)
    for _, r in browse.iterrows():
        render_stock_card(r, show_scores=False)

def market_tab(industry_df: pd.DataFrame, regime_df: pd.DataFrame, combined_df: pd.DataFrame, industry_changes_df: pd.DataFrame):
    st.markdown("### Market")
    tone = market_tone(regime_df, combined_df)
    c1, c2, c3 = st.columns(3)
    with c1:
        render_summary_card("Market tone", tone, "High-level read of the latest run")
    with c2:
        render_summary_card("Top industries", top_industry_text(industry_df), "Industries leading the current scan")
    with c3:
        rising = int((industry_changes_df["rank_change"].fillna(0) > 0).sum()) if not industry_changes_df.empty and "rank_change" in industry_changes_df.columns else 0
        render_summary_card("Industries improving", str(rising), "Industries moving higher in rank")

    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown("#### Industry strength")
        cols = [c for c in ["Industry", "avg_combined_score", "rs_rank", "strong_combined", "actionable_daily", "actionable_weekly"] if c in industry_df.columns]
        if cols:
            st.dataframe(industry_df[cols], use_container_width=True, hide_index=True, height=420)
        else:
            st.info("Industry strength data not available.")
    with right:
        st.markdown("#### Industry rotation")
        cols = [c for c in ["Industry", "current_rank", "prev_rank", "rank_change", "combined_score_change"] if c in industry_changes_df.columns]
        if cols:
            rising_df = industry_changes_df.sort_values(["rank_change", "combined_score_change"], ascending=[False, False]).head(10)
            st.dataframe(rising_df[cols], use_container_width=True, hide_index=True, height=420)
        else:
            st.info("Industry rotation data not available.")

def movers_tab(price_moves_df: pd.DataFrame):
    st.markdown("### Movers")
    st.caption("This view shows which names moved most over the selected time window. Movement and classification are separate concepts.")
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
            render_stock_card(row, show_scores=False)
    with c2:
        st.markdown(f"#### Fastest downward moves • {selected}")
        laggards = df.sort_values([col, "final_combined_score"], ascending=[True, False]).head(10)
        for _, row in laggards.iterrows():
            render_stock_card(row, show_scores=False)

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
    st.caption("Raw tables for users who want deeper detail.")
    with st.expander("Overall ranked", expanded=True):
        st.dataframe(combined_df, use_container_width=True, hide_index=True, height=360)
    with st.expander("Daily ranked", expanded=False):
        st.dataframe(daily_df, use_container_width=True, hide_index=True, height=320)
    with st.expander("Weekly ranked", expanded=False):
        st.dataframe(weekly_df, use_container_width=True, hide_index=True, height=320)
    with st.expander("Stock changes", expanded=False):
        st.dataframe(changes_df, use_container_width=True, hide_index=True, height=320)
    with st.expander("Industry changes", expanded=False):
        st.dataframe(industry_changes_df, use_container_width=True, hide_index=True, height=320)

st.title("VCP Market Analytics")
render_disclosure()

with st.sidebar:
    st.header("Settings")
    outdir = st.text_input("Output folder", value="outputs")
    help_image_path = st.text_input("Stage image", value="market_phases_reference.png")

outputs = {
    "daily": str(Path(outdir) / "vcp_daily_ranked.csv"),
    "weekly": str(Path(outdir) / "vcp_weekly_ranked.csv"),
    "combined": str(Path(outdir) / "vcp_combined_ranked.csv"),
    "industry": str(Path(outdir) / "industry_strength.csv"),
    "regime": str(Path(outdir) / "market_regime.csv"),
    "stock_changes": str(Path(outdir) / "stock_changes.csv"),
    "industry_changes": str(Path(outdir) / "industry_changes.csv"),
    "price_moves": str(Path(outdir) / "stock_price_moves.csv"),
    "daily_charts_dir": str(Path(outdir) / "charts" / "daily"),
    "weekly_charts_dir": str(Path(outdir) / "charts" / "weekly"),
}

daily_df = add_labels(safe_read(outputs["daily"]))
weekly_df = add_labels(safe_read(outputs["weekly"]))
combined_df = add_labels(safe_read(outputs["combined"]))
industry_df = add_labels(safe_read(outputs["industry"]))
regime_df = safe_read(outputs["regime"])
changes_df = add_labels(safe_read(outputs["stock_changes"]))
industry_changes_df = add_labels(safe_read(outputs["industry_changes"]))
price_moves_df = add_labels(safe_read(outputs["price_moves"]))

if combined_df.empty:
    st.warning("No output files found yet. Run the scan first.")
    st.stop()

company_map = company_choices(combined_df)

tabs = st.tabs(["Home", "Stocks", "Market", "Movers", "Learn", "Portfolio", "Advanced"])

with tabs[0]:
    home_tab(combined_df, industry_df, regime_df, changes_df)
with tabs[1]:
    stocks_tab(combined_df, company_map, outputs["daily_charts_dir"], outputs["weekly_charts_dir"])
with tabs[2]:
    market_tab(industry_df, regime_df, combined_df, industry_changes_df)
with tabs[3]:
    movers_tab(price_moves_df)
with tabs[4]:
    learn_tab(help_image_path)
with tabs[5]:
    portfolio_tab(combined_df, company_map)
with tabs[6]:
    advanced_tab(daily_df, weekly_df, combined_df, changes_df, industry_changes_df)
