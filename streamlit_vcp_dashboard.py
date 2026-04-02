import streamlit as st
import pandas as pd
from pathlib import Path
import math

st.set_page_config(page_title="Market Structure Radar", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root {
  --card-border: rgba(128,128,128,0.16);
  --muted: rgba(255,255,255,0.72);
  --strong: #1ec977;
  --developing: #f0b429;
  --weak: #ff6b6b;
  --cautious: #ff9f43;
  --up: #1ec977;
  --down: #ff6b6b;
  --stage1-bg: rgba(55,95,220,0.14);
  --stage2-bg: rgba(0,179,179,0.12);
  --stage3-bg: rgba(212,160,23,0.12);
  --stage4-bg: rgba(170,80,180,0.14);
  --stage1-border: rgba(55,95,220,0.34);
  --stage2-border: rgba(0,179,179,0.28);
  --stage3-border: rgba(212,160,23,0.28);
  --stage4-border: rgba(170,80,180,0.34);
}
.block-container {padding-top: 0.45rem; padding-bottom: 1.2rem; padding-left: 0.7rem; padding-right: 0.7rem; max-width: 1400px;}
.stTabs [data-baseweb="tab"] {font-size: 1.05rem; font-weight: 700;}
.stTabs [data-baseweb="tab-list"] {gap: 0.55rem; margin-top: 0.1rem;}
.hero-card, .stock-card, .learn-card {
  border: 2px solid var(--card-border);
  border-radius: 16px;
  padding: 0.8rem 0.9rem;
}
.hero-card {padding: 0.95rem 1rem; background: rgba(255,255,255,0.03);}
.kicker {font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted);}
.big-number {font-size: 1.34rem; font-weight: 800; margin-top: 0.08rem; margin-bottom: 0.1rem;}
.muted {color: var(--muted);}
.status-pill {display:inline-block; font-size:0.74rem; font-weight:700; padding:0.18rem 0.5rem; border-radius:999px; white-space:nowrap;}
.status-strong {background: rgba(30,201,119,0.14); color: var(--strong); border:1px solid rgba(30,201,119,0.35);}
.status-developing {background: rgba(240,180,41,0.14); color: var(--developing); border:1px solid rgba(240,180,41,0.35);}
.status-weak {background: rgba(255,107,107,0.14); color: var(--weak); border:1px solid rgba(255,107,107,0.35);}
.status-cautious {background: rgba(255,159,67,0.14); color: var(--cautious); border:1px solid rgba(255,159,67,0.35);}
.assist-box {border:1px solid var(--card-border); border-radius:16px; padding:0.85rem 0.95rem; background:rgba(255,255,255,0.03); margin-bottom:0.55rem;}
.assist-title {font-size:1rem; font-weight:800; margin-bottom:0.28rem;}
.assist-text {font-size:0.92rem; color: var(--muted); line-height:1.35;}
.stock-title {font-size: 1.02rem; font-weight: 700; margin-bottom: 0.06rem; line-height: 1.2;}
.meta-line {font-size: 0.93rem; font-weight: 600; line-height: 1.18; margin-top: 0.06rem; margin-bottom: 0.02rem;}
.stock-card {margin-bottom: 0.42rem; background: rgba(255,255,255,0.03); padding-top: 0.72rem; padding-bottom: 0.72rem;}
.stage-card-1 {background: var(--stage1-bg); border-color: var(--stage1-border);}
.stage-card-2 {background: var(--stage2-bg); border-color: var(--stage2-border);}
.stage-card-3 {background: var(--stage3-bg); border-color: var(--stage3-border);}
.stage-card-4 {background: var(--stage4-bg); border-color: var(--stage4-border);}
.change-badge-up {font-size: 1.12rem; font-weight: 900; margin-top: 0.1rem; color: var(--up);}
.change-badge-down {font-size: 1.12rem; font-weight: 900; margin-top: 0.1rem; color: var(--down);}
.rank-text {font-size: 0.84rem; font-weight: 700; color: var(--muted); margin-top: 0.18rem;}
.disclosure {border-left: 4px solid rgba(240,180,41,0.55); background: rgba(240,180,41,0.08); border-radius: 12px; padding: 0.7rem 0.85rem; font-size: 0.86rem; margin-bottom: 0.7rem; margin-top: 1rem;}
.list-tight {margin: 0.2rem 0 0 1rem; padding: 0;}
.change-text {font-size: 0.88rem; margin-top: 0.06rem; line-height: 1.18;}
.sidebar-nav-title {font-size: 0.95rem; font-weight: 800; margin-bottom: 0.4rem;}
@media (max-width: 768px) {
  [data-testid="stSidebar"] {display:none;}
  .block-container {padding-top: 0.35rem; padding-left: 0.35rem; padding-right: 0.35rem;}
}
</style>
""", unsafe_allow_html=True)

LABELS = {
    "Strong": {"css": "status-strong"},
    "Developing": {"css": "status-developing"},
    "Weak": {"css": "status-weak"},
    "Cautious": {"css": "status-cautious"},
}

MAX_PORTFOLIO_STOCKS = 25
PAGE_OPTIONS = ["Home", "Stocks", "Movers", "Market", "How to Use", "Portfolio", "Alerts", "Advanced", "Disclaimer"]

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
    rs3 = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs6 = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")

    if stage == "Stage 2":
        return "Strong"
    if stage == "Stage 1":
        if pd.notna(rs3) and pd.notna(rs6) and rs3 < 0 and rs6 < 0:
            return "Cautious"
        return "Developing"
    if stage == "Stage 3":
        return "Cautious"
    if stage == "Stage 4":
        return "Weak"
    if pd.notna(rs3) and pd.notna(rs6) and rs3 < 0 and rs6 < 0:
        return "Weak"
    return "Developing"

def ensure_label(df: pd.DataFrame) -> pd.DataFrame:
    out = normalize_columns(df)
    numeric_cols = [
        "final_combined_score", "avg_combined_score", "current_rank", "prev_rank", "rank_change",
        "combined_score_change", "change_1d_pct", "change_1w_pct", "change_1m_pct", "change_ytd_pct", "rs_rank"
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
        "Stage 1": "Base/Repair",
        "Stage 2": "Advancing Trend",
        "Stage 3": "Topping/Transition",
        "Stage 4": "Declining Trend",
    }.get(stage, stage or "Unknown")

def trend_text(row: pd.Series) -> str:
    label = str(row.get("label", row.get("classification", "Developing")))
    if label == "Strong":
        return "Strong trend"
    if label == "Weak":
        return "Weak trend"
    if label == "Cautious":
        return "Cautious trend"
    return "Developing trend"

def one_line_explanation(row: pd.Series) -> str:
    label = str(row.get("label", row.get("classification", "Developing")))
    stage = str(row.get("stage", ""))
    industry = str(row.get("Industry", "its industry")).strip() or "its industry"
    rank = pd.to_numeric(row.get("current_rank"), errors="coerce")
    prev_rank = pd.to_numeric(row.get("prev_rank"), errors="coerce")
    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    rs3 = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs6 = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")

    if stage == "Stage 2" and label == "Strong":
        if pd.notna(rank_change) and rank_change > 0:
            return f"Advancing trend is intact and relative position improved by {int(rank_change)} places."
        if pd.notna(rank) and rank <= 10:
            return "This is a top-ranked Stage 2 leader in the current scan."
        if pd.notna(rs3) and rs3 > 0 and pd.notna(rs6) and rs6 > 0:
            return "Trend and medium-term relative strength are aligned on the upside."
        return "Structure is acting like a leadership candidate rather than a repair candidate."
    if stage == "Stage 1":
        if pd.notna(rs3) and rs3 < 0:
            return "The stock is still repairing after weakness, so the base needs more time."
        return "This looks like a base or repair zone, not a confirmed advancing trend yet."
    if label == "Developing" and stage == "Stage 2":
        return "Trend is positive, but conviction is still lower than the strongest Stage 2 leaders."
    if stage == "Stage 3" or label == "Cautious":
        if pd.notna(prev_rank) and pd.notna(rank) and rank > prev_rank:
            return "Structure is losing momentum and rank is slipping versus peers."
        return "This is a transition or distribution-type structure, so failed rallies are a risk here."
    if stage == "Stage 4":
        return "Declining structure remains dominant, so this is better treated as avoid-for-now."
    if pd.notna(rs3) and pd.notna(rs6) and rs3 < 0 and rs6 < 0:
        return f"Relative strength is weak across timeframes and lagging {industry} peers."
    return "Current structure is weak or incomplete, so it is not a priority candidate right now."

def guided_workflow_steps(market_label: str) -> list:
    first_step = {
        "Risk On": "Start with Stage 2 names and the strongest industries.",
        "Mixed": "Be selective and focus on top-ranked Stage 2 names or the tightest Stage 1 bases.",
        "Risk Off": "Use the dashboard mainly to track improving bases and avoid forcing Stage 2 labels.",
    }.get(market_label, "Start with the highest-ranked names and confirm on both timeframes.")
    return [
        f"Step 1: Read market tone first. Today the model reads: {market_label}. {first_step}",
        "Step 2: Treat Stage 1 as a base or repair zone, and treat Stage 2 as the primary leadership phase.",
        "Step 3: Prefer improving ranks, stronger industries, and daily-weekly alignment over isolated laggards.",
        "Step 4: Use Portfolio and Alerts views to monitor stage transitions over time.",
    ]

def portfolio_assistant(current: pd.DataFrame) -> list:
    if current.empty:
        return ["Portfolio is empty. Add stocks to see a structure summary."]
    total = len(current)
    stage2 = int((current["stage"] == "Stage 2").sum()) if "stage" in current.columns else 0
    weak = int((current["label"].isin(["Weak", "Cautious"])).sum()) if "label" in current.columns else 0
    stage4 = int((current["stage"] == "Stage 4").sum()) if "stage" in current.columns else 0
    msgs = []
    if stage2 >= max(3, math.ceil(total * 0.45)):
        msgs.append(f"{stage2} of {total} stocks are in Stage 2, so the basket has decent trend participation.")
    else:
        msgs.append(f"Only {stage2} of {total} stocks are in Stage 2, so leadership inside the basket is limited.")
    if weak >= max(2, math.ceil(total * 0.4)):
        msgs.append(f"{weak} names are in Weak or Cautious territory, so risk is concentrated in lagging names.")
    else:
        msgs.append("Weak and Cautious names are contained, so the basket is not heavily tilted to laggards.")
    if stage4 > 0:
        msgs.append(f"{stage4} names are already in Stage 4, so these deserve extra review first.")
    top_industries = current["Industry"].dropna().astype(str).value_counts().head(2).index.tolist() if "Industry" in current.columns else []
    if top_industries:
        msgs.append(f"The basket is most exposed to {', '.join(top_industries)}.")
    return msgs

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
    if "final_combined_score" in tmp.columns:
        tmp = tmp.sort_values(["final_combined_score", "Company Name"], ascending=[False, True])
    else:
        tmp = tmp.sort_values(["Company Name"])
    tmp = tmp.drop_duplicates(subset=["Company Name"], keep="first")
    return dict(zip(tmp["Company Name"], tmp["ticker"]))

def render_disclosure():
    st.markdown("""
