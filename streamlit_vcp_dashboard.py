import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Market Structure Radar", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
:root {
  --card-bg: rgba(255,255,255,0.03);
  --card-border: rgba(128,128,128,0.16);
  --muted: rgba(255,255,255,0.72);
  --strong: #1ec977;
  --developing: #f0b429;
  --weak: #ff6b6b;
  --up: #1ec977;
  --down: #ff6b6b;
  --stage1: #6c5ce7;
  --stage2: #00b3b3;
  --stage3: #d4a017;
  --stage4: #8e7dff;
}
.block-container {padding-top: 0.45rem; padding-bottom: 1.2rem; padding-left: 0.7rem; padding-right: 0.7rem; max-width: 1400px;}
[data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
.stTabs [data-baseweb="tab"] {font-size: 2.15rem; font-weight: 1700;}
.stTabs [data-baseweb="tab-list"] {gap: 1.55rem; margin-top: 1.1rem;}
.hero-card, .stock-card, .list-card, .learn-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 0.8rem 0.9rem;
}
.hero-card {padding: 0.95rem 1rem;}
.kicker {font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted);}
.big-number {font-size: 1.34rem; font-weight: 800; margin-top: 0.08rem; margin-bottom: 0.1rem;}
.muted {color: var(--muted);}
.status-pill {
  display:inline-block; font-size:0.74rem; font-weight:700; padding:0.18rem 0.5rem; border-radius:999px; white-space:nowrap;
}
.status-strong {background: rgba(30,201,119,0.14); color: var(--strong); border:1px solid rgba(30,201,119,0.35);}
.status-developing {background: rgba(240,180,41,0.14); color: var(--developing); border:1px solid rgba(240,180,41,0.35);}
.status-weak {background: rgba(255,107,107,0.14); color: var(--weak); border:1px solid rgba(255,107,107,0.35);}
.stock-title {font-size: 1.02rem; font-weight: 700; margin-bottom: 0.06rem; line-height: 1.2;}
.meta-line {font-size: 0.93rem; font-weight: 600; line-height: 1.25; margin-top: 0.1rem;}
.stock-subtitle {font-size: 0.92rem; color: var(--muted); margin-top: 0.2rem; line-height: 1.2;}
.stock-card {margin-bottom: 0.42rem;}
.stage-border-1 {border-left: 5px solid var(--stage1);}
.stage-border-2 {border-left: 5px solid var(--stage2);}
.stage-border-3 {border-left: 5px solid var(--stage3);}
.stage-border-4 {border-left: 5px solid var(--stage4);}
.change-badge-up {font-size: 1.12rem; font-weight: 900; margin-top: 0.1rem; color: var(--up);}
.change-badge-down {font-size: 1.12rem; font-weight: 900; margin-top: 0.1rem; color: var(--down);}
.change-side-up {border-left: 5px solid var(--up);}
.change-side-down {border-left: 5px solid var(--down);}
.disclosure {
  border-left: 4px solid rgba(240,180,41,0.55);
  background: rgba(240,180,41,0.08);
  border-radius: 12px; padding: 0.7rem 0.85rem; font-size: 0.86rem; margin-bottom: 0.7rem; margin-top: 1rem;
}
.simple-list-item {border-bottom: 1px solid rgba(255,255,255,0.06); padding: 0.55rem 0;}
.simple-list-item:last-child {border-bottom:none;}
.list-tight {margin: 0.2rem 0 0 1rem; padding: 0;}
@media (max-width: 768px) {
  .block-container {padding-top: 0.35rem; padding-left: 0.35rem; padding-right: 0.35rem;}
  .stTabs [data-baseweb="tab"] {font-size: 0.93rem;}
}
</style>
""", unsafe_allow_html=True)

LABELS = {
    "Strong": {"css": "status-strong"},
    "Developing": {"css": "status-developing"},
    "Weak": {"css": "status-weak"},
}

@st.cache_data(show_spinner=False)
def load_csv(path: str, mtime_ns: int) -> pd.DataFrame:
    return pd.read_csv(path)

def safe_read(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    try:
        return load_csv(str(p), p.stat().st_mtime_ns)
    except Exception:
        return pd.DataFrame()

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

def classify_stock(row: pd.Series) -> str:
    stage = str(row.get("stage", ""))
    score = pd.to_numeric(row.get("final_combined_score", row.get("combined_score")), errors="coerce")
    rs3 = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs6 = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")
    if stage == "Stage 2" and pd.notna(score) and score >= 60:
        return "Strong"
    if stage in {"Stage 3", "Stage 4"}:
        return "Weak"
    if pd.notna(rs3) and pd.notna(rs6) and rs3 < 0 and rs6 < 0:
        return "Weak"
    return "Developing"

def ensure_label(df: pd.DataFrame) -> pd.DataFrame:
    out = normalize_columns(df)
    numeric_cols = [
        "final_combined_score", "avg_combined_score", "current_rank", "prev_rank", "rank_change",
        "change_1d_pct", "change_1w_pct", "change_1m_pct", "change_ytd_pct", "rs_rank"
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if not out.empty and "label" not in out.columns and "classification" not in out.columns:
        out["label"] = out.apply(classify_stock, axis=1)
    elif "classification" in out.columns and "label" not in out.columns:
        out["label"] = out["classification"]
    return out

def resolve_chart_path(charts_dir: str, ticker: str, suffix: str):
    filename = ticker.replace(".", "_") + suffix
    path = Path(charts_dir) / filename
    return path if path.exists() else None

@st.cache_data(show_spinner=False)
def load_image_bytes(path: str, mtime_ns: int) -> bytes:
    return Path(path).read_bytes()

def safe_image_bytes(path):
    if not path or not path.exists():
        return None
    return load_image_bytes(str(path), path.stat().st_mtime_ns)

def stage_display(stage: str) -> str:
    return {
        "Stage 1": "Accumulation",
        "Stage 2": "Uptrend",
        "Stage 3": "Distribution",
        "Stage 4": "Downtrend",
    }.get(stage, stage or "Unknown")

def trend_text(row: pd.Series) -> str:
    label = str(row.get("label", row.get("classification", "Developing")))
    if label == "Strong":
        return "Strong trend"
    if label == "Weak":
        return "Weak trend"
    return "Developing trend"

def market_tone(regime_df: pd.DataFrame, combined_df: pd.DataFrame) -> str:
    if not regime_df.empty and "regime_label" in regime_df.columns:
        label = str(regime_df.iloc[0]["regime_label"])
        return {"risk_on": "Risk On", "mixed": "Mixed", "risk_off": "Risk Off"}.get(label, "Mixed")
    strong_count = int((combined_df["label"] == "Strong").sum()) if not combined_df.empty and "label" in combined_df.columns else 0
    if strong_count >= 15:
        return "Risk On"
    if strong_count >= 6:
        return "Mixed"
    return "Risk Off"

def top_industry_text(industry_df: pd.DataFrame, n: int = 3) -> str:
    if industry_df.empty or "Industry" not in industry_df.columns:
        return "Not available"
    return ", ".join(industry_df.head(n)["Industry"].astype(str).tolist())

def company_choices(df: pd.DataFrame):
    if df.empty:
        return {}
    tmp = df.dropna(subset=["Company Name", "ticker"]).copy()
    tmp["Company Name"] = tmp["Company Name"].astype(str).str.strip()
    tmp = tmp.sort_values(["final_combined_score", "Company Name"], ascending=[False, True])
    tmp = tmp.drop_duplicates(subset=["Company Name"], keep="first")
    return dict(zip(tmp["Company Name"], tmp["ticker"]))

def render_disclosure():
    st.markdown("""
