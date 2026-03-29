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
  --card-border: rgba(128,128,128,0.18);
  --muted: rgba(255,255,255,0.72);
  --ready: #1ec977;
  --watch: #f0b429;
  --avoid: #ff6b6b;
  --neutral: #77a8ff;
}
.block-container {padding-top: 0.7rem; padding-bottom: 1.6rem; padding-left: 0.7rem; padding-right: 0.7rem; max-width: 1420px;}
[data-testid="stMetric"] {background: var(--card-bg); border: 1px solid var(--card-border); padding: 0.5rem 0.65rem; border-radius: 0.85rem;}
[data-testid="stMetricLabel"] {font-size: 0.8rem;}
[data-testid="stMetricValue"] {font-size: 1.18rem;}
.stImage img {border-radius: 0.9rem; border: 1px solid rgba(255,255,255,0.08);}
.element-container, .stDataFrame, .stImage {margin-bottom: 0.5rem;}
pre {white-space: pre-wrap !important; word-break: break-word !important;}
.hero-card, .summary-card, .status-card, .insight-card, .stock-card, .guide-card, .mini-card, .filter-card, .learn-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 18px;
  padding: 0.85rem 0.95rem;
}
.hero-card {padding: 1rem 1rem;}
.summary-card {min-height: 110px;}
.stock-card {margin-bottom: 0.7rem;}
.muted {color: var(--muted);}
.kicker {font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted);}
.stock-title {font-size: 1.03rem; font-weight: 700; margin-bottom: 0.12rem;}
.stock-subtitle {font-size: 0.82rem; color: var(--muted); margin-bottom: 0.5rem;}
.row-wrap {display:flex; flex-wrap:wrap; gap:0.38rem; margin-top:0.35rem;}
.chip {
  display:inline-block;
  border: 1px solid var(--card-border);
  background: rgba(255,255,255,0.04);
  padding: 0.18rem 0.48rem;
  border-radius: 999px;
  font-size: 0.74rem;
}
.ready-chip {border-color: rgba(30,201,119,0.35); color: var(--ready);}
.watch-chip {border-color: rgba(240,180,41,0.35); color: var(--watch);}
.avoid-chip {border-color: rgba(255,107,107,0.35); color: var(--avoid);}
.neutral-chip {border-color: rgba(119,168,255,0.35); color: var(--neutral);}
.status-banner {
  display:inline-block;
  font-size:0.76rem;
  font-weight:700;
  padding:0.2rem 0.55rem;
  border-radius:999px;
  margin-bottom:0.45rem;
}
.status-ready {background: rgba(30,201,119,0.14); color: var(--ready); border:1px solid rgba(30,201,119,0.35);}
.status-watch {background: rgba(240,180,41,0.14); color: var(--watch); border:1px solid rgba(240,180,41,0.35);}
.status-avoid {background: rgba(255,107,107,0.14); color: var(--avoid); border:1px solid rgba(255,107,107,0.35);}
.status-neutral {background: rgba(119,168,255,0.14); color: var(--neutral); border:1px solid rgba(119,168,255,0.35);}
.big-number {font-size: 1.45rem; font-weight: 800; margin-top: 0.12rem; margin-bottom: 0.15rem;}
.list-tight {margin: 0.2rem 0 0 1rem; padding: 0;}
.list-tight li {margin: 0.18rem 0;}
.stock-grid-note {font-size: 0.78rem; color: var(--muted); margin-bottom: 0.5rem;}
.change-up {color: var(--ready); font-weight: 700;}
.change-down {color: var(--avoid); font-weight: 700;}
.change-flat {color: var(--watch); font-weight: 700;}
.disclosure {
  border-left: 4px solid rgba(240,180,41,0.55);
  background: rgba(240,180,41,0.08);
  border-radius: 12px;
  padding: 0.8rem 0.9rem;
  font-size: 0.88rem;
}
.small-label {font-size: 0.76rem; color: var(--muted);}
.section-title {font-size: 1.05rem; font-weight: 700; margin-bottom: 0.55rem;}
.mover-card {
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  border-radius: 14px;
  padding: 0.7rem 0.8rem;
  margin-bottom: 0.55rem;
}
.mover-top {border-left: 4px solid rgba(30,201,119,0.85);}
.mover-bottom {border-left: 4px solid rgba(255,107,107,0.85);}
.mover-head {display:flex; justify-content:space-between; gap:0.5rem; align-items:flex-start;}
.mover-ticker {font-weight:700; font-size:0.98rem;}
.mover-company {font-size:0.84rem; opacity:0.88; margin-top:0.12rem;}
.mover-chip-wrap {display:flex; flex-wrap:wrap; gap:0.35rem; margin-top:0.5rem;}
.mover-chip {
  font-size:0.72rem;
  padding:0.18rem 0.45rem;
  border-radius:999px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(128,128,128,0.18);
}
.mover-change-up {font-weight:800; color:var(--ready);}
.mover-change-down {font-weight:800; color:var(--avoid);}
.learn-card {margin-bottom: 0.6rem;}
.learn-title {font-size: 0.92rem; font-weight: 700; margin-bottom: 0.3rem;}
@media (max-width: 768px) {
  .block-container {padding-top: 0.45rem; padding-left: 0.35rem; padding-right: 0.35rem;}
  h1 {font-size: 1.4rem !important;}
  h2 {font-size: 1.12rem !important;}
  h3 {font-size: 0.98rem !important;}
  [data-testid="stMetric"] {padding: 0.35rem 0.5rem;}
  [data-testid="stMetricValue"] {font-size: 1rem;}
  .hero-card, .summary-card, .status-card, .insight-card, .stock-card, .guide-card, .mini-card, .learn-card {padding: 0.75rem 0.75rem;}
  .stock-title {font-size: 0.95rem;}
  .big-number {font-size: 1.15rem;}
}
</style>
""",
    unsafe_allow_html=True,
)

BEGINNER_LABELS = {
    "ready": {
        "title": "Ready",
        "subtitle": "Stronger technical structure in the current scan",
        "css": "status-ready",
        "chip": "ready-chip",
        "explain": "The current rule-based inputs show comparatively stronger structure, momentum, and broader context.",
        "classification": "This stock is currently placed in the stronger setup bucket by the model.",
    },
    "watch": {
        "title": "Watch",
        "subtitle": "Developing structure with mixed alignment",
        "css": "status-watch",
        "chip": "watch-chip",
        "explain": "The current rule-based inputs show some constructive features, but alignment is still mixed or incomplete.",
        "classification": "This stock is currently placed in the developing setup bucket by the model.",
    },
    "avoid": {
        "title": "Lower strength",
        "subtitle": "Weaker technical structure in the current scan",
        "css": "status-avoid",
        "chip": "avoid-chip",
        "explain": "The current rule-based inputs show weaker or less aligned technical structure.",
        "classification": "This stock is currently placed in the lower-strength bucket by the model.",
    },
    "neutral": {
        "title": "Mixed",
        "subtitle": "Signals are mixed or limited",
        "css": "status-neutral",
        "chip": "neutral-chip",
        "explain": "The current rule-based inputs do not create a strong classification either way.",
        "classification": "This stock is currently placed in a mixed bucket by the model.",
    },
}

DAILY_LABEL_MAP = {
    "breakout_today": "Daily breakout condition",
    "near_pivot": "Daily near-pivot condition",
    "forming_vcp": "Daily structure building",
    "watchlist": "Daily watchlist condition",
}
WEEKLY_LABEL_MAP = {
    "weekly_breakout": "Weekly breakout condition",
    "weekly_near_pivot": "Weekly near-pivot condition",
    "weekly_forming": "Weekly structure building",
    "weekly_watchlist": "Weekly watchlist condition",
}
COMBINED_LABEL_MAP = {
    "high_conviction_breakout": "Stronger daily and weekly alignment",
    "high_conviction_near_pivot": "Stronger near-pivot alignment",
    "building_setup": "Structure still building",
    "watchlist": "Watchlist condition",
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

def get_last_updated(file_path: str) -> str:
    p = Path(file_path)
    if not p.exists():
        return "Not available"
    ts = pd.Timestamp(p.stat().st_mtime, unit="s").tz_localize("UTC").tz_convert("Asia/Kolkata")
    return ts.strftime("%d %b %Y, %I:%M %p IST")

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

def add_safe_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = normalize_columns(df)
    if "daily_setup_bucket" in out.columns:
        out["daily_setup_label"] = out["daily_setup_bucket"].map(DAILY_LABEL_MAP).fillna(out["daily_setup_bucket"])
    if "weekly_setup_bucket" in out.columns:
        out["weekly_setup_label"] = out["weekly_setup_bucket"].map(WEEKLY_LABEL_MAP).fillna(out["weekly_setup_bucket"])
    if "combined_bucket" in out.columns:
        out["overall_setup_label"] = out["combined_bucket"].map(COMBINED_LABEL_MAP).fillna(out["combined_bucket"])
    numeric_cols = [
        "daily_score", "weekly_score", "combined_score", "final_daily_score", "final_weekly_score",
        "final_combined_score", "rs_3m_pct", "rs_6m_pct", "industry_boost", "combined_score_change",
        "daily_score_change", "weekly_score_change", "rank_change", "rs_rank", "avg_combined_score",
        "strong_combined_change", "actionable_daily_change", "actionable_weekly_change", "current_rank", "prev_rank",
        "change_1d_pct", "change_1w_pct", "change_1m_pct", "change_ytd_pct"
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(2)
    if "avg_turnover_inr" in out.columns:
        out = out.drop(columns=["avg_turnover_inr"])
    return out

def pretty_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "ticker": "Ticker",
        "Company Name": "Company",
        "Industry": "Industry",
        "stage": "Stage",
        "overall_setup_label": "Overall Label",
        "daily_setup_label": "Daily Label",
        "weekly_setup_label": "Weekly Label",
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
        "strong_combined_change": "Strong Setups Change",
        "actionable_daily": "Daily Breadth",
        "actionable_weekly": "Weekly Breadth",
        "actionable_daily_change": "Daily Breadth Change",
        "actionable_weekly_change": "Weekly Breadth Change",
        "new_top_10": "New Top 10",
        "new_top_20": "New Top 20",
        "current_rank": "Current Rank",
        "prev_rank": "Previous Rank",
        "new_cluster": "New Cluster",
        "change_1d_pct": "1D Change %",
        "change_1w_pct": "1W Change %",
        "change_1m_pct": "1M Change %",
        "change_ytd_pct": "YTD Change %",
    }
    return df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

def compact_metric_grid(items: List[Tuple[str, object]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.metric(label, value)

def format_num(x) -> str:
    if pd.isna(pd.to_numeric(x, errors="coerce")):
        return "n/a"
    return f"{float(x):.1f}"

def get_beginner_status(row: pd.Series) -> Dict[str, str]:
    stage = str(row.get("stage", ""))
    bucket = str(row.get("combined_bucket", ""))
    final_score = pd.to_numeric(row.get("final_combined_score", row.get("combined_score")), errors="coerce")
    rs_3m = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs_6m = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")

    if stage == "Stage 2" and bucket in {"high_conviction_breakout", "high_conviction_near_pivot"} and pd.notna(final_score) and final_score >= 60:
        return BEGINNER_LABELS["ready"]
    if stage == "Stage 2" and pd.notna(final_score) and final_score >= 48:
        return BEGINNER_LABELS["watch"]
    if bucket == "building_setup" and pd.notna(final_score) and final_score >= 45:
        return BEGINNER_LABELS["watch"]
    if stage in {"Stage 3", "Stage 4"}:
        return BEGINNER_LABELS["avoid"]
    if pd.notna(rs_3m) and pd.notna(rs_6m) and rs_3m < 0 and rs_6m < 0:
        return BEGINNER_LABELS["avoid"]
    return BEGINNER_LABELS["neutral"]

def momentum_label(row: pd.Series) -> str:
    rs_3m = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs_6m = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")
    vals = [v for v in [rs_3m, rs_6m] if pd.notna(v)]
    if not vals:
        return "Momentum unclear"
    avg = sum(vals) / len(vals)
    if avg >= 15:
        return "Momentum strong"
    if avg >= 5:
        return "Momentum improving"
    if avg >= -5:
        return "Momentum mixed"
    return "Momentum weak"

def structure_label(row: pd.Series) -> str:
    bucket = str(row.get("combined_bucket", ""))
    mapping = {
        "high_conviction_breakout": "Breakout-style structure",
        "high_conviction_near_pivot": "Near-pivot structure",
        "building_setup": "Structure still building",
        "watchlist": "No stronger structure yet",
    }
    return mapping.get(bucket, "Structure mixed")

def stage_label(row: pd.Series) -> str:
    stage = str(row.get("stage", "Unknown"))
    mapping = {
        "Stage 1": "Accumulation / recovery phase",
        "Stage 2": "Uptrend / markup phase",
        "Stage 3": "Distribution phase",
        "Stage 4": "Downtrend / markdown phase",
    }
    return mapping.get(stage, stage)

def stage_explanation(stage: str) -> str:
    mapping = {
        "Stage 1": "Price is stabilizing after weakness or moving sideways while longer-term trend pressure reduces.",
        "Stage 2": "Price is showing stronger trend behaviour and sits in the strongest phase within this framework.",
        "Stage 3": "Price is losing trend quality and moving into a more unstable topping-style phase.",
        "Stage 4": "Price is in a weaker trend phase and sits below the strongest structural zone.",
    }
    return mapping.get(stage, "Stage description not available.")

def simple_explanation(row: pd.Series) -> List[str]:
    return [
        structure_label(row),
        momentum_label(row),
        stage_label(row),
    ]

def compliance_safe_interpretation(row: pd.Series) -> str:
    status = get_beginner_status(row)["title"]
    if status == "Ready":
        return "The model currently places this stock in the stronger setup bucket based on structure, momentum, and broader context."
    if status == "Watch":
        return "The model currently places this stock in the developing setup bucket because the signals are constructive but not fully aligned."
    if status == "Lower strength":
        return "The model currently places this stock in the lower-strength bucket because the current signals are weaker or less aligned."
    return "The model currently places this stock in a mixed bucket because the available signals do not create a stronger classification."

def change_flags(row: pd.Series) -> List[str]:
    flags = []
    if bool(row.get("new_daily_breakout", False)):
        flags.append("New daily breakout condition")
    if bool(row.get("new_weekly_breakout", False)):
        flags.append("New weekly breakout condition")
    if bool(row.get("entered_stage_2", False)):
        flags.append("Entered Stage 2")
    if bool(row.get("new_top_10", False)):
        flags.append("Entered Top 10")
    if bool(row.get("new_top_20", False)):
        flags.append("Entered Top 20")
    return flags

def market_summary_text(regime_df: pd.DataFrame, industry_df: pd.DataFrame, combined_df: pd.DataFrame) -> Tuple[str, str, str]:
    regime = regime_df.iloc[0]["regime_label"] if not regime_df.empty and "regime_label" in regime_df.columns else "n/a"
    regime_map = {
        "risk_on": "Market tone is constructive",
        "mixed": "Market tone is mixed",
        "risk_off": "Market tone is defensive",
    }
    regime_text = regime_map.get(regime, "Market tone unavailable")
    top_industries = ", ".join(industry_df.head(3)["Industry"].astype(str).tolist()) if not industry_df.empty and "Industry" in industry_df.columns else "Not available"
    ready_count = int(((combined_df["stage"] == "Stage 2") & (combined_df["final_combined_score"] >= 60)).sum()) if not combined_df.empty and "final_combined_score" in combined_df.columns else 0
    return regime_text, top_industries, f"{ready_count} names currently fall in the stronger setup bucket"

def render_disclosure() -> None:
    st.markdown(
        """