<div class="disclosure">
This dashboard is an informational analytics tool. It shows rule-based stage classifications and market summaries. In this model, Stage 1 means a base or repair zone, not an actionable uptrend by itself. Stage 2 is the primary leadership phase. The tool does not provide personalized investment advice, suitability analysis, buy calls, sell calls, or allocation recommendations.
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

def _stage_card_class(stage_raw: str) -> str:
    return {
        "Stage 1": "stage-card-1",
        "Stage 2": "stage-card-2",
        "Stage 3": "stage-card-3",
        "Stage 4": "stage-card-4",
    }.get(stage_raw, "")

def auto_rank(df: pd.DataFrame, preferred_cols: list) -> str:
    if df.empty:
        return "n/a"
    work = df.copy()
    candidate_score_cols = [
        "final_combined_score", "avg_combined_score", "combined_score",
        "final_daily_score", "daily_score", "final_weekly_score", "weekly_score",
        "score"
    ]
    for score_col in candidate_score_cols:
        if score_col in work.columns:
            scores = pd.to_numeric(work[score_col], errors="coerce")
            if scores.notna().any():
                val = scores.rank(method="min", ascending=False).iloc[0]
                if pd.notna(val):
                    return str(int(val))
    return "n/a"

def rank_lookup(df: pd.DataFrame, ticker: str, preferred_cols: list) -> str:
    if df.empty:
        return "n/a"
    work = df.copy()
    ticker_col = None
    for cand in ["ticker", "Ticker", "symbol", "Symbol"]:
        if cand in work.columns:
            ticker_col = cand
            break
    if ticker_col is None:
        return auto_rank(work, preferred_cols)
    work[ticker_col] = work[ticker_col].astype(str).str.strip()
    ticker_norm = str(ticker).strip()
    match = work[work[ticker_col] == ticker_norm]
    if match.empty:
        match = work[work[ticker_col].str.replace(".NS", "", regex=False) == ticker_norm.replace(".NS", "")]
    if match.empty:
        return auto_rank(work, preferred_cols)
    row = match.iloc[0]
    search_cols = preferred_cols + [
        "current_rank", "rank", "rs_rank", "daily_rank", "weekly_rank",
        "final_rank", "combined_rank", "stock_rank"
    ]
    for col in search_cols:
        if col in match.columns:
            val = pd.to_numeric(row.get(col), errors="coerce")
            if pd.notna(val):
                return str(int(val))
    return auto_rank(match, preferred_cols)