<div class="disclosure">
This dashboard is an informational analytics tool. It shows rule-based classifications and market summaries. It does not provide personalized investment advice, suitability analysis, buy calls, sell calls, or allocation recommendations.
</div>
""", unsafe_allow_html=True)

def render_summary_card(title: str, value: str, subtitle: str):
    st.markdown(f"""
<div class="hero-card">
  <div class="kicker">{title}</div>
  <div class="big-number">{value}</div>
  <div class="muted">{subtitle}</div>
</div>
""", unsafe_allow_html=True)

def _stage_border_class(stage_raw: str) -> str:
    return {
        "Stage 1": "stage-border-1",
        "Stage 2": "stage-border-2",
        "Stage 3": "stage-border-3",
        "Stage 4": "stage-border-4",
    }.get(stage_raw, "")

def card(row: pd.Series, pct=None, highlight=None, use_stage_color=False):
    label = row.get("label", row.get("classification", "Developing"))
    style = LABELS.get(label, LABELS["Developing"])
    company = row.get("Company Name", row.get("ticker", "Stock"))
    ticker = str(row.get("ticker", "")).replace(".NS", "")
    stage_raw = str(row.get("stage", "Unknown"))
    trend = trend_text(row)
    phase = stage_display(stage_raw)
    border_cls = _stage_border_class(stage_raw) if use_stage_color else ""
    if highlight == "up":
        border_cls = f"{border_cls} change-side-up".strip()
    elif highlight == "down":
        border_cls = f"{border_cls} change-side-down".strip()
    change_html = ""
    if pct is not None:
        cls = "change-badge-up" if pct > 0 else "change-badge-down"
        change_html = f"<div class='{cls}'>{pct:+.2f}%</div>"
    st.markdown(f"""