<div class="disclosure">
<b>Important:</b> This dashboard is an informational and educational analytics tool. It presents rule-based screening outputs, classifications, and summaries. It does not provide personalized investment advice, suitability assessment, target prices, buy calls, sell calls, or portfolio recommendations.
</div>
""",
        unsafe_allow_html=True,
    )

def render_summary_card(title: str, value: str, subtitle: str) -> None:
    st.markdown(
        f"""
<div class="summary-card">
  <div class="kicker">{title}</div>
  <div class="big-number">{value}</div>
  <div class="muted">{subtitle}</div>
</div>
""",
        unsafe_allow_html=True,
    )

def render_learn_card(title: str, body: str) -> None:
    st.markdown(
        f"""
<div class="learn-card">
  <div class="learn-title">{title}</div>
  <div>{body}</div>
</div>
""",
        unsafe_allow_html=True,
    )

def render_stock_card(row: pd.Series, beginner_mode: bool = True, show_change_flags: bool = False) -> None:
    status = get_beginner_status(row)
    ticker = str(row.get("ticker", "")).replace(".NS", "")
    company = str(row.get("Company Name", ticker))
    industry = str(row.get("Industry", "Unknown"))
    score = format_num(row.get("final_combined_score", row.get("combined_score")))
    daily = format_num(row.get("final_daily_score", row.get("daily_score")))
    weekly = format_num(row.get("final_weekly_score", row.get("weekly_score")))
    change_flags_list = change_flags(row) if show_change_flags else []
    explanation = simple_explanation(row)
    interpretation = compliance_safe_interpretation(row)
    overall = row.get("overall_setup_label", row.get("combined_bucket", "n/a"))
    rs3 = format_num(row.get("rs_3m_pct"))
    rs6 = format_num(row.get("rs_6m_pct"))

    chips = [
        f'<span class="chip {status["chip"]}">{status["title"]}</span>',
        f'<span class="chip neutral-chip">{industry}</span>',
        f'<span class="chip neutral-chip">{stage_label(row)}</span>',
    ]
    if not beginner_mode:
        chips.extend([
            f'<span class="chip neutral-chip">{overall}</span>',
            f'<span class="chip neutral-chip">Final {score}</span>',
            f'<span class="chip neutral-chip">RS 3M {rs3}</span>',
            f'<span class="chip neutral-chip">RS 6M {rs6}</span>',
        ])

    flags_html = ""
    if change_flags_list:
        flags_html = '<div class="row-wrap">' + "".join([f'<span class="chip neutral-chip">{f}</span>' for f in change_flags_list]) + '</div>'

    expl_html = "".join([f"<li>{x}</li>" for x in explanation])
    advanced_html = ""
    if not beginner_mode:
        advanced_html = f"""
        <div class="row-wrap">
            <span class="chip neutral-chip">Daily {daily}</span>
            <span class="chip neutral-chip">Weekly {weekly}</span>
            <span class="chip neutral-chip">Final {score}</span>
        </div>
        """

    st.markdown(
        f"""