def card(row: pd.Series, pct=None, use_stage_color=False, show_change_text: str = "", stock_rank: str = "n/a", show_quick_read: bool = False):
    label = row.get("label", row.get("classification", "Developing"))
    style = LABELS.get(label, LABELS["Developing"])
    company = row.get("Company Name", row.get("ticker", "Stock"))
    ticker = str(row.get("ticker", "")).replace(".NS", "")
    stage_raw = str(row.get("stage", "Unknown"))
    trend = trend_text(row)
    phase = stage_display(stage_raw)
    explanation = one_line_explanation(row)
    classes = []
    if use_stage_color:
        stage_cls = _stage_card_class(stage_raw)
        if stage_cls:
            classes.append(stage_cls)
    change_html = ""
    if pct is not None:
        cls = "change-badge-up" if pct > 0 else "change-badge-down"
        change_html = f"<div class='{cls}'>{pct:+.2f}%</div>"
    extra_change = f"<div class='change-text'>{show_change_text}</div>" if show_change_text else ""
    quick_read_html = f"<div class='change-text'><b>Quick read:</b> {explanation}</div>" if show_quick_read else ""
    class_attr = " ".join(classes)
    status_html = f"<div class='status-pill {style['css']}'>{label}</div>"
    rank_html = f"<div class='rank-text'>Rank {stock_rank}</div>"
    html = (
        f"<div class='stock-card {class_attr}'>"
        f"<div style='display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem;'>"
        f"<div style='min-width:0;'>"
        f"<div class='stock-title'>{company} ({ticker})</div>"
        f"<div class='meta-line'>{stage_raw} * {trend} * {phase}</div>"
        f"</div>"
        f"<div style='display:flex; flex-direction:column; align-items:flex-end; gap:0.05rem;'>"
        f"{status_html}{rank_html}{change_html}"
        f"</div>"
        f"</div>"
        f"<div class='stock-title'>{quick_read_html}</div>"
        f"{extra_change}"
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)