<div class="stock-card {border_cls}">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.6rem;">
    <div style="min-width:0; flex:1;">
      <div class="stock-title">{company} ({ticker})</div>
      <div class="meta-line">{stage_raw} * {trend} * {phase}</div>
      <div class="stock-subtitle">{row.get("Industry", "Unknown")}</div>
    </div>
    <div style="display:flex; flex-direction:column; align-items:flex-end; gap:0.05rem;">
      <div class="status-pill {style["css"]}">{label}</div>
      {change_html}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

def render_simple_list(rows: pd.DataFrame):
    st.markdown("<div class='list-card'>", unsafe_allow_html=True)
    for _, row in rows.iterrows():
        st.markdown(f"""
<div class="simple-list-item">
  <div><b>{row.get('title','')}</b></div>
  <div class="muted">{row.get('message','')}</div>
</div>
""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def stage2_count_by_industry(combined_df: pd.DataFrame) -> pd.DataFrame:
    if combined_df.empty or "Industry" not in combined_df.columns or "stage" not in combined_df.columns:
        return pd.DataFrame(columns=["Industry", "Stage 2 Stocks"])
    return combined_df.groupby("Industry", dropna=True)["stage"].apply(lambda s: int((s == "Stage 2").sum())).reset_index(name="Stage 2 Stocks")

# defaults
outdir = "outputs"
help_image_path = "market_phases_reference.png"

combined = ensure_label(safe_read(f"{outdir}/vcp_combined_ranked.csv"))
industry = ensure_label(safe_read(f"{outdir}/industry_strength.csv"))
changes = ensure_label(safe_read(f"{outdir}/stock_changes.csv"))
industry_changes = ensure_label(safe_read(f"{outdir}/industry_changes.csv"))
moves = ensure_label(safe_read(f"{outdir}/stock_price_moves.csv"))
regime = safe_read(f"{outdir}/market_regime.csv")

if combined.empty:
    st.error("No data found in the default outputs folder.")
    st.info("Create an outputs folder beside this file and keep the generated CSV files there.")
    st.stop()

daily_dir = f"{outdir}/charts/daily"
weekly_dir = f"{outdir}/charts/weekly"
company_map = company_choices(combined)

st.title("Market Structure Radar")
tabs = st.tabs(["Home","Stocks","Movers","Market","Learn","Portfolio","Advanced","Disclaimer"])

with tabs[0]:
    c1, c2, c3 = st.columns(3)
    with c1:
        render_summary_card("Market tone", market_tone(regime, combined), "Simple summary of the latest saved scan")
    with c2:
        render_summary_card("Top industries", top_industry_text(industry), "Industries leading the current scan")
    with c3:
        render_summary_card("Setups", str(int((combined["label"] == "Strong").sum())), "Stocks currently in the top classification")
    st.divider()
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("### Top stocks today")
        for _, r in combined.sort_values("final_combined_score", ascending=False).head(5).iterrows():
            card(r, use_stage_color=True)
    with right:
        st.markdown("### What changed today")
        items = []
        if not changes.empty:
            if "new_top_10" in changes.columns:
                items.append({"title": f"{int(changes['new_top_10'].fillna(False).sum())} names entered Top 10", "message": "These names moved into the top-ranked group in the latest saved run."})
            if "new_daily_breakout" in changes.columns:
                items.append({"title": f"{int(changes['new_daily_breakout'].fillna(False).sum())} new daily breakout conditions", "message": "These names newly met the daily breakout rule in the latest run."})
            if "entered_stage_2" in changes.columns:
                items.append({"title": f"{int(changes['entered_stage_2'].fillna(False).sum())} names entered Stage 2", "message": "These names moved into the uptrend phase in the latest run."})
        if not items:
            items = [{"title": "No major changes found", "message": "The latest saved run did not show large classification changes."}]
        render_simple_list(pd.DataFrame(items))
    render_disclosure()

with tabs[1]:
    ranked = combined.sort_values("final_combined_score", ascending=False).reset_index(drop=True).copy()
    names = ranked["Company Name"].dropna().astype(str).tolist()
    if "selected_stock_index" not in st.session_state:
        st.session_state["selected_stock_index"] = 0
    st.session_state["selected_stock_index"] = max(0, min(st.session_state["selected_stock_index"], len(names)-1))
    selected_name = st.selectbox("Select stock", names, index=st.session_state["selected_stock_index"], key="stocks_select_name_ordered")
    selected_index = names.index(selected_name)
    if selected_index != st.session_state["selected_stock_index"]:
        st.session_state["selected_stock_index"] = selected_index
    row = ranked.iloc[st.session_state["selected_stock_index"]]

    st.markdown("#### Selected stock")
    card(row, use_stage_color=True)

    st.markdown("#### Selected charts")
    dpath = resolve_chart_path(daily_dir, row["ticker"], "_daily.png")
    wpath = resolve_chart_path(weekly_dir, row["ticker"], "_weekly.png")
    a, b = st.columns(2)
    with a:
        st.markdown("##### Daily")
        if dpath: st.image(safe_image_bytes(dpath), use_container_width=True)
        else: st.info("Daily chart not available.")
    with b:
        st.markdown("##### Weekly")
        if wpath: st.image(safe_image_bytes(wpath), use_container_width=True)
        else: st.info("Weekly chart not available.")

    nav1, nav2 = st.columns(2)
    with nav1:
        prev_clicked = st.button("Previous", use_container_width=True, disabled=(st.session_state["selected_stock_index"] == 0), key="stocks_prev_btn")
    with nav2:
        next_clicked = st.button("Next", use_container_width=True, disabled=(st.session_state["selected_stock_index"] >= len(names) - 1), key="stocks_next_btn")

    if prev_clicked and st.session_state["selected_stock_index"] > 0:
        st.session_state["selected_stock_index"] -= 1
        st.rerun()
    if next_clicked and st.session_state["selected_stock_index"] < len(names) - 1:
        st.session_state["selected_stock_index"] += 1
        st.rerun()

    st.divider()
    st.markdown("### Browse more stocks")
    for _, r in ranked.head(20).iterrows():
        card(r, use_stage_color=True)
    render_disclosure()

with tabs[2]:
    st.markdown("### Movers")
    if moves.empty:
        st.info("Price move data not found yet.")
    else:
        window_map = {"1 Day":"change_1d_pct","1 Week":"change_1w_pct","1 Month":"change_1m_pct","YTD":"change_ytd_pct"}
        selected = st.radio("Move window", list(window_map.keys()), horizontal=True, index=0)
        col = window_map[selected]
        mv = moves.copy()
        mv[col] = pd.to_numeric(mv[col], errors="coerce")
        mv = mv.dropna(subset=[col])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### Fastest upward moves • {selected}")
            for _, r in mv.sort_values([col, "final_combined_score"], ascending=[False, False]).head(10).iterrows():
                card(r, pct=float(r[col]), highlight="up", use_stage_color=True)
        with c2:
            st.markdown(f"#### Fastest downward moves • {selected}")
            for _, r in mv.sort_values([col, "final_combined_score"], ascending=[True, False]).head(10).iterrows():
                card(r, pct=float(r[col]), highlight="down", use_stage_color=True)
    render_disclosure()

with tabs[3]:
    st.markdown("### Market")
    if industry.empty:
        st.info("Industry data not available.")
    else:
        view = industry.copy()
        stage2 = stage2_count_by_industry(combined)
        if "Industry" in view.columns:
            view = view.merge(stage2, on="Industry", how="left")
        sort_col = None
        for candidate in ["avg_combined_score","current_rank","rs_rank"]:
            if candidate in view.columns:
                sort_col = candidate
                break
        if sort_col is not None:
            view[sort_col] = pd.to_numeric(view[sort_col], errors="coerce")
            view = view.sort_values(sort_col, ascending=(sort_col!="avg_combined_score"), na_position="last").reset_index(drop=True)
            view["Rank"] = range(1, len(view)+1)
        if "Stage 2 Stocks" in view.columns:
            view["Stage 2 Stocks"] = view["Stage 2 Stocks"].fillna(0).astype(int)
        left, right = st.columns(2)
        with left:
            st.markdown("#### Industry strength")
            st.dataframe(view[[c for c in ["Industry","Rank","Stage 2 Stocks"] if c in view.columns]], use_container_width=True, hide_index=True, height=520)
        with right:
            st.markdown("#### Industry changes")
            if industry_changes.empty:
                st.info("Industry changes data not available.")
            else:
                cols = [c for c in ["Industry","current_rank","prev_rank","rank_change"] if c in industry_changes.columns]
                renamed = industry_changes[cols].rename(columns={"current_rank":"Current Rank","prev_rank":"Previous Rank","rank_change":"Rank Change"})
                st.dataframe(renamed, use_container_width=True, hide_index=True, height=520)
    render_disclosure()

with tabs[4]:
    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown("""
<div class="learn-card">
  <div class="stock-title">What this site is trying to show</div>
  <ul class="list-tight">
    <li>Which stocks currently look technically stronger or weaker inside this model.</li>
    <li>Which industries are improving or weakening relative to others.</li>
    <li>How daily and weekly structure compare for the same stock.</li>
  </ul>
</div>
<div class="learn-card">
  <div class="stock-title">Simple labels</div>
  <ul class="list-tight">
    <li><b>Strong</b>: the model sees stronger structure right now.</li>
    <li><b>Developing</b>: the model sees mixed or still-building structure.</li>
    <li><b>Weak</b>: the model sees weaker structure right now.</li>
  </ul>
</div>
""", unsafe_allow_html=True)
    with right:
        img = Path(help_image_path)
        if img.exists():
            st.image(str(img), caption="Reference image for the four market phases", use_container_width=True)
        else:
            st.info("Stage image not found.")
    render_disclosure()

with tabs[5]:
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
    else:
        current = combined[combined["Company Name"].isin(st.session_state["portfolio_names"])].copy()
        c1, c2, c3 = st.columns(3)
        with c1: render_summary_card("Total stocks", str(len(current)), "Stocks currently added")
        with c2: render_summary_card("Strong", str(int((current["label"] == "Strong").sum())), "Current Strong classifications")
        with c3: render_summary_card("Developing", str(int((current["label"] == "Developing").sum())), "Current Developing classifications")
        st.divider()
        for _, r in current.sort_values("final_combined_score", ascending=False).iterrows():
            card(r, use_stage_color=True)
        removable = [""] + sorted(st.session_state["portfolio_names"])
        selected_remove = st.selectbox("Remove stock", removable, key="portfolio_remove_name")
        if st.button("Remove from portfolio", use_container_width=True, key="portfolio_remove_btn") and selected_remove:
            st.session_state["portfolio_names"] = [x for x in st.session_state["portfolio_names"] if x != selected_remove]
            st.rerun()
    render_disclosure()

with tabs[6]:
    def keep_simple(df: pd.DataFrame) -> pd.DataFrame:
        wanted = [c for c in ["Company Name","ticker","label","classification","stage","Industry"] if c in df.columns]
        out = df[wanted].copy() if wanted else df.copy()
        if "classification" in out.columns and "label" not in out.columns:
            out["label"] = out["classification"]
            out = out.drop(columns=["classification"])
        if "ticker" in out.columns:
            out = out.rename(columns={"ticker":"Ticker","label":"Classification"})
            out["Ticker"] = out["Ticker"].astype(str).str.replace(".NS","", regex=False)
        else:
            out = out.rename(columns={"label":"Classification"})
        return out
    st.markdown("### Advanced")
    with st.expander("Overall ranked", expanded=True):
        st.dataframe(keep_simple(combined), use_container_width=True, hide_index=True, height=360)
    with st.expander("Daily ranked", expanded=False):
        st.dataframe(keep_simple(ensure_label(safe_read(f"{outdir}/vcp_daily_ranked.csv"))), use_container_width=True, hide_index=True, height=320)
    with st.expander("Weekly ranked", expanded=False):
        st.dataframe(keep_simple(ensure_label(safe_read(f"{outdir}/vcp_weekly_ranked.csv"))), use_container_width=True, hide_index=True, height=320)
    with st.expander("Stock changes", expanded=False):
        st.dataframe(keep_simple(changes), use_container_width=True, hide_index=True, height=320)
    with st.expander("Industry changes", expanded=False):
        cols = [c for c in ["Industry","current_rank","prev_rank","rank_change"] if c in industry_changes.columns]
        st.dataframe(industry_changes[cols].rename(columns={"current_rank":"Current Rank","prev_rank":"Previous Rank","rank_change":"Rank Change"}), use_container_width=True, hide_index=True, height=320)
    render_disclosure()

with tabs[7]:
    st.markdown("### Disclaimer")
    st.write("This tool is for informational purposes only. It presents rule-based classifications and market summaries. It does not provide personalized investment advice, suitability analysis, buy calls, sell calls, or allocation recommendations.")
    render_disclosure()