<div class="stock-card">
  <div class="status-banner {status["css"]}">{status["title"]}</div>
  <div class="stock-title">{ticker} • {company}</div>
  <div class="stock-subtitle">{status["subtitle"]}</div>
  <div class="row-wrap">{"".join(chips)}</div>
  {flags_html}
  <div style="margin-top:0.55rem;" class="small-label">What the model is seeing</div>
  <ul class="list-tight">{expl_html}</ul>
  <div style="margin-top:0.5rem;" class="small-label">Current classification</div>
  <div>{interpretation}</div>
  {advanced_html}
</div>
""",
        unsafe_allow_html=True,
    )

def filter_table(df: pd.DataFrame, search_text: str, industries: List[str], stages: List[str], min_score: float, score_col: str, label_col: str, labels: List[str]) -> pd.DataFrame:
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

def hero_dashboard(combined: pd.DataFrame, industry: pd.DataFrame, regime: pd.DataFrame, last_updated: str) -> None:
    regime_text, top_industries, ready_text = market_summary_text(regime, industry, combined)
    st.markdown(
        f"""
<div class="hero-card">
  <div class="kicker">Market summary</div>
  <div class="big-number">{regime_text}</div>
  <div class="muted">Leading industries in the latest saved scan: {top_industries}</div>
  <div class="muted" style="margin-top:0.25rem;">{ready_text}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ready_count = int(((combined["stage"] == "Stage 2") & (combined["final_combined_score"].fillna(0) >= 60)).sum()) if not combined.empty else 0
        render_summary_card("Stronger setups", str(ready_count), "Stage 2 names with stronger alignment")
    with c2:
        watch_count = int((combined["final_combined_score"].fillna(0).between(48, 59.99)).sum()) if not combined.empty else 0
        render_summary_card("Developing setups", str(watch_count), "Names with constructive but mixed alignment")
    with c3:
        industry_count = len(industry) if not industry.empty else 0
        render_summary_card("Industries tracked", str(industry_count), "Industry rotation is included in the scan")
    with c4:
        render_summary_card("Last refresh", last_updated, "Latest saved scan read from your outputs folder")