def stage_count_summary(combined_df: pd.DataFrame):
    counts = combined_df["stage"].value_counts() if "stage" in combined_df.columns else pd.Series(dtype=int)
    return {
        "Stage 1": int(counts.get("Stage 1", 0)),
        "Stage 2": int(counts.get("Stage 2", 0)),
        "Stage 3": int(counts.get("Stage 3", 0)),
        "Stage 4": int(counts.get("Stage 4", 0)),
    }

def stage2_count_by_industry(combined_df: pd.DataFrame) -> pd.DataFrame:
    if combined_df.empty or "Industry" not in combined_df.columns or "stage" not in combined_df.columns:
        return pd.DataFrame(columns=["Industry", "Stage 2 Stocks"])
    return combined_df.groupby("Industry", dropna=True)["stage"].apply(lambda s: int((s == "Stage 2").sum())).reset_index(name="Stage 2 Stocks")

def build_today_changes(changes_df: pd.DataFrame):
    summary = {"New Strong": 0, "Entered Stage 2": 0, "New Breakouts": 0}
    if changes_df.empty:
        return pd.DataFrame(), summary
    df = changes_df.copy()
    if "label" not in df.columns:
        df["label"] = df.apply(classify_stock, axis=1)
    if "entered_stage_2" in df.columns:
        summary["Entered Stage 2"] = int(df["entered_stage_2"].fillna(False).sum())
    if "new_daily_breakout" in df.columns:
        summary["New Breakouts"] += int(df["new_daily_breakout"].fillna(False).sum())
    if "new_weekly_breakout" in df.columns:
        summary["New Breakouts"] += int(df["new_weekly_breakout"].fillna(False).sum())

    df["change_priority_score"] = 0.0
    weights = {"new_top_10": 60, "new_top_20": 40, "entered_stage_2": 90, "new_daily_breakout": 70, "new_weekly_breakout": 80}
    for col, wt in weights.items():
        if col in df.columns:
            df["change_priority_score"] += df[col].fillna(False).astype(int) * wt
    if "rank_change" in df.columns:
        df["change_priority_score"] += pd.to_numeric(df["rank_change"], errors="coerce").clip(lower=0, upper=20).fillna(0) * 2
    if "combined_score_change" in df.columns:
        df["change_priority_score"] += pd.to_numeric(df["combined_score_change"], errors="coerce").clip(lower=0).fillna(0) * 3

    entered_strong = (df["label"] == "Strong") & (df["change_priority_score"] >= 60)
    summary["New Strong"] = int(entered_strong.sum())
    df["change_priority_score"] += entered_strong.astype(int) * 100

    def what_changed(row):
        parts = []
        if bool(row.get("entered_stage_2", False)):
            parts.append("Entered Stage 2")
        if bool(row.get("new_weekly_breakout", False)):
            parts.append("Weekly breakout")
        if bool(row.get("new_daily_breakout", False)):
            parts.append("Daily breakout")
        if bool(row.get("new_top_10", False)):
            parts.append("Entered Top 10")
        elif bool(row.get("new_top_20", False)):
            parts.append("Entered Top 20")
        rc = pd.to_numeric(row.get("rank_change"), errors="coerce")
        if pd.notna(rc) and rc > 0:
            parts.append(f"Rank improved by {int(rc)}")
        return ", ".join(parts[:3]) if parts else "Score improved"

    df["what_changed"] = df.apply(what_changed, axis=1)
    if "final_combined_score" in df.columns:
        top_changed = df.sort_values(["change_priority_score", "final_combined_score"], ascending=[False, False]).head(5).copy()
    else:
        top_changed = df.sort_values(["change_priority_score"], ascending=[False]).head(5).copy()
    return top_changed, summary

outdir = "outputs"
help_image_path = "market_phases_reference.png"

combined = ensure_label(safe_read(f"{outdir}/vcp_combined_ranked.csv"))
daily_df = ensure_label(safe_read(f"{outdir}/vcp_daily_ranked.csv"))
weekly_df = ensure_label(safe_read(f"{outdir}/vcp_weekly_ranked.csv"))
industry = ensure_label(safe_read(f"{outdir}/industry_strength.csv"))
changes = ensure_label(safe_read(f"{outdir}/stock_changes.csv"))
industry_changes = ensure_label(safe_read(f"{outdir}/industry_changes.csv"))
moves = ensure_label(safe_read(f"{outdir}/stock_price_moves.csv"))
top_movers = ensure_label(safe_read(f"{outdir}/top_movers.csv"))
if top_movers.empty:
    top_movers = moves.copy()
regime = safe_read(f"{outdir}/market_regime.csv")

if combined.empty:
    st.error("No data found in the default outputs folder.")
    st.info("Create an outputs folder beside this file and keep the generated CSV files there.")
    st.stop()

daily_dir = f"{outdir}/charts/daily"
weekly_dir = f"{outdir}/charts/weekly"
company_map = company_choices(combined)
top_changed_df, changes_summary = build_today_changes(changes)
changed_tickers = set(top_changed_df["ticker"].dropna().tolist()) if not top_changed_df.empty and "ticker" in top_changed_df.columns else set()
if "final_combined_score" in combined.columns:
    top_stocks_today = combined[~combined["ticker"].isin(changed_tickers)].sort_values("final_combined_score", ascending=False).head(5).copy()