def learn_while_using_panel() -> None:
    st.markdown("### Learn while using")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_learn_card("What does Ready mean?", "Ready is a simplified label for stocks that currently rank better on structure, momentum, and broader context within this model.")
    with c2:
        render_learn_card("What is Stage 2?", "Stage 2 is the stronger uptrend phase in this framework. It usually means price structure is stronger than Stage 1, 3, or 4.")
    with c3:
        render_learn_card("What is industry rotation?", "Industry rotation shows which sectors or industries are gaining or losing strength relative to others in the latest saved scan.")

def render_stock_grid(df: pd.DataFrame, beginner_mode: bool, limit: int = 12, show_change_flags: bool = False) -> None:
    st.markdown('<div class="small-label">The cards below translate raw scores into simpler labels. They are descriptive classifications, not instructions.</div>', unsafe_allow_html=True)
    for _, row in df.head(limit).iterrows():
        render_stock_card(row, beginner_mode=beginner_mode, show_change_flags=show_change_flags)

def dashboard_tab(combined: pd.DataFrame, daily: pd.DataFrame, weekly: pd.DataFrame, industry: pd.DataFrame, regime: pd.DataFrame, last_updated: str, beginner_mode: bool) -> None:
    hero_dashboard(combined, industry, regime, last_updated)
    st.divider()
    learn_while_using_panel()
    st.divider()

    top_ready = combined.copy()
    if "final_combined_score" in top_ready.columns:
        top_ready = top_ready.sort_values("final_combined_score", ascending=False)

    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown("### Stronger setups")
        st.caption("A simplified view of the highest-ranked names in the latest scan.")
        render_stock_grid(top_ready, beginner_mode=beginner_mode, limit=8)
    with c2:
        st.markdown("### What changed in the market")
        daily_events = int(daily["daily_setup_bucket"].isin(["breakout_today", "near_pivot"]).sum()) if not daily.empty and "daily_setup_bucket" in daily.columns else 0
        weekly_events = int(weekly["weekly_setup_bucket"].isin(["weekly_breakout", "weekly_near_pivot"]).sum()) if not weekly.empty and "weekly_setup_bucket" in weekly.columns else 0
        leading_industries = industry.head(5)["Industry"].astype(str).tolist() if not industry.empty and "Industry" in industry.columns else []

        st.markdown(
            f"""
<div class="guide-card">
  <div class="section-title">Simple readout</div>
  <ul class="list-tight">
    <li>{daily_events} names currently show stronger daily behaviour in the latest scan.</li>
    <li>{weekly_events} names currently show stronger weekly behaviour in the latest scan.</li>
    <li>Leading industries now: {", ".join(leading_industries) if leading_industries else "not available"}.</li>
  </ul>
</div>
""",
            unsafe_allow_html=True,
        )
        render_disclosure()

def ranked_tab(title: str, df: pd.DataFrame, score_col: str, label_col: str, beginner_mode: bool, show_search: bool = True) -> None:
    st.subheader(title)
    if df.empty:
        st.info("No scan outputs found yet.")
        return
    with st.expander("Filters", expanded=False):
        c1, c2 = st.columns(2)
        search = c1.text_input("Search by ticker, company, or industry", key=f"{title}_search") if show_search else ""
        min_score = c2.slider(f"Minimum {score_col}", 0.0, 100.0, 55.0 if beginner_mode else 0.0, 0.5, key=f"{title}_min")
        c3, c4, c5 = st.columns(3)
        industries = c3.multiselect("Industry", sorted(df["Industry"].dropna().unique().tolist()) if "Industry" in df.columns else [], key=f"{title}_industry")
        stages = c4.multiselect("Stage", sorted(df["stage"].dropna().unique().tolist()) if "stage" in df.columns else [], key=f"{title}_stage")
        labels = c5.multiselect("Setup label", sorted(df[label_col].dropna().unique().tolist()) if label_col in df.columns else [], key=f"{title}_label")
    filtered = filter_table(df, search, industries, stages, min_score, score_col, label_col, labels)

    if beginner_mode:
        st.caption(f"{len(filtered)} results. Cards below translate the scan output into simpler labels.")
        render_stock_grid(filtered, beginner_mode=True, limit=min(20, len(filtered)))
    else:
        cols = [c for c in ["ticker", "Company Name", "Industry", "stage", label_col, score_col, "rs_3m_pct", "rs_6m_pct"] if c in filtered.columns]
        st.caption(f"{len(filtered)} results")
        st.dataframe(pretty_columns(filtered[cols]), use_container_width=True, hide_index=True, height=520)