else:
    top_stocks_today = combined[~combined["ticker"].isin(changed_tickers)].head(5).copy()

def build_alert_candidates(combined_df: pd.DataFrame, changes_df: pd.DataFrame) -> pd.DataFrame:
    if combined_df.empty:
        return pd.DataFrame()
    alerts = []
    changes_lookup = changes_df.copy() if not changes_df.empty else pd.DataFrame()
    if not changes_lookup.empty and "ticker" in changes_lookup.columns:
        changes_lookup["ticker"] = changes_lookup["ticker"].astype(str).str.strip()
        changes_lookup = changes_lookup.set_index("ticker", drop=False)
    for _, row in combined_df.iterrows():
        ticker = str(row.get("ticker", "")).strip()
        cr = changes_lookup.loc[ticker] if (not changes_lookup.empty and ticker in changes_lookup.index) else None
        alert_type = ""
        reason = ""
        if cr is not None and bool(cr.get("entered_stage_2", False)):
            alert_type = "Entered Stage 2"
            reason = "Trend moved into the uptrend phase."
        elif cr is not None and bool(cr.get("new_weekly_breakout", False)):
            alert_type = "Weekly breakout"
            reason = "Weekly structure triggered a fresh breakout event."
        elif cr is not None and bool(cr.get("new_daily_breakout", False)):
            alert_type = "Daily breakout"
            reason = "Daily structure triggered a fresh breakout event."
        else:
            rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
            if pd.notna(rank_change) and rank_change >= 5:
                alert_type = "Rank improvement"
                reason = f"Rank improved by {int(rank_change)} places."
        if alert_type:
            item = row.copy()
            item["alert_type"] = alert_type
            item["alert_reason"] = reason
            alerts.append(item)
    if not alerts:
        return pd.DataFrame()
    out = pd.DataFrame(alerts)
    if "final_combined_score" in out.columns:
        out = out.sort_values(["final_combined_score", "alert_type"], ascending=[False, True])
    return out.head(20)

alert_candidates = build_alert_candidates(combined, changes)
stage_counts = stage_count_summary(combined)

def dedupe_names(names: list, limit: int = MAX_PORTFOLIO_STOCKS) -> list:
    out = []
    seen = set()
    for name in names:
        if pd.isna(name):
            continue
        name = str(name).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
        if len(out) >= limit:
            break
    return out

def get_stock_rank(ticker: str) -> str:
    return rank_lookup(combined, ticker, ["current_rank"])

def get_display_stock_rank(ticker: str) -> str:
    return get_stock_rank(ticker)

def get_industry_portfolio_options(industry_df: pd.DataFrame, combined_df: pd.DataFrame, limit: int = 21) -> list:
    if not industry_df.empty and "Industry" in industry_df.columns:
        view = industry_df.copy()
        sort_col = None
        ascending = False
        for candidate in ["avg_combined_score", "final_combined_score"]:
            if candidate in view.columns:
                sort_col = candidate
                ascending = False
                break
        if sort_col is None:
            for candidate in ["current_rank", "rs_rank"]:
                if candidate in view.columns:
                    sort_col = candidate
                    ascending = True
                    break
        if sort_col is not None:
            view[sort_col] = pd.to_numeric(view[sort_col], errors="coerce")
            view = view.sort_values(sort_col, ascending=ascending, na_position="last")
        industries = view["Industry"].dropna().astype(str).str.strip().tolist()
        return dedupe_names(industries, limit=limit)
    if "Industry" not in combined_df.columns:
        return []
    grouped = (combined_df.dropna(subset=["Industry"]).groupby("Industry", as_index=False)["final_combined_score"].mean().sort_values("final_combined_score", ascending=False))
    industries = grouped["Industry"].astype(str).str.strip().tolist()
    return dedupe_names(industries, limit=limit)

INDUSTRY_PORTFOLIOS = get_industry_portfolio_options(industry, combined, limit=21)

def get_prebuilt_portfolio(name: str, combined: pd.DataFrame, changes: pd.DataFrame) -> list:
    ranked = combined.sort_values("final_combined_score", ascending=False) if "final_combined_score" in combined.columns else combined.copy()
    names = []
    if name == "Top 15":
        names = ranked.head(15)["Company Name"].dropna().tolist()
    elif name == "New Breakouts":
        tmp = changes.copy()
        mask = pd.Series(False, index=tmp.index)
        if "new_daily_breakout" in tmp.columns:
            mask = mask | tmp["new_daily_breakout"].fillna(False)
        if "new_weekly_breakout" in tmp.columns:
            mask = mask | tmp["new_weekly_breakout"].fillna(False)
        names = tmp.loc[mask, "Company Name"].dropna().tolist()
    elif name == "New Strong":
        tmp = changes.copy()
        if "label" not in tmp.columns:
            tmp["label"] = tmp.apply(classify_stock, axis=1)
        names = tmp.loc[tmp["label"] == "Strong", "Company Name"].dropna().tolist()
    elif name in {"Stage 1", "Stage 2", "Stage 3", "Stage 4"}:
        names = combined.loc[combined["stage"] == name, "Company Name"].dropna().tolist()
    elif name == "Cautious":
        names = combined.loc[combined["label"] == "Cautious", "Company Name"].dropna().tolist()
    elif name == "Weak":
        names = combined.loc[combined["label"] == "Weak", "Company Name"].dropna().tolist()
    elif name == "Strong":
        names = combined.loc[combined["label"] == "Strong", "Company Name"].dropna().tolist()
    elif name in INDUSTRY_PORTFOLIOS:
        names = ranked.loc[ranked["Industry"].astype(str).str.strip() == name, "Company Name"].dropna().tolist()
    return dedupe_names(names, limit=MAX_PORTFOLIO_STOCKS)

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

with st.sidebar:
    st.markdown('<div class="sidebar-nav-title">Navigation</div>', unsafe_allow_html=True)
    page = st.radio("", PAGE_OPTIONS, index=PAGE_OPTIONS.index(st.session_state["page"]))
    st.session_state["page"] = page
    st.divider()
    view_mode = st.radio("View mode", ["Beginner", "Pro"], horizontal=False, index=0)
    st.caption("Sidebar stays visible on larger screens and hides on phone-sized screens.")

page = st.session_state["page"]
show_pro_quick_read = view_mode == "Pro"

st.title("Market Structure Radar")
st.caption("Pro mode adds a quick-read summary on stock cards. Stage 1 is treated as a base/watchlist phase, while Stage 2 is treated as the main leadership phase.")

# Due to size, copy the remaining page sections from the earlier message or ask for a split file if needed.
# This canvas contains the corrected architecture, sidebar navigation, and all helper functions.
# Use the prior full page blocks for Home/Stocks/Movers/Market/How to Use/Portfolio/Alerts/Advanced/Disclaimer.