def render_stock_snapshot(row: pd.Series, beginner_mode: bool) -> None:
    status = get_beginner_status(row)
    company = row.get("Company Name", row.get("ticker", "Stock"))
    industry = row.get("Industry", "n/a")
    final_score = format_num(row.get("final_combined_score", row.get("combined_score")))
    daily_score = format_num(row.get("final_daily_score", row.get("daily_score")))
    weekly_score = format_num(row.get("final_weekly_score", row.get("weekly_score")))

    st.markdown(
        f"""
<div class="status-card">
  <div class="status-banner {status["css"]}">{status["title"]}</div>
  <div class="stock-title">{company}</div>
  <div class="stock-subtitle">{industry} • {stage_label(row)}</div>
  <div class="row-wrap">
    <span class="chip neutral-chip">{structure_label(row)}</span>
    <span class="chip neutral-chip">{momentum_label(row)}</span>
  </div>
  <div style="margin-top:0.55rem;" class="muted">{status["explain"]}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        render_summary_card("Overall", final_score, "Overall model score")
    with c2:
        render_summary_card("Daily", daily_score, "Daily model score")
    with c3:
        render_summary_card("Weekly", weekly_score, "Weekly model score")

    with st.expander("How to read this stock", expanded=True):
        st.markdown(
            f"""
- **Current bucket:** {status["title"]}  
- **Structure:** {structure_label(row)}  
- **Momentum:** {momentum_label(row)}  
- **Stage:** {stage_label(row)}  
- **Stage meaning:** {stage_explanation(str(row.get("stage", "")))}  
- **Current classification:** {compliance_safe_interpretation(row)}
"""
        )
        if not beginner_mode:
            st.json({
                "Daily label": row.get("daily_setup_label", row.get("daily_setup_bucket")),
                "Weekly label": row.get("weekly_setup_label", row.get("weekly_setup_bucket")),
                "Overall label": row.get("overall_setup_label", row.get("combined_bucket")),
                "RS 3M": row.get("rs_3m_pct"),
                "RS 6M": row.get("rs_6m_pct"),
                "Notes": row.get("notes"),
            })

def stock_detail_tab(combined: pd.DataFrame, daily_charts_dir: str, weekly_charts_dir: str, beginner_mode: bool) -> None:
    st.subheader("Stock detail")
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
        manual_ticker = f3.selectbox("Stock", ticker_list, index=current_idx, key=f"stock_detail_ticker_selectbox_{st.session_state['stock_nav_version']}")
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
    render_stock_snapshot(row, beginner_mode=beginner_mode)

    dpath = resolve_chart_path(daily_charts_dir, ticker, "_daily.png")
    wpath = resolve_chart_path(weekly_charts_dir, ticker, "_weekly.png")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Daily chart")
        if dpath:
            st.image(safe_image_bytes(dpath), use_container_width=True)
        else:
            st.info("Daily chart not available.")
    with c2:
        st.markdown("### Weekly chart")
        if wpath:
            st.image(safe_image_bytes(wpath), use_container_width=True)
        else:
            st.info("Weekly chart not available.")

    st.caption("Charts are descriptive visualizations of the latest saved scan and do not provide personalized recommendations.")

def changes_tab(stock_changes: pd.DataFrame, top_movers: pd.DataFrame, beginner_mode: bool) -> None:
    st.subheader("What changed")
    if stock_changes.empty:
        st.info("No change data found yet.")
        return
    compact_metric_grid([
        ("New daily breakout conditions", int(stock_changes["new_daily_breakout"].fillna(False).sum()) if "new_daily_breakout" in stock_changes.columns else 0),
        ("New weekly breakout conditions", int(stock_changes["new_weekly_breakout"].fillna(False).sum()) if "new_weekly_breakout" in stock_changes.columns else 0),
        ("Entered Stage 2", int(stock_changes["entered_stage_2"].fillna(False).sum()) if "entered_stage_2" in stock_changes.columns else 0),
        ("New Top 10", int(stock_changes["new_top_10"].fillna(False).sum()) if "new_top_10" in stock_changes.columns else 0),
    ])

    if beginner_mode:
        st.caption("These cards highlight names whose model classification improved in the latest saved run.")
        improved = stock_changes.copy()
        if "combined_score_change" in improved.columns:
            improved = improved.sort_values(["new_top_10", "new_top_20", "combined_score_change", "rank_change"], ascending=[False, False, False, False])
        if all(col in improved.columns for col in ["new_daily_breakout", "new_weekly_breakout", "entered_stage_2", "new_top_10", "new_top_20"]):
            improved = improved[improved[["new_daily_breakout", "new_weekly_breakout", "entered_stage_2", "new_top_10", "new_top_20"]].fillna(False).any(axis=1)]
        render_stock_grid(improved, beginner_mode=True, limit=min(15, len(improved)), show_change_flags=True)
    else:
        cols = [c for c in ["ticker", "Company Name", "Industry", "stage", "current_rank", "prev_rank", "rank_change", "final_combined_score", "combined_score_change", "new_top_10", "new_top_20"] if c in top_movers.columns]
        movers = top_movers.copy()
        if "rank_change" in movers.columns:
            movers = movers[(movers["rank_change"].fillna(0) > 0) | (movers["combined_score_change"].fillna(0) > 0)]
        movers = movers.sort_values(["new_top_10", "new_top_20", "rank_change", "combined_score_change"], ascending=[False, False, False, False]).head(30)
        st.dataframe(pretty_columns(movers[cols]), use_container_width=True, hide_index=True, height=420)

def industry_rotation_tab(industry_changes: pd.DataFrame, beginner_mode: bool) -> None:
    st.subheader("Industry rotation")
    if industry_changes.empty:
        st.info("No industry rotation data found yet.")
        return
    compact_metric_grid([
        ("New clusters", int(industry_changes["new_cluster"].fillna(False).sum()) if "new_cluster" in industry_changes.columns else 0),
        ("Industries rising", int((industry_changes["rank_change"].fillna(0) > 0).sum()) if "rank_change" in industry_changes.columns else 0),
        ("Industries falling", int((industry_changes["rank_change"].fillna(0) < 0).sum()) if "rank_change" in industry_changes.columns else 0),
        ("Daily breadth change", int(industry_changes["actionable_daily_change"].fillna(0).sum()) if "actionable_daily_change" in industry_changes.columns else 0),
    ])
    cols = [c for c in ["Industry", "current_rank", "prev_rank", "rank_change", "avg_combined_score", "combined_score_change", "strong_combined", "strong_combined_change", "actionable_daily", "actionable_daily_change", "actionable_weekly", "actionable_weekly_change", "new_cluster"] if c in industry_changes.columns]

    rising = industry_changes.sort_values(["rank_change", "combined_score_change"], ascending=[False, False]).head(10)
    falling = industry_changes.sort_values(["rank_change", "combined_score_change"], ascending=[True, True]).head(10)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Industries improving")
        st.dataframe(pretty_columns(rising[cols]), use_container_width=True, hide_index=True, height=320)
    with c2:
        st.markdown("### Industries weakening")
        st.dataframe(pretty_columns(falling[cols]), use_container_width=True, hide_index=True, height=320)

def industry_tab(industry: pd.DataFrame) -> None:
    st.subheader("Industry strength")
    if industry.empty:
        st.info("No scan outputs found yet.")
        return
    cols = [c for c in ["Industry", "avg_combined_score", "rs_rank", "strong_combined", "actionable_daily", "actionable_weekly"] if c in industry.columns]
    st.dataframe(pretty_columns(industry[cols]), use_container_width=True, hide_index=True, height=480)

def stage_by_industry_tab(combined: pd.DataFrame) -> None:
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
    st.dataframe(display, use_container_width=True, hide_index=True, height=480)

def normalize_portfolio_ticker(x: str) -> str:
    x = str(x).strip().upper()
    if not x or x == "NAN":
        return ""
    return x if x.endswith(".NS") else f"{x}.NS"

def portfolio_tab(combined: pd.DataFrame, beginner_mode: bool) -> None:
    st.subheader("My portfolio")
    st.caption("This section shows analytics on tickers entered by the user. It does not assess suitability, allocation, or appropriateness.")
    if combined.empty:
        st.info("No scan outputs found yet.")
        return
    if "portfolio_tickers" not in st.session_state:
        st.session_state["portfolio_tickers"] = []

    input_text = st.text_input("Enter tickers (comma separated)", placeholder="Example: RELIANCE, TCS, INFY", key="portfolio_input_text")
    if st.button("Add", use_container_width=True, key="portfolio_add_btn") and input_text:
        raw = [x.strip() for x in input_text.split(",")]
        normalized = [normalize_portfolio_ticker(x) for x in raw]
        for t in normalized:
            if t and t not in st.session_state["portfolio_tickers"] and len(st.session_state["portfolio_tickers"]) < 20:
                st.session_state["portfolio_tickers"].append(t)
        st.rerun()

    st.caption(f"{len(st.session_state['portfolio_tickers'])}/20 tickers")
    if not st.session_state["portfolio_tickers"]:
        st.info("Add tickers to see analytics for that list.")
        return

    portfolio = pd.DataFrame({"ticker": st.session_state["portfolio_tickers"]})
    merged = portfolio.merge(combined, on="ticker", how="left")
    stage_counts = merged["stage"].value_counts() if "stage" in merged.columns else pd.Series(dtype=int)
    avg_score = round(float(merged["final_combined_score"].dropna().mean()), 1) if "final_combined_score" in merged.columns and merged["final_combined_score"].notna().any() else "n/a"

    compact_metric_grid([
        ("Stage 1", int(stage_counts.get("Stage 1", 0))),
        ("Stage 2", int(stage_counts.get("Stage 2", 0))),
        ("Stage 3", int(stage_counts.get("Stage 3", 0))),
        ("Stage 4", int(stage_counts.get("Stage 4", 0))),
        ("Avg Score", avg_score),
    ])

    if beginner_mode:
        render_stock_grid(merged.dropna(subset=["ticker"]), beginner_mode=True, limit=min(20, len(merged)))
    else:
        display = merged.copy()
        display["Ticker"] = display["ticker"].astype(str).str.replace(".NS", "", regex=False)
        display = display.rename(columns={"stage": "Stage", "final_combined_score": "Final Score", "overall_setup_label": "Setup"})
        cols = [c for c in ["Ticker", "Industry", "Stage", "Final Score", "Setup"] if c in display.columns]
        st.dataframe(display[cols].reset_index(drop=True), use_container_width=True, hide_index=True, height=320)

    remove_choice = st.selectbox("Remove ticker", [""] + [t.replace(".NS", "") for t in st.session_state["portfolio_tickers"]], key="portfolio_remove_select")
    if st.button("Remove selected ticker", key="portfolio_remove_btn", use_container_width=True) and remove_choice:
        full_ticker = normalize_portfolio_ticker(remove_choice)
        st.session_state["portfolio_tickers"] = [t for t in st.session_state["portfolio_tickers"] if t != full_ticker]
        st.rerun()

def render_mover_card(row, period_col: str, positive: bool = True, beginner_mode: bool = True):
    ticker = str(row.get("ticker", "")).replace(".NS", "")
    company = row.get("Company Name", "")
    industry = row.get("Industry", "")
    stage = row.get("stage", "")
    score = row.get("final_combined_score")
    change = pd.to_numeric(row.get(period_col), errors="coerce")
    status = get_beginner_status(row)
    change_cls = "mover-change-up" if pd.notna(change) and change >= 0 else "mover-change-down"
    shell_cls = "mover-card mover-top" if positive else "mover-card mover-bottom"
    change_text = f"{change:+.2f}%" if pd.notna(change) else "n/a"
    score_text = f"{float(score):.1f}" if pd.notna(pd.to_numeric(score, errors="coerce")) else "n/a"
    html = f"""
    <div class="{shell_cls}">
      <div class="mover-head">
        <div>
          <div class="mover-ticker">{ticker}</div>
          <div class="mover-company">{company}</div>
        </div>
        <div class="{change_cls}">{change_text}</div>
      </div>
      <div class="mover-chip-wrap">
        <span class="mover-chip">{industry}</span>
        <span class="mover-chip">{stage}</span>
        <span class="mover-chip">{status["title"] if beginner_mode else row.get("overall_setup_label", row.get("combined_bucket", ""))}</span>
        {"<span class='mover-chip'>Score " + score_text + "</span>" if not beginner_mode else ""}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def moves_tab(price_moves: pd.DataFrame, beginner_mode: bool) -> None:
    st.subheader("Market movers")
    st.caption("This section simply shows which names moved most over the selected time window. Price movement and quality classification are different things.")
    if price_moves.empty:
        st.info("No price move data found yet.")
        return

    period_map = {
        "1 Day": "change_1d_pct",
        "1 Week": "change_1w_pct",
        "1 Month": "change_1m_pct",
        "YTD": "change_ytd_pct",
    }
    selected_period = st.radio("Move window", list(period_map.keys()), horizontal=True, index=0)
    col_name = period_map[selected_period]

    df = normalize_columns(price_moves.copy())
    if "overall_setup_label" not in df.columns and "combined_bucket" in df.columns:
        df["overall_setup_label"] = df["combined_bucket"]
    df[col_name] = pd.to_numeric(df[col_name], errors="coerce")
    df["final_combined_score"] = pd.to_numeric(df.get("final_combined_score"), errors="coerce")
    df = df.dropna(subset=[col_name]).reset_index(drop=True)

    compact_metric_grid([
        ("Up moves", int((df[col_name] > 0).sum())),
        ("Down moves", int((df[col_name] < 0).sum())),
        ("Best move", f"{df[col_name].max():+.2f}%" if not df.empty else "n/a"),
        ("Worst move", f"{df[col_name].min():+.2f}%" if not df.empty else "n/a"),
    ])

    render_learn_card("How to read this section", "A large move only means price moved more than other names over the selected window. It does not mean the stock is automatically a stronger setup.")
    leaders = df.sort_values([col_name, "final_combined_score"], ascending=[False, False]).head(10)
    laggards = df.sort_values([col_name, "final_combined_score"], ascending=[True, False]).head(10)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### Fastest upward moves • {selected_period}")
        for _, row in leaders.iterrows():
            render_mover_card(row, col_name, positive=True, beginner_mode=beginner_mode)
    with c2:
        st.markdown(f"### Fastest downward moves • {selected_period}")
        for _, row in laggards.iterrows():
            render_mover_card(row, col_name, positive=False, beginner_mode=beginner_mode)

    with st.expander("View as table", expanded=False):
        cols = [c for c in ["ticker", "Company Name", "Industry", "stage", "final_combined_score", "change_1d_pct", "change_1w_pct", "change_1m_pct", "change_ytd_pct"] if c in df.columns]
        st.dataframe(pretty_columns(df[cols].sort_values(col_name, ascending=False)), use_container_width=True, hide_index=True, height=420)

def help_tab(beginner_mode: bool, help_image_path: str) -> None:
    st.subheader("Beginner help")
    st.markdown(
        """
This site is designed to help a beginner understand three things from a large stock universe:

1. which names currently look technically stronger or weaker inside this rule-based scan  
2. which industries are improving or weakening relative to others  
3. how market structure changes over time across daily and weekly views  

The site does **not** decide what is suitable for any individual person.
"""
    )

    st.markdown("### What the main labels mean")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_learn_card("Ready", "The model currently sees comparatively stronger structure, momentum, and context.")
    with c2:
        render_learn_card("Watch", "The model currently sees developing structure, but alignment is still mixed or incomplete.")
    with c3:
        render_learn_card("Lower strength", "The model currently sees weaker or less aligned structure.")

    st.markdown("### What are stages?")
    st.markdown(
        """
Stages are a simple way to describe where a stock appears to sit in a broad market cycle:

- **Stage 1**: accumulation or recovery phase  
- **Stage 2**: uptrend or markup phase  
- **Stage 3**: distribution phase  
- **Stage 4**: downtrend or markdown phase  

Within this framework, Stage 2 is usually the strongest phase and Stage 4 is the weakest.
"""
    )
    help_img = Path(help_image_path)
    if help_img.exists():
        st.image(str(help_img), caption="Reference image for the four broad market phases", use_container_width=True)
    else:
        st.info("Stage reference image not found.")

    st.markdown("### What each page is trying to show")
    render_learn_card("Dashboard", "A quick summary of market tone, stronger names, and simple learning cards.")
    render_learn_card("Overall", "The full ranked universe using the model's overall score and overall classification.")
    render_learn_card("Market movers", "The largest price moves over 1 day, 1 week, 1 month, or YTD.")
    render_learn_card("Portfolio", "Analytics for tickers entered by the user. This is descriptive only.")
    render_learn_card("Stock", "A deep look at one stock using labels, charts, and explanatory text.")
    render_learn_card("Changes", "Names whose model classification improved in the latest saved run.")
    render_learn_card("Rotation", "Industries moving up or down relative to others.")
    render_learn_card("Industries", "Industry-level strength snapshot.")
    render_learn_card("Stages", "Stage distribution by industry.")

    st.markdown("### How to read the site in a simple way")
    st.markdown(
        """
- Start with **Dashboard** to understand the broad market tone.  
- Use **Overall** to see which names currently rank better in the model.  
- Use **Market movers** to separate pure price movement from quality classification.  
- Use **Stock** to understand why a specific name got its current label.  
- Use **Rotation** to see which industries are gaining or losing strength.  
"""
    )

    st.markdown("### Compliance-safe interpretation")
    st.markdown(
        """
The classifications and summaries on this site are descriptive outputs from a rule-based model. They do not evaluate personal goals, financial situation, suitability, or risk tolerance. They are not buy calls, sell calls, or allocation advice.
"""
    )

    if beginner_mode:
        st.info("Beginner Mode is ON. Simpler labels appear more often across the site.")
    else:
        st.info("Beginner Mode is OFF. Raw scores and detailed labels appear more often across the site.")

st.title("VCP Market Analytics Dashboard")
render_disclosure()

with st.sidebar:
    st.header("Dashboard settings")
    outdir = st.text_input("Output folder", value="outputs")
    beginner_mode = st.toggle("Beginner Mode", value=True, help="Shows simpler labels more often.")
    help_image_path = st.text_input("Help page stage image", value="market_phases_reference.png")
    st.caption("This dashboard reads the latest saved scan outputs from the outputs folder.")

outputs = {
    "daily": str(Path(outdir) / "vcp_daily_ranked.csv"),
    "weekly": str(Path(outdir) / "vcp_weekly_ranked.csv"),
    "combined": str(Path(outdir) / "vcp_combined_ranked.csv"),
    "industry": str(Path(outdir) / "industry_strength.csv"),
    "regime": str(Path(outdir) / "market_regime.csv"),
    "stock_changes": str(Path(outdir) / "stock_changes.csv"),
    "industry_changes": str(Path(outdir) / "industry_changes.csv"),
    "top_movers": str(Path(outdir) / "top_movers.csv"),
    "price_moves": str(Path(outdir) / "stock_price_moves.csv"),
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
price_moves_df = add_safe_labels(safe_read(outputs["price_moves"]))
last_updated = get_last_updated(outputs["combined"])

if combined_df.empty and daily_df.empty and weekly_df.empty:
    st.warning("No output files found yet. Wait for the saved scan to generate the latest files.")

tabs = st.tabs([
    "Dashboard", "Overall", "Market movers", "Portfolio", "Stock",
    "Daily", "Weekly", "Changes", "Rotation", "Industries", "Stages", "Help"
])

with tabs[0]:
    dashboard_tab(combined_df, daily_df, weekly_df, industry_df, regime_df, last_updated, beginner_mode)
with tabs[1]:
    ranked_tab("Overall candidates", combined_df, "final_combined_score", "overall_setup_label", beginner_mode, show_search=True)
with tabs[2]:
    moves_tab(price_moves_df, beginner_mode)
with tabs[3]:
    portfolio_tab(combined_df, beginner_mode)
with tabs[4]:
    stock_detail_tab(combined_df, outputs["daily_charts_dir"], outputs["weekly_charts_dir"], beginner_mode)
with tabs[5]:
    ranked_tab("Daily candidates", daily_df, "final_daily_score", "daily_setup_label", beginner_mode, show_search=False)
with tabs[6]:
    ranked_tab("Weekly candidates", weekly_df, "final_weekly_score", "weekly_setup_label", beginner_mode, show_search=False)
with tabs[7]:
    changes_tab(stock_changes_df, top_movers_df, beginner_mode)
with tabs[8]:
    industry_rotation_tab(industry_changes_df, beginner_mode)
with tabs[9]:
    industry_tab(industry_df)
with tabs[10]:
    stage_by_industry_tab(combined_df)
with tabs[11]:
    help_tab(beginner_mode, help_image_path)
